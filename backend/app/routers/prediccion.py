"""
Router: /api/v1/prediccion
===========================
Exposición del modelo ML de árbol de decisión para predicción de riesgo
nutricional en adultos mayores de la Región del Maule.
"""

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter()


# ─── Schemas ─────────────────────────────────────────────────

class BeneficiarioInput(BaseModel):
    """Features de entrada para la predicción de riesgo nutricional."""

    # Sociodemográficas
    edad: int = Field(..., ge=60, le=120, description="Edad en años")
    sexo: str = Field(..., description="'M' o 'F'")
    zona: Optional[str] = Field("urbano", description="'urbano' o 'rural'")
    region: Optional[str] = Field("07", description="Código de región INE")
    ingreso_per_capita: Optional[float] = Field(
        None, description="Ingreso per cápita del hogar (CLP)"
    )
    num_carencias: Optional[int] = Field(
        0, ge=0, le=5, description="Nº carencias RSH (0-5)"
    )
    hacinamiento: Optional[bool] = Field(False)

    # Antropometría / estado nutricional
    imc: Optional[float] = Field(None, description="Índice de masa corporal")
    circ_pantorrilla: Optional[float] = Field(
        None, description="Circunferencia de pantorrilla (cm)"
    )
    puntaje_mna: Optional[float] = Field(
        None, ge=0, le=30, description="Puntaje MNA (0-30)"
    )
    perdio_peso: Optional[bool] = Field(
        False, description="Perdio peso en los ultimos 3 meses"
    )

    # Morbilidades
    diabetes: Optional[bool] = Field(False)
    hta: Optional[bool] = Field(False)
    depresion: Optional[bool] = Field(False)
    limitacion_fisica: Optional[bool] = Field(False)

    # Seguridad alimentaria (0=seguro, 1=leve, 2=moderado, 3=severo)
    inseg_alimentaria: Optional[int] = Field(0, ge=0, le=3)

    # Acceso a programas
    acceso_pacam: Optional[bool] = Field(False)
    vive_solo: Optional[bool] = Field(False)

    # Factor movilidad MNA (0=cama/silla, 1=puede salir de casa, 2=sale)
    movilidad: Optional[int] = Field(1, ge=0, le=2)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "edad": 75,
                "sexo": "F",
                "zona": "rural",
                "imc": 20.5,
                "puntaje_mna": 19,
                "diabetes": True,
                "depresion": True,
                "inseg_alimentaria": 2,
                "acceso_pacam": True,
                "vive_solo": True,
            }
        }
    )


class ProbabilidadNivel(BaseModel):
    nivel: str
    probabilidad: float


class PrediccionOutput(BaseModel):
    """Respuesta del modelo de predicción."""

    riesgo: str = Field(
        ..., description="Nivel de riesgo: bajo, medio, alto, critico"
    )
    probabilidad: float = Field(..., ge=0.0, le=1.0)
    factores_principales: List[str] = Field(
        ..., description="Features con mayor contribución a la predicción"
    )
    probabilidades: List[ProbabilidadNivel] = Field(
        default_factory=list,
        description="Probabilidad por cada nivel de riesgo"
    )
    modelo: str = Field(
        "RandomForestClassifier",
        description="Tipo de modelo usado"
    )
    usa_fallback: bool = Field(
        False, description="True si el modelo ML no esta disponible"
    )


class ModeloInfo(BaseModel):
    modelo_disponible: bool
    tipo: str
    n_features: int
    feature_names: List[str]
    metricas: dict


# ─── Endpoints ───────────────────────────────────────────────

@router.get("/info", response_model=ModeloInfo)
def info_modelo():
    """Retorna metadatos y metricas del modelo cargado."""
    from ml.predict import model_info
    return model_info()


@router.post("/", response_model=PrediccionOutput)
def predecir_riesgo(data: BeneficiarioInput):
    """
    Predice el nivel de riesgo de desnutricion usando el modelo ML.

    El modelo es un RandomForestClassifier entrenado sobre el dataset
    sintetico piloto Maule (N=1.200 registros). Incluye fallback heuristico
    cuando los artefactos del modelo no estan disponibles.
    """
    from ml.predict import model_info, predict

    record = data.model_dump()

    nivel, prob, factors, probs_all = predict(record)
    info = model_info()

    return PrediccionOutput(
        riesgo=nivel,
        probabilidad=prob,
        factores_principales=factors,
        probabilidades=[
            ProbabilidadNivel(**p) for p in probs_all
        ],
        modelo=info["tipo"],
        usa_fallback=not info["modelo_disponible"],
    )
