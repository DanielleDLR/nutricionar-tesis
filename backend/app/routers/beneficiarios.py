from fastapi import APIRouter, Query, Path
from typing import Optional

router = APIRouter()


@router.get("/")
def list_beneficiarios(
    region: Optional[str] = Query(None),
    riesgo: Optional[str] = Query(None, description="alto, medio, bajo"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Lista paginada de beneficiarios con filtros."""
    return {
        "page": page,
        "page_size": page_size,
        "total": 0,
        "items": [],
    }


@router.get("/{beneficiario_id}")
def get_beneficiario(beneficiario_id: int = Path(..., description="ID del beneficiario")):
    """Detalle de un beneficiario específico."""
    return {"id": beneficiario_id, "data": "pendiente conexión BD"}
