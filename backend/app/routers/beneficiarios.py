from fastapi import APIRouter, Query, Path, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from app.database import get_db

router = APIRouter()


@router.get("/")
def list_beneficiarios(
    region: Optional[str] = Query(None),
    riesgo: Optional[str] = Query(None, description="alto, medio, bajo"),
    zona: Optional[str] = Query(None, description="urbano, rural"),
    no_retira_pacam: Optional[bool] = Query(
        None, description="True para filtrar solo beneficiarios PACAM que no retiran"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lista paginada de adultos mayores con su nivel de riesgo nutricional."""
    offset = (page - 1) * page_size

    base = """
        FROM personas p
        JOIN hogares h                   ON h.id = p.hogar_id
        JOIN indicadores_nutricionales i ON i.persona_id = p.id
        WHERE 1=1
    """
    params: dict = {}

    if region:
        base += " AND h.region = :region"
        params["region"] = region
    if riesgo:
        base += " AND i.nivel_riesgo = :riesgo"
        params["riesgo"] = riesgo
    if zona:
        base += " AND h.zona = :zona"
        params["zona"] = zona
    if no_retira_pacam is True:
        # Beneficiarios inscritos en PACAM (acceso_pacam=TRUE) pero con riesgo alto/medio
        base += " AND h.acceso_pacam = TRUE AND i.nivel_riesgo IN ('alto', 'medio')"

    total = db.execute(text(f"SELECT COUNT(*) {base}"), params).scalar()

    rows = db.execute(text(f"""
        SELECT p.id, p.edad, p.sexo, h.region, h.comuna, h.zona,
               p.imc, p.nivel_inseguridad, p.vive_solo,
               p.tiene_diabetes, p.tiene_hipertension, p.tiene_depresion,
               h.acceso_pacam, h.quintil_ingreso,
               i.nivel_riesgo, i.probabilidad_riesgo
        {base}
        ORDER BY i.probabilidad_riesgo DESC NULLS LAST
        LIMIT :limit OFFSET :offset
    """), {**params, "limit": page_size, "offset": offset}).mappings().all()

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": [dict(r) for r in rows],
    }


MOTIVOS_NO_RETIRO = ["lejania", "desconocimiento", "movilidad", "otro"]

# Etiquetas legibles para el frontend (donut de adherencia PACAM).
MOTIVO_LABELS = {
    "lejania": "Lejanía / distancia al punto",
    "desconocimiento": "Desconocimiento del beneficio",
    "movilidad": "Movilidad reducida",
    "otro": "Otro",
}


@router.get("/no-retiro/motivos")
def motivos_no_retiro(
    region: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Conteo de beneficiarios PACAM que no retiran el beneficio, agrupados por
    motivo declarado (lejania / desconocimiento / movilidad / otro).

    Alimenta el donut de adherencia PACAM. Cohorte: inscritos en PACAM con
    riesgo alto/medio (misma definición que el filtro `no_retira_pacam`).
    """
    where = (
        "WHERE h.acceso_pacam = TRUE "
        "AND i.nivel_riesgo IN ('alto', 'medio')"
    )
    params: dict = {}
    if region:
        where += " AND h.region = :region"
        params["region"] = region

    try:
        rows = db.execute(text(f"""
            SELECT COALESCE(p.motivo_no_retiro, 'otro') AS motivo,
                   COUNT(*) AS n
            FROM personas p
            JOIN hogares h                   ON h.id = p.hogar_id
            JOIN indicadores_nutricionales i ON i.persona_id = p.id
            {where}
            GROUP BY COALESCE(p.motivo_no_retiro, 'otro')
        """), params).mappings().all()
        conteo = {r["motivo"]: r["n"] for r in rows}
    except Exception:
        # Tabla legada sin la columna motivo_no_retiro.
        conteo = {}

    total = sum(conteo.values())
    motivos = [
        {
            "motivo": m,
            "label": MOTIVO_LABELS[m],
            "n": conteo.get(m, 0),
            "pct": round(100.0 * conteo.get(m, 0) / total, 1) if total else 0.0,
        }
        for m in MOTIVOS_NO_RETIRO
    ]
    return {"total": total, "motivos": motivos}


@router.get("/{beneficiario_id}")
def get_beneficiario(
    beneficiario_id: int = Path(..., description="ID del adulto mayor"),
    db: Session = Depends(get_db),
):
    """Detalle completo de un adulto mayor y su evaluacion nutricional."""
    row = db.execute(text("""
        SELECT p.id, p.edad, p.sexo, p.vive_solo, p.estado_civil, p.escolaridad,
               p.peso_kg, p.talla_cm, p.imc, p.circunferencia_pantorrilla,
               p.tiene_diabetes, p.tiene_hipertension, p.tiene_depresion,
               p.puntaje_elcsa, p.nivel_inseguridad,
               h.region, h.comuna, h.zona, h.ingreso_total, h.quintil_ingreso,
               h.acceso_pacam, h.acceso_rsh, h.hacinamiento,
               i.nivel_riesgo, i.probabilidad_riesgo, i.estado_nutricional,
               i.riesgo_sarcopenia, i.riesgo_desnutricion,
               i.factor_1, i.factor_2, i.factor_3, i.fecha_calculo
        FROM personas p
        JOIN hogares h                   ON h.id = p.hogar_id
        JOIN indicadores_nutricionales i ON i.persona_id = p.id
        WHERE p.id = :id
    """), {"id": beneficiario_id}).mappings().one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Beneficiario no encontrado")

    return dict(row)
