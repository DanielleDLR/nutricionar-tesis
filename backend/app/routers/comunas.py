"""
Router: /api/v1/comunas
=======================
Endpoints para estadísticas agregadas por comuna.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.comuna import ComunaResumen
from app.routers.indicadores import aplicar_filtros

router = APIRouter()


def _nivel_desde_pct(pct: float) -> str:
    """Nivel de riesgo de la zona según el % de riesgo alto/crítico."""
    if pct >= 40:
        return "critico"
    if pct >= 25:
        return "alto"
    if pct >= 10:
        return "medio"
    return "bajo"


# ─── Schemas de respuesta ────────────────────────────────────

class ComunaOut(BaseModel):
    id: int
    comuna_cod: str
    comuna_nombre: str
    region_cod: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    total_personas: int
    n_desnutricion: int
    n_riesgo: int
    n_normal: int
    pct_desnutricion: float
    pct_riesgo_mna: float
    pct_inseg_severa: float
    pct_inseg_mod_sev: float
    n_benef_pacam: int
    pct_no_retiro_pacam: float
    n_critico: int
    n_alto: int
    pct_riesgo_alto_crit: float
    nivel_riesgo_zona: Optional[str] = None
    # Vigilancia Nutricional REM P5 (MINSAL) — registro administrativo oficial,
    # independiente de los filtros de persona (sexo/grupo_etario/pacam/fuente).
    n_control_rem: Optional[int] = None
    pct_normal_rem: Optional[float] = None
    pct_bajo_peso_rem: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ComunasResponse(BaseModel):
    total: int
    comunas: List[ComunaOut]


# ─── Endpoints ───────────────────────────────────────────────

@router.get("/", response_model=ComunasResponse)
def listar_comunas(
    region_cod: Optional[str] = Query(
        None, description="Filtrar por código de región (ej: '07')"
    ),
    nivel_riesgo: Optional[str] = Query(
        None,
        description=(
            "Filtrar por nivel de riesgo zona; admite múltiples valores "
            "separados por coma (ej: 'critico,alto')"
        ),
    ),
    sexo: Optional[str] = Query(None, description="'F', 'M' o 'F,M'"),
    grupo_etario: Optional[str] = Query(
        None, description="'65-74', '75-84', '85+' (coma = OR)"
    ),
    pacam: Optional[str] = Query(
        None, description="'beneficiarios', 'no_retiradores' o 'sin_cobertura'"
    ),
    fuente: Optional[str] = Query(
        None, description="'SINTETICO', 'CASEN_ENS_REAL' o ambos separados por coma"
    ),
    db: Session = Depends(get_db),
):
    """Estadísticas por comuna recalculadas sobre el subconjunto filtrado.

    Se agregan en vivo desde personas/hogares/indicadores (no desde la tabla
    pre-agregada) para que sexo, grupo etario, PACAM y fuente tengan efecto.
    Las coordenadas y los campos descriptivos provienen de `comunas_resumen`.
    """
    # Filtros a nivel de persona (el nivel de riesgo de zona se aplica luego,
    # sobre el porcentaje recalculado).
    where, params = aplicar_filtros(
        "WHERE 1=1", {}, region=region_cod, sexo=sexo,
        grupo_etario=grupo_etario, pacam=pacam, fuente=fuente,
    )

    # Niveles de riesgo zona aceptados (CSV → lista); None = sin filtro.
    niveles = (
        [n.strip() for n in nivel_riesgo.split(",") if n.strip()]
        if nivel_riesgo else None
    )

    filas = db.execute(text(f"""
        SELECT h.comuna AS cod,
               COUNT(*) AS total_personas,
               SUM(CASE WHEN i.nivel_riesgo = 'critico' THEN 1 ELSE 0 END) AS n_critico,
               SUM(CASE WHEN i.nivel_riesgo = 'alto'    THEN 1 ELSE 0 END) AS n_alto,
               SUM(CASE WHEN p.nivel_inseguridad = 'severo'
                   THEN 1 ELSE 0 END) AS n_inseg_severa,
               SUM(CASE WHEN p.nivel_inseguridad IN ('moderado','severo')
                   THEN 1 ELSE 0 END) AS n_inseg_mod_sev,
               SUM(CASE WHEN h.acceso_pacam = TRUE THEN 1 ELSE 0 END) AS n_benef_pacam
        FROM personas p
        JOIN hogares h                   ON h.id = p.hogar_id
        JOIN indicadores_nutricionales i ON i.persona_id = p.id
        {where}
        GROUP BY h.comuna
    """), params).mappings().all()

    # Metadatos estáticos (coordenadas, nombre, campos descriptivos) por comuna.
    meta = {c.comuna_cod: c for c in db.query(ComunaResumen).all()}

    comunas = []
    for f in filas:
        cod = f["cod"]
        if not cod:
            continue
        m = meta.get(cod)
        total = f["total_personas"] or 0
        n_alto = f["n_alto"] or 0
        n_critico = f["n_critico"] or 0
        pct_alto_crit = round(100.0 * (n_alto + n_critico) / total, 2) if total else 0.0
        nivel = _nivel_desde_pct(pct_alto_crit)

        # El filtro de nivel de riesgo de zona se aplica sobre el % recalculado.
        if niveles and nivel not in niveles:
            continue

        comunas.append({
            "id": m.id if m else 0,
            "comuna_cod": cod,
            "comuna_nombre": (m.comuna_nombre if m else cod),
            "region_cod": (m.region_cod if m else (region_cod or "")),
            "lat": (m.lat if m else None),
            "lon": (m.lon if m else None),
            "total_personas": total,
            "n_desnutricion": (m.n_desnutricion if m else 0),
            "n_riesgo": (m.n_riesgo if m else 0),
            "n_normal": (m.n_normal if m else 0),
            "pct_desnutricion": (m.pct_desnutricion if m else 0.0),
            "pct_riesgo_mna": (m.pct_riesgo_mna if m else 0.0),
            "pct_inseg_severa": (
                round(100.0 * (f["n_inseg_severa"] or 0) / total, 2) if total else 0.0
            ),
            "pct_inseg_mod_sev": (
                round(100.0 * (f["n_inseg_mod_sev"] or 0) / total, 2) if total else 0.0
            ),
            "n_benef_pacam": f["n_benef_pacam"] or 0,
            "pct_no_retiro_pacam": (m.pct_no_retiro_pacam if m else 0.0),
            "n_critico": n_critico,
            "n_alto": n_alto,
            "pct_riesgo_alto_crit": pct_alto_crit,
            "nivel_riesgo_zona": nivel,
            "n_control_rem": (m.n_control_rem if m else None),
            "pct_normal_rem": (m.pct_normal_rem if m else None),
            "pct_bajo_peso_rem": (m.pct_bajo_peso_rem if m else None),
        })

    comunas.sort(key=lambda c: c["pct_riesgo_alto_crit"], reverse=True)
    return {"total": len(comunas), "comunas": comunas}


@router.get("/{comuna_cod}", response_model=ComunaOut)
def detalle_comuna(
    comuna_cod: str,
    sexo: Optional[str] = Query(None, description="'F', 'M' o 'F,M'"),
    grupo_etario: Optional[str] = Query(
        None, description="'65-74', '75-84', '85+' (coma = OR)"
    ),
    pacam: Optional[str] = Query(
        None, description="'beneficiarios', 'no_retiradores' o 'sin_cobertura'"
    ),
    fuente: Optional[str] = Query(
        None, description="'SINTETICO', 'CASEN_ENS_REAL' o ambos separados por coma"
    ),
    db: Session = Depends(get_db),
):
    """Detalle de una comuna, recalculado en vivo (misma lógica que el
    listado) para que sexo/grupo_etario/pacam/fuente tengan efecto. Nombre y
    coordenadas provienen de `comunas_resumen`."""
    meta = db.query(ComunaResumen).filter(
        ComunaResumen.comuna_cod == comuna_cod
    ).first()
    if not meta:
        raise HTTPException(
            status_code=404,
            detail=f"Comuna con código '{comuna_cod}' no encontrada"
        )

    where, params = aplicar_filtros(
        "WHERE h.comuna = :comuna_cod", {"comuna_cod": comuna_cod},
        sexo=sexo, grupo_etario=grupo_etario, pacam=pacam, fuente=fuente,
    )
    fila = db.execute(text(f"""
        SELECT COUNT(*) AS total_personas,
               SUM(CASE WHEN i.nivel_riesgo = 'critico' THEN 1 ELSE 0 END) AS n_critico,
               SUM(CASE WHEN i.nivel_riesgo = 'alto'    THEN 1 ELSE 0 END) AS n_alto,
               SUM(CASE WHEN p.nivel_inseguridad = 'severo'
                   THEN 1 ELSE 0 END) AS n_inseg_severa,
               SUM(CASE WHEN p.nivel_inseguridad IN ('moderado','severo')
                   THEN 1 ELSE 0 END) AS n_inseg_mod_sev,
               SUM(CASE WHEN h.acceso_pacam = TRUE THEN 1 ELSE 0 END) AS n_benef_pacam
        FROM personas p
        JOIN hogares h                   ON h.id = p.hogar_id
        JOIN indicadores_nutricionales i ON i.persona_id = p.id
        {where}
    """), params).mappings().one()

    total = fila["total_personas"] or 0
    n_alto = fila["n_alto"] or 0
    n_critico = fila["n_critico"] or 0
    pct_alto_crit = round(100.0 * (n_alto + n_critico) / total, 2) if total else 0.0

    return {
        "id": meta.id,
        "comuna_cod": comuna_cod,
        "comuna_nombre": meta.comuna_nombre,
        "region_cod": meta.region_cod,
        "lat": meta.lat,
        "lon": meta.lon,
        "total_personas": total,
        "n_desnutricion": meta.n_desnutricion,
        "n_riesgo": meta.n_riesgo,
        "n_normal": meta.n_normal,
        "pct_desnutricion": meta.pct_desnutricion,
        "pct_riesgo_mna": meta.pct_riesgo_mna,
        "pct_inseg_severa": (
            round(100.0 * (fila["n_inseg_severa"] or 0) / total, 2) if total else 0.0
        ),
        "pct_inseg_mod_sev": (
            round(100.0 * (fila["n_inseg_mod_sev"] or 0) / total, 2) if total else 0.0
        ),
        "n_benef_pacam": fila["n_benef_pacam"] or 0,
        "pct_no_retiro_pacam": meta.pct_no_retiro_pacam,
        "n_critico": n_critico,
        "n_alto": n_alto,
        "pct_riesgo_alto_crit": pct_alto_crit,
        "nivel_riesgo_zona": _nivel_desde_pct(pct_alto_crit),
        "n_control_rem": meta.n_control_rem,
        "pct_normal_rem": meta.pct_normal_rem,
        "pct_bajo_peso_rem": meta.pct_bajo_peso_rem,
    }
