from sqlalchemy import Column, Integer, String, Float
from app.database import Base


class ComunaResumen(Base):
    __tablename__ = "comunas_resumen"

    id = Column(Integer, primary_key=True, index=True)
    comuna_cod = Column(String(5), unique=True, nullable=False, index=True)
    comuna_nombre = Column(String(100), nullable=False)
    region_cod = Column(String(2), nullable=False, index=True)
    total_personas = Column(Integer, default=0)
    n_desnutricion = Column(Integer, default=0)
    n_riesgo = Column(Integer, default=0)
    n_normal = Column(Integer, default=0)
    pct_desnutricion = Column(Float, default=0.0)
    pct_riesgo_mna = Column(Float, default=0.0)
    pct_inseg_severa = Column(Float, default=0.0)
    pct_inseg_mod_sev = Column(Float, default=0.0)
    n_benef_pacam = Column(Integer, default=0)
    pct_no_retiro_pacam = Column(Float, default=0.0)
    n_critico = Column(Integer, default=0)
    n_alto = Column(Integer, default=0)
    pct_riesgo_alto_crit = Column(Float, default=0.0)
    nivel_riesgo_zona = Column(String(20), nullable=True)
