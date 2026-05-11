from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from app.database import get_db

router = APIRouter()


@router.get("/")
def get_indicadores(
    region: Optional[str] = Query(None, description="Código de región (ej. '07')"),
    zona: Optional[str] = Query(None, description="'urbano' o 'rural'"),
    db: Session = Depends(get_db),
):
    """
    Indicadores nutricionales agregados desde la vista resumen regional.
    Filtrables por región y zona.
    """
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
    """Totales nacionales de indicadores nutricionales."""
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

    return dict(result) if result else {"message": "Sin datos aún — carga el dataset primero"}
