"""
Router: /api/v1/comunas
=======================
Endpoints para estadísticas agregadas por comuna.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.comuna import ComunaResumen

router = APIRouter()


# ─── Schemas de respuesta ────────────────────────────────────

class ComunaOut(BaseModel):
    id: int
    comuna_cod: str
    comuna_nombre: str
    region_cod: str
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
        description="Filtrar por nivel de riesgo zona (critico/alto/medio/bajo)"
    ),
    db: Session = Depends(get_db),
):
    """Retorna estadísticas agregadas por comuna, con filtros opcionales."""
    q = db.query(ComunaResumen)

    if region_cod:
        q = q.filter(ComunaResumen.region_cod == region_cod)
    if nivel_riesgo:
        q = q.filter(ComunaResumen.nivel_riesgo_zona == nivel_riesgo)

    comunas = q.order_by(
        ComunaResumen.pct_riesgo_alto_crit.desc()
    ).all()

    return {"total": len(comunas), "comunas": comunas}


@router.get("/{comuna_cod}", response_model=ComunaOut)
def detalle_comuna(
    comuna_cod: str,
    db: Session = Depends(get_db),
):
    """Retorna el resumen estadístico de una comuna específica."""
    comuna = db.query(ComunaResumen).filter(
        ComunaResumen.comuna_cod == comuna_cod
    ).first()

    if not comuna:
        raise HTTPException(
            status_code=404,
            detail=f"Comuna con código '{comuna_cod}' no encontrada"
        )

   