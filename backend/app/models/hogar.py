from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Hogar(Base):
    __tablename__ = "hogares"

    id = Column(Integer, primary_key=True, index=True)

    # Identificación geográfica
    region = Column(String(2), nullable=False, index=True)       # Código región (ej. "07")
    provincia = Column(String(3), nullable=True)
    comuna = Column(String(5), nullable=True, index=True)
    zona = Column(String(10), nullable=True)                     # "urbano" / "rural"

    # Características socioeconómicas
    ingreso_total = Column(Float, nullable=True)
    quintil_ingreso = Column(Integer, nullable=True)             # 1-5
    n_integrantes = Column(Integer, nullable=True)
    hacinamiento = Column(Boolean, default=False)

    # Acceso a programas
    acceso_pacam = Column(Boolean, default=False)
    acceso_rsh = Column(Boolean, default=False)

    # Relaciones
    personas = relationship("Persona", back_populates="hogar")
