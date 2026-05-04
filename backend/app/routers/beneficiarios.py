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

    total = db.execute(text(f"SELECT COUNT(*) {base}"), params).scalar()

    rows = db.execute(text(f"""
        SELECT p.id, p.edad, p.sexo, h.region, h.comuna, h.zona,
               p.imc, p.nivel_inseguridad, i.nivel_riesgo, i.probabilidad_riesgo
        {base}
        ORDER BY i.probabilidad_riesgo DESC
        LIMIT :limit OFFSET :offset
    """), {**params, "limit": page_size, "offset": offset}).mappings().all()

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": [dict(r) for r in rows],
    }


@router.get("/{beneficiario_id}")
def get_beneficiario(
    beneficiario_id: int = Path(..., description="ID del adulto mayor"),
    db: Session = Depends(get_db),
):
    """Detalle completo de un adulto mayor y su evaluación nutricional."""
    row = db.execute(text("""
        SELECT p.*, h.region, h.comuna, h.zona, h.ingreso_total, h.quintil_ingreso,
               h.acceso_pacam, h.acceso_rsh,
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
