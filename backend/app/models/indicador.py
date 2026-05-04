from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class IndicadorNutricional(Base):
    __tablename__ = "indicadores_nutricionales"

    id = Column(Integer, primary_key=True, index=True)
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=False, index=True)

    # Clasificación de riesgo (salida del modelo ML)
    nivel_riesgo = Column(String(10), nullable=False)            # "alto" / "medio" / "bajo"
    probabilidad_riesgo = Column(Float, nullable=True)           # 0.0 - 1.0

    # Indicadores calculados
    estado_nutricional = Column(String(20), nullable=True)       # "normal" / "bajo peso" / "obesidad"
    riesgo_sarcopenia = Column(String(10), nullable=True)        # "si" / "no" / "probable"
    riesgo_desnutricion = Column(String(10), nullable=True)      # "si" / "no" / "probable"

    # Factores principales detectados por el modelo
    factor_1 = Column(String(50), nullable=True)
    factor_2 = Column(String(50), nullable=True)
    factor_3 = Column(String(50), nullable=True)

    # Metadatos
    modelo_version = Column(String(20), nullable=True)
    fecha_calculo = Column(DateTime, server_default=func.now())

    # Relaciones
    persona = relationship("Persona", back_populates="indicadores")
