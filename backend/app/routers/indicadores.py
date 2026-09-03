import math
import random
from datetime import date, timedelta

from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from app.database import get_db
from app.cache import cache_get, cache_set

router = APIRouter()


def _rango_etario(g: str):
    """Convierte una etiqueta de grupo etario ('65-74', '85+') en (lo, hi).

    Normaliza los guiones tipográficos (– —) al guion simple. Devuelve hi=None
    para los grupos abiertos ('85+'); None si la etiqueta no es válida.
    """
    g = g.replace("–", "-").replace("—", "-").strip()
    if g.endswith("+"):
        try:
            return int(g[:-1]), None
        except ValueError:
            return None
    if "-" in g:
        a, b = g.split("-", 1)
        try:
            return int(a), int(b)
        except ValueError:
            return None
    return None


def aplicar_filtros(where, params, *, region=None, comuna=None,
                    nivel_riesgo=None, sexo=None, grupo_etario=None,
                    pacam=None):
    """Agrega condiciones WHERE comunes a las consultas del dashboard.

    Asume los alias estándar: hogares=h, personas=p, indicadores=i. El filtro
    por nivel de riesgo exige que la consulta una la tabla de indicadores.
    """
    if region:
        where += " AND h.region = :region"
        params["region"] = region
    if comuna:
        where += " AND h.comuna = :comuna"
        params["comuna"] = comuna
    if nivel_riesgo:
        where += " AND i.nivel_riesgo = :nivel_riesgo"
        params["nivel_riesgo"] = nivel_riesgo
    if pacam == "beneficiarios":
        where += " AND h.acceso_pacam = TRUE"
    elif pacam == "no_retiradores":
        where += " AND h.acceso_pacam = TRUE AND p.motivo_no_retiro IS NOT NULL"
    elif pacam in ("sin_cobertura", "no_beneficiarios"):
        where += " AND h.acceso_pacam = FALSE"
    if sexo:
        sexos = [s.strip().upper() for s in sexo.split(",") if s.strip()]
        if sexos:
            marks = ", ".join(f":sexo{k}" for k in range(len(sexos)))
            where += f" AND p.sexo IN ({marks})"
            for k, s in enumerate(sexos):
                params[f"sexo{k}"] = s
    if grupo_etario:
        grupos = [g.strip() for g in grupo_etario.split(",") if g.strip()]
        conds = []
        for k, g in enumerate(grupos):
            rng = _rango_etario(g)
            if not rng:
                continue
            lo, hi = rng
            if hi is None:
                conds.append(f"p.edad >= :edad_lo{k}")
                params[f"edad_lo{k}"] = lo
            else:
                conds.append(f"(p.edad BETWEEN :edad_lo{k} AND :edad_hi{k})")
                params[f"edad_lo{k}"] = lo
                params[f"edad_hi{k}"] = hi
        if conds:
            where += " AND (" + " OR ".join(conds) + ")"
    return where, params


def _clave_filtros(region, comuna, nivel_riesgo, sexo, grupo_etario, pacam=None):
    """Sufijo determinista para las claves de caché según los filtros activos."""
    return "|".join(str(x or "") for x in
                    (region, comuna, nivel_riesgo, sexo, grupo_etario, pacam))


@router.get("/")
def get_indicadores(
    region: Optional[str] = Query(None, description="Codigo de region (ej. '07')"),
    zona: Optional[str] = Query(None, description="'urbano' o 'rural'"),
    db: Session = Depends(get_db),
):
    """Indicadores nutricionales agregados desde la vista resumen regional."""
    query = "SELECT * FROM vista_resumen_regional WHERE 1=1"
    params = {}

    if region:
        query += " AND region = :region"
        params["region"] = region
    if zona:
        query += " AND zona = :zona"
        params["zona"] = zona

    rows = db.execute(text(query), params).mappings().all()
    return {"filtros": {"region": region, "zona": zona}, "datos": [dict(r) for r in rows]}


@router.get("/resumen")
def get_resumen_nacional(
    region: Optional[str] = Query(None),
    comuna: Optional[str] = Query(None),
    nivel_riesgo: Optional[str] = Query(None),
    sexo: Optional[str] = Query(None, description="Lista separada por comas (F,M)"),
    grupo_etario: Optional[str] = Query(None, description="Ej. '65-74,85+'"),
    pacam: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Totales de indicadores nutricionales, filtrables y cacheados por TTL."""
    cache_key = "indicadores:resumen:" + _clave_filtros(
        region, comuna, nivel_riesgo, sexo, grupo_etario, pacam
    )
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    where, params = aplicar_filtros(
        "WHERE 1=1", {}, region=region, comuna=comuna,
        nivel_riesgo=nivel_riesgo, sexo=sexo, grupo_etario=grupo_etario,
        pacam=pacam,
    )
    sql = f"""
        SELECT
            COUNT(DISTINCT p.id) AS total_adultos_mayores,
            ROUND(100.0 * SUM(CASE WHEN i.nivel_riesgo = 'alto'
                THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_riesgo_alto,
            ROUND(100.0 * SUM(CASE WHEN i.nivel_riesgo = 'medio'
                THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_riesgo_medio,
            ROUND(100.0 * SUM(CASE WHEN h.acceso_pacam = TRUE
                THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_beneficiarios_pacam,
            ROUND(100.0 * SUM(CASE WHEN p.nivel_inseguridad
                IN ('moderado','severo')
                THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_inseguridad_alimentaria
        FROM hogares h
        JOIN personas p                  ON p.hogar_id = h.id
        JOIN indicadores_nutricionales i ON i.persona_id = p.id
        {where}
    """
    result = db.execute(text(sql), params).mappings().one_or_none()
    payload = dict(result) if result else {
        "message": "Sin datos aun - carga el dataset primero"
    }
    cache_set(cache_key, payload)
    return payload


@router.get("/stats")
def get_stats(
    region: Optional[str] = Query(None, description="Filtrar por region"),
    comuna: Optional[str] = Query(None),
    nivel_riesgo: Optional[str] = Query(None),
    sexo: Optional[str] = Query(None, description="Lista separada por comas (F,M)"),
    grupo_etario: Optional[str] = Query(None, description="Ej. '65-74,85+'"),
    pacam: Optional[str] = Query(
        None, description="'beneficiarios', 'no_retiradores' o 'sin_cobertura'"
    ),
    db: Session = Depends(get_db),
):
    """
    Distribuciones estadisticas para el StatsPanel del dashboard.
    Retorna: distribucion_riesgo, distribucion_inseguridad,
             comorbilidades, distribucion_quintil.
    """
    cache_key = "indicadores:stats:" + _clave_filtros(
        region, comuna, nivel_riesgo, sexo, grupo_etario, pacam
    )
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    # Todas las subconsultas unen indicadores (i) para poder filtrar por nivel
    # de riesgo de forma homogénea.
    where, params = aplicar_filtros(
        "WHERE 1=1", {}, region=region, comuna=comuna,
        nivel_riesgo=nivel_riesgo, sexo=sexo, grupo_etario=grupo_etario,
        pacam=pacam,
    )

    # Distribucion nivel de riesgo
    sql_riesgo = f"""
        SELECT i.nivel_riesgo AS nivel, COUNT(*) AS n
        FROM hogares h
        JOIN personas p                  ON p.hogar_id = h.id
        JOIN indicadores_nutricionales i ON i.persona_id = p.id
        {where}
        GROUP BY i.nivel_riesgo
        ORDER BY CASE i.nivel_riesgo
            WHEN 'alto' THEN 0 WHEN 'medio' THEN 1 WHEN 'bajo' THEN 2 END
    """
    riesgo_rows = db.execute(text(sql_riesgo), params).mappings().all()

    # Distribucion inseguridad alimentaria
    sql_inseg = f"""
        SELECT p.nivel_inseguridad AS nivel, COUNT(*) AS n
        FROM hogares h
        JOIN personas p                  ON p.hogar_id = h.id
        JOIN indicadores_nutricionales i ON i.persona_id = p.id
        {where}
        GROUP BY p.nivel_inseguridad
        ORDER BY CASE p.nivel_inseguridad
            WHEN 'severo' THEN 0 WHEN 'moderado' THEN 1
            WHEN 'leve' THEN 2 WHEN 'seguro' THEN 3 END
    """
    inseg_rows = db.execute(text(sql_inseg), params).mappings().all()

    # Comorbilidades — columnas reales: tiene_hipertension, tiene_diabetes, tiene_depresion
    sql_comorb = f"""
        SELECT
            SUM(CASE WHEN p.tiene_hipertension THEN 1 ELSE 0 END) AS hipertension,
            SUM(CASE WHEN p.tiene_diabetes     THEN 1 ELSE 0 END) AS diabetes,
            SUM(CASE WHEN p.tiene_depresion    THEN 1 ELSE 0 END) AS depresion,
            COUNT(*) AS total
        FROM hogares h
        JOIN personas p                  ON p.hogar_id = h.id
        JOIN indicadores_nutricionales i ON i.persona_id = p.id
        {where}
    """
    comorb = db.execute(text(sql_comorb), params).mappings().one_or_none()

    # Distribucion por quintil de ingreso x nivel riesgo
    sql_quintil = f"""
        SELECT
            h.quintil_ingreso AS quintil,
            i.nivel_riesgo AS riesgo,
            COUNT(*) AS n
        FROM hogares h
        JOIN personas p                  ON p.hogar_id = h.id
        JOIN indicadores_nutricionales i ON i.persona_id = p.id
        {where}
        AND h.quintil_ingreso IS NOT NULL
        GROUP BY h.quintil_ingreso, i.nivel_riesgo
        ORDER BY h.quintil_ingreso, i.nivel_riesgo
    """
    quintil_rows = db.execute(text(sql_quintil), params).mappings().all()

    # Calcular porcentajes para riesgo
    total_riesgo = sum(r["n"] for r in riesgo_rows) or 1
    distribucion_riesgo = [
        {
            "nivel": r["nivel"],
            "n": r["n"],
            "pct": round(100.0 * r["n"] / total_riesgo, 1),
        }
        for r in riesgo_rows
    ]

    # Calcular porcentajes para inseguridad
    total_inseg = sum(r["n"] for r in inseg_rows) or 1
    distribucion_inseguridad = [
        {
            "nivel": r["nivel"],
            "n": r["n"],
            "pct": round(100.0 * r["n"] / total_inseg, 1),
        }
        for r in inseg_rows
        if r["nivel"] is not None
    ]

    # Comorbilidades como lista de porcentajes
    comorbilidades = []
    if comorb and comorb["total"]:
        total_c = comorb["total"]
        for key, label in [
            ("hipertension", "Hipertension arterial"),
            ("diabetes",     "Diabetes mellitus"),
            ("depresion",    "Depresion"),
        ]:
            comorbilidades.append({
                "nombre": label,
                "n": int(comorb[key] or 0),
                "pct": round(100.0 * (comorb[key] or 0) / total_c, 1),
            })

    # Quintil agrupado
    quintil_dict: dict = {}
    for r in quintil_rows:
        q = f"Q{r['quintil']}"
        if q not in quintil_dict:
            quintil_dict[q] = {"tramo": q, "total": 0, "por_riesgo": {}}
        quintil_dict[q]["total"] += r["n"]
        quintil_dict[q]["por_riesgo"][r["riesgo"]] = r["n"]

    payload = {
        "distribucion_riesgo": distribucion_riesgo,
        "distribucion_inseguridad": distribucion_inseguridad,
        "comorbilidades": comorbilidades,
        "distribucion_rsh": list(quintil_dict.values()),
        "hay_datos": len(riesgo_rows) > 0,
    }
    cache_set(cache_key, payload)
    return payload


@router.get("/tendencias")
def get_tendencias(
    meses: int = Query(6, ge=3, le=24, description="Numero de meses hacia atras"),
    region: Optional[str] = Query(None),
    comuna: Optional[str] = Query(None),
    nivel_riesgo: Optional[str] = Query(None),
    sexo: Optional[str] = Query(None, description="Lista separada por comas (F,M)"),
    grupo_etario: Optional[str] = Query(None, description="Ej. '65-74,85+'"),
    db: Session = Depends(get_db),
):
    """
    Evolucion mensual de indicadores nutricionales.
    Usa fecha_calculo de indicadores_nutricionales para agrupar por mes.
    Si no hay datos temporales suficientes, retorna serie sintetica calibrada.
    """
    where, params = aplicar_filtros(
        "WHERE 1=1", {}, region=region, comuna=comuna,
        nivel_riesgo=nivel_riesgo, sexo=sexo, grupo_etario=grupo_etario,
    )

    # Formato de mes según el dialecto: PostgreSQL usa TO_CHAR; SQLite (tests)
    # no tiene TO_CHAR y requiere strftime.
    if db.bind.dialect.name == "sqlite":
        mes_expr = "strftime('%Y-%m', i.fecha_calculo)"
    else:
        mes_expr = "TO_CHAR(i.fecha_calculo, 'YYYY-MM')"

    sql = f"""
        SELECT
            {mes_expr} AS mes,
            COUNT(*) AS total,
            SUM(CASE WHEN i.nivel_riesgo = 'alto'  THEN 1 ELSE 0 END) AS riesgo_alto,
            SUM(CASE WHEN i.nivel_riesgo = 'medio' THEN 1 ELSE 0 END) AS riesgo_medio,
            SUM(CASE WHEN i.nivel_riesgo = 'bajo'  THEN 1 ELSE 0 END) AS riesgo_bajo,
            SUM(CASE WHEN p.nivel_inseguridad IN ('moderado','severo')
                THEN 1 ELSE 0 END) AS inseg_moderada_severa
        FROM indicadores_nutricionales i
        JOIN personas p ON p.id = i.persona_id
        JOIN hogares h  ON h.id = p.hogar_id
        {where}
        AND i.fecha_calculo IS NOT NULL
        GROUP BY {mes_expr}
        ORDER BY mes DESC
        LIMIT :meses
    """
    params["meses"] = meses
    rows = db.execute(text(sql), params).mappings().all()

    if len(rows) >= 3:
        serie = [
            {
                "mes": r["mes"],
                "total": r["total"],
                "pct_riesgo_alto": (
                    round(100.0 * r["riesgo_alto"] / r["total"], 1)
                    if r["total"] else 0
                ),
                "pct_riesgo_medio": (
                    round(100.0 * r["riesgo_medio"] / r["total"], 1)
                    if r["total"] else 0
                ),
                "pct_inseg_moderada_severa": (
                    round(100.0 * r["inseg_moderada_severa"] / r["total"], 1)
                    if r["total"] else 0
                ),
            }
            for r in reversed(list(rows))
        ]
        return {"serie": serie, "es_sintetica": False}

    # Fallback: serie sintetica calibrada con dataset Maule.
    # Modelo estacional coherente (no aleatorio puro):
    #   - Mayor riesgo/inseguridad en invierno austral (jun-ago): el frio y los
    #     costos de calefaccion deterioran la seguridad alimentaria del adulto
    #     mayor. Factor estacional = coseno centrado en julio (mes 7).
    #   - Leve tendencia creciente a lo largo del periodo observado.
    #   - Varianza acotada y determinista (semilla por mes) para reproducibilidad.
    #   - Las líneas base se anclan a la cohorte filtrada actual, de modo que la
    #     serie responde a los filtros del dashboard.
    cohorte = db.execute(text(f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN i.nivel_riesgo = 'alto'  THEN 1 ELSE 0 END) AS alto,
            SUM(CASE WHEN i.nivel_riesgo = 'medio' THEN 1 ELSE 0 END) AS medio,
            SUM(CASE WHEN p.nivel_inseguridad IN ('moderado','severo')
                THEN 1 ELSE 0 END) AS inseg
        FROM indicadores_nutricionales i
        JOIN personas p ON p.id = i.persona_id
        JOIN hogares h  ON h.id = p.hogar_id
        {where}
    """), params).mappings().one_or_none()

    tot = (cohorte["total"] if cohorte else 0) or 0
    base_alto = round(100.0 * (cohorte["alto"] or 0) / tot, 1) if tot else 27.0
    base_medio = round(100.0 * (cohorte["medio"] or 0) / tot, 1) if tot else 7.0
    base_inseg = round(100.0 * (cohorte["inseg"] or 0) / tot, 1) if tot else 11.0

    def _estacional(mes_anio: int) -> float:
        # +1 en julio (invierno), -1 en enero (verano).
        return math.cos(2 * math.pi * (mes_anio - 7) / 12)

    meses_list = []
    base_date = date.today().replace(day=1)
    for idx, i in enumerate(range(meses, 0, -1)):
        m = (base_date.replace(day=1) - timedelta(days=30 * (i - 1)))
        label = m.strftime("%Y-%m")
        est = _estacional(m.month)
        # Tendencia creciente suave centrada para que el mes más reciente quede
        # cerca del valor real de la cohorte (trend va de -0.75 a +0.75 pp).
        trend = 1.5 * (idx / max(meses - 1, 1)) - 0.75
        # Ruido acotado determinista (±0.6 pp), reproducible por mes.
        rng = random.Random(int(m.strftime("%Y%m")))
        ruido = rng.uniform(-0.6, 0.6)

        pct_alto = round(base_alto + 3.0 * est + trend + ruido, 1)
        pct_medio = round(base_medio + 1.2 * est + 0.4 * trend + ruido * 0.4, 1)
        pct_inseg = round(base_inseg + 2.5 * est + trend + ruido * 0.5, 1)

        meses_list.append({
            "mes": label,
            "total": 1200,
            "pct_riesgo_alto": max(0.0, min(100.0, pct_alto)),
            "pct_riesgo_medio": max(0.0, min(100.0, pct_medio)),
            "pct_inseg_moderada_severa": max(0.0, min(100.0, pct_inseg)),
        })
    return {"serie": meses_list, "es_sintetica": True}
