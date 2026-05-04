from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()


@router.get("/")
def get_indicadores(
    region: Optional[str] = Query(None, description="Código de región"),
    comuna: Optional[str] = Query(None, description="Código de comuna"),
    grupo_etario: Optional[str] = Query(None, description="Grupo etario (60-74, 75+)"),
):
    """
    Retorna indicadores nutricionales agregados por zona geográfica.
    Filtrables por región, comuna y grupo etario.
    """
    # TODO: Conectar con base de datos PostgreSQL
    return {
        "region": region,
        "comuna": comuna,
        "grupo_etario": grupo_etario,
        "indicadores": {
            "pct_riesgo_desnutricion": 0.0,
            "pct_inseguridad_alimentaria": 0.0,
            "pct_beneficiarios_pacam": 0.0,
            "total_adultos_mayores": 0,
        },
    }


@router.get("/resumen")
def get_resumen_nacional():
    """Resumen de indicadores a nivel nacional."""
    return {"message": "Resumen nacional — pendiente conexión BD"}
