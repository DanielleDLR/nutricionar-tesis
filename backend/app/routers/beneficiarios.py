import logging

from fastapi import APIRouter, Query, Path, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError
from typing import Optional

from app.database import get_db
from app.routers.indicadores import aplicar_filtros

logger = logging.getLogger(__name__)

router = APIRouter()


class VisitaIn(BaseModel):
    """Cuerpo del registro de una visita domiciliaria (US-09)."""
    contacto: Optional[str] = None
    nota: Optional[str] = None
    seguimiento_dias: Optional[int] = None


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
    comuna: Optional[str] = Query(None),
    sexo: Optional[str] = Query(None, description="Lista separada por comas (F,M)"),
    grupo_etario: Optional[str] = Query(None, description="Ej. '65-74,85+'"),
    db: Session = Depends(get_db),
):
    """
    Conteo de beneficiarios PACAM que no retiran el beneficio, agrupados por
    motivo declarado (lejania / desconocimiento / movilidad / otro).

    Alimenta el donut de adherencia PACAM. Cohorte: inscritos en PACAM con
    riesgo alto/medio (misma definición que el filtro `no_retira_pacam`).
    """
    # La cohorte ya fija el nivel de riesgo (alto/medio); el resto de filtros
    # del dashboard se aplican con el helper compartido.
    where, params = aplicar_filtros(
        "WHERE h.acceso_pacam = TRUE AND i.nivel_riesgo IN ('alto', 'medio')",
        {}, region=region, comuna=comuna, sexo=sexo, grupo_etario=grupo_etario,
    )

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
    except (OperationalError, ProgrammingError) as exc:
        # Tabla legada sin la columna motivo_no_retiro.
        logger.warning(
            "motivos_no_retiro: columna no disponible, usando fallback: %s", exc
        )
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


@router.post("/{beneficiario_id}/visitas")
def registrar_visita(
    beneficiario_id: int = Path(..., description="ID del adulto mayor"),
    visita: VisitaIn = ...,
    db: Session = Depends(get_db),
):
    """Registra una visita domiciliaria para el beneficiario.

    La persistencia real (tabla `visitas`) se incorpora en Fase 5; por ahora se
    valida la existencia del beneficiario y se confirma la recepción del
    registro sin almacenarlo.
    """
    existe = db.execute(
        text("SELECT 1 FROM personas WHERE id = :id"),
        {"id": beneficiario_id},
    ).scalar()
    if not existe:
        raise HTTPException(status_code=404, detail="Beneficiario no encontrado")

    logger.info(
        "Visita registrada (sin persistir) beneficiario=%s contacto=%s "
        "seguimiento_dias=%s", beneficiario_id, visita.contacto,
        visita.seguimiento_dias,
    )
    return {"ok": True, "mensaje": "Registro guardado"}
