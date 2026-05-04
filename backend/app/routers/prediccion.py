from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class BeneficiarioInput(BaseModel):
    edad: int
    sexo: str  # "M" o "F"
    region: str
    imc: Optional[float] = None
    ingreso_hogar: Optional[float] = None
    acceso_pacam: Optional[bool] = None
    vive_solo: Optional[bool] = None


class PrediccionOutput(BaseModel):
    riesgo: str          # "alto", "medio", "bajo"
    probabilidad: float  # 0.0 - 1.0
    factores_principales: list[str]


@router.post("/", response_model=PrediccionOutput)
def predecir_riesgo(data: BeneficiarioInput):
    """
    Predice el nivel de riesgo de desnutrición usando el modelo ML (árbol de decisión).
    TODO: Cargar modelo entrenado con dataset CASEN/ENS.
    """
    # Placeholder — modelo ML se implementa en S7-S11
    return PrediccionOutput(
        riesgo="medio",
        probabilidad=0.5,
        factores_principales=["imc", "ingreso_hogar"],
    )
