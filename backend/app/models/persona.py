from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Persona(Base):
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    hogar_id = Column(Integer, ForeignKey("hogares.id"), nullable=False, index=True)

    # Datos demográficos
    edad = Column(Integer, nullable=False)
    sexo = Column(String(1), nullable=False)                     # "M" / "F"
    fecha_nacimiento = Column(Date, nullable=True)
    estado_civil = Column(String(20), nullable=True)
    escolaridad = Column(String(50), nullable=True)
    vive_solo = Column(Boolean, default=False)

    # Salud y nutrición
    peso_kg = Column(Float, nullable=True)
    talla_cm = Column(Float, nullable=True)
    imc = Column(Float, nullable=True)                           # kg/m²
    circunferencia_pantorrilla = Column(Float, nullable=True)    # cm (marcador sarcopenia)
    tiene_diabetes = Column(Boolean, default=False)
    tiene_hipertension = Column(Boolean, default=False)
    tiene_depresion = Column(Boolean, default=False)

    # Seguridad alimentaria (escala ELCSA)
    puntaje_elcsa = Column(Integer, nullable=True)               # 0-15
    nivel_inseguridad = Column(String(10), nullable=True)        # seguro/leve/moderado/severo

    # Fuente del dato
    fuente = Column(String(20), nullable=True)                   # "CASEN", "ENS", "SINTETICO"
    anio_encuesta = Column(Integer, nullable=True)

    # Relaciones
    hogar = relationship("Hogar", back_populates="personas")
    indicadores = relationship("IndicadorNutricional", back_populates="persona")
