from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from app.database import get_db
from app.cache import cache_get, cache_set

router = APIRouter()


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
def get_resumen_nacional(db: Session = Depends(get_db)):
    """Totales nacionales de indicadores nutricionales (cacheado por TTL)."""
    cache_key = "indicadores:resumen_nacional"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    sql = """
        SELECT
            COUNT(DISTINCT p.id) AS total_adultos_mayores,
            ROUND(100.0 * SUM(CASE WHEN i.nivel_riesgo = 'alto'
                THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_riesgo_alto,
            ROUND(100.0 * SUM(CASE WHEN h.acceso_pacam = TRUE
                THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_beneficiarios_pacam,
            ROUND(100.0 * SUM(CASE WHEN p.nivel_inseguridad
                IN ('moderado','severo')
                THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_inseguridad_alimentaria
        FROM hogares h
        JOIN personas p                  ON p.hogar_id = h.id
        JOIN indicadores_nutricionales i ON i.persona_id = p.id
    """
    result = db.execute(text(sql)).mappings().one_or_none()
    payload = dict(result) if result else {
        "message": "Sin datos aun - carga el dataset primero"
    }
    cache_set(cache_key, payload)
    return payload


@router.get("/stats")
def get_stats(
    region: Optional[str] = Query(None, description="Filtrar por region"),
    db: Session = Depends(get_db),
):
    """
    Distribuciones estadisticas para el StatsPanel del dashboard.
    Retorna: distribucion_riesgo, distribucion_inseguridad,
             comorbilidades, distribucion_quintil.
    """
    cache_key = f"indicadores:stats:{region or 'all'}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    where = "WHERE 1=1"
    params: dict = {}
    if region:
        where += " AND h.region = :region"
        params["region"] = region

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
        JOIN personas p ON p.hogar_id = h.id
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
        JOIN personas p ON p.hogar_id = h.id
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
    db: Session = Depends(get_db),
):
    """
    Evolucion mensual de indicadores nutricionales.
    Usa fecha_calculo de indicadores_nutricionales para agrupar por mes.
    Si no hay datos temporales suficientes, retorna serie sintetica calibrada.
    """
    where = "WHERE 1=1"
    params: dict = {}
    if region:
        where += " AND h.region = :region"
        params["region"] = region

    sql = f"""
        SELECT
            strftime('%Y-%m', i.fecha_calculo) AS mes,
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
        GROUP BY strftime('%Y-%m', i.fecha_calculo)
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

    # Fallback: serie sintetica de 6 meses calibrada con dataset Maule
    import random
    random.seed(42)
    from datetime import date, timedelta
    meses_list = []
    base_date = date.today().replace(day=1)
    for i in range(meses, 0, -1):
        m = (base_date.replace(day=1) - timedelta(days=30 * (i - 1)))
        label = m.strftime("%Y-%m")
        riesgo_alto = round(28 + random.uniform(-3, 3), 1)
        meses_list.append({
            "mes": label,
            "total": 1200,
            "pct_riesgo_alto": riesgo_alto,
            "pct_riesgo_medio": round(7 + random.uniform(-1, 1), 1),
            "pct_inseg_moderada_severa": round(11 + random.uniform(-2, 2), 1),
        })
    return {"serie": meses_list, "es_sintetica": True}
