"""
Pesos poblacionales reales de personas de 60+ años por comuna de la Región
del Maule (Censo 2017, INE).
============================================================================
Se usan para distribuir de forma representativa (no aleatoria uniforme) los
registros de CASEN 2022 / ENS 2016-2017 entre comunas, ya que la extracción
de CASEN 2022 disponible para este proyecto NO incluye la variable comuna
(solo región) — ver sección 7.5 / Anexo A de la memoria.

IMPORTANTE — limitación declarada: la comuna asignada a cada persona real
es una ESTIMACIÓN basada en el peso poblacional de su comuna, no un dato
observado. Sirve para poblar el mapa de forma representativa a nivel
agregado, pero el detalle comunal de una persona específica no debe
interpretarse como un hecho medido.

Fuente: Censo de Población y Vivienda 2017 (INE), grupos etarios 60+
sumados por comuna. Ver `adultXcom.xlsx` en la raíz del repositorio.
"""

import json
from pathlib import Path

_PESOS_PATH = Path(__file__).parent / "pesos_comuna_maule.json"

with open(_PESOS_PATH, encoding="utf-8") as _f:
    PESOS_COMUNA_MAULE_60PLUS: dict[str, int] = json.load(_f)
