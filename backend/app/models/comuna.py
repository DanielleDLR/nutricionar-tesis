from sqlalchemy import Column, Integer, String, Float
from app.database import Base


class ComunaResumen(Base):
    __tablename__ = "comunas_resumen"

    id = Column(Integer, primary_key=True, index=True)
    comuna_cod = Column(String(5), unique=True, nullable=False, index=True)
    comuna_nombre = Column(String(100), nullable=False)
    region_cod = Column(String(2), nullable=False, index=True)
    # Centroide geográfico (fuente: cartografía pública INE). Alimenta el mapa.
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
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

    # Vigilancia Nutricional REM P5 (MINSAL) — registro administrativo oficial
    # de personas mayores bajo control, no la muestra CASEN/ENS/sintética.
    n_control_rem = Column(Integer, nullable=True)
    pct_normal_rem = Column(Float, nullable=True)
    pct_bajo_peso_rem = Column(Float, nullable=True)
