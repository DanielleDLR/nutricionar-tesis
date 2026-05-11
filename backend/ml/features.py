"""
features.py — Ingeniería de características para el modelo de riesgo nutricional
=================================================================================
Define las features utilizadas para entrenar y predecir con el árbol de decisión.
Centraliza la lógica de transformación para garantizar consistencia entre
entrenamiento e inferencia.
"""

import numpy as np
import pandas as pd

# ─── Definición de features ──────────────────────────────────────────────────

# Orden estable de las 18 features del modelo
FEATURE_NAMES = [
    # Sociodemográficas
    "edad",
    "sexo_num",           # 0=M, 1=F
    "zona_num",           # 0=urbano, 1=rural
    "ingreso_per_capita", # en miles de CLP
    "num_carencias",      # 0–5 carencias RSH
    "hacinamiento",       # bool

    # Estado nutricional / antropometría
    "imc",
    "circ_pantorrilla",   # cm
    "puntaje_mna",        # 0–30
    "perdio_peso",        # bool

    # Morbilidades
    "diabetes",
    "hta",
    "depresion",
    "limitacion_fisica",

    # Inseguridad alimentaria
    "inseg_alimentaria",  # 0=seguro, 1=leve, 2=moderado, 3=severo

    # Acceso a programas
    "acceso_pacam",       # bool

    # Factores MNA
    "movilidad_num",      # 0=cama/silla, 1=puede salir, 2=sale
    "vive_solo",          # bool
]

# Etiquetas → entero para el modelo
NIVEL_RIESGO_MAP = {
    "bajo":    0,
    "medio":   1,
    "alto":    2,
    "critico": 3,
}
NIVEL_RIESGO_INV = {v: k for k, v in NIVEL_RIESGO_MAP.items()}

INSEG_MAP = {
    "seguro": 0, "leve": 1, "moderado": 2, "severo": 3,
    0: 0, 1: 1, 2: 2, 3: 3,
}

MOVILIDAD_MAP = {
    0: 0, 1: 1, 2: 2,      # numérico directo
    "cama": 0, "interior": 1, "sale": 2,
}

MEDIANS: dict = {}  # se rellena durante entrenamiento


def _safe_float(val, default: float = 0.0) -> float:
    try:
        v = float(val)
        return v if np.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def _safe_bool(val, default: bool = False) -> float:
    if isinstance(val, bool):
        return float(val)
    if isinstance(val, (int, float)):
        return float(bool(val))
    return float(default)


def build_feature_vector(record: dict, medians: dict | None = None) -> np.ndarray:
    """
    Convierte un dict con datos de una persona en el vector de features del modelo.

    Parámetros de entrada esperados (todos opcionales con fallback a medianas):
        edad, sexo, zona, ingreso_per_capita, num_carencias, hacinamiento,
        imc, circ_pantorrilla, puntaje_mna, perdio_peso,
        diabetes, hta, depresion, limitacion_fisica,
        inseg_alimentaria, acceso_pacam, movilidad, vive_solo
    """
    m = medians or MEDIANS

    edad = _safe_float(record.get("edad"), m.get("edad", 72))
    sexo = 1.0 if str(record.get("sexo", "M")).upper() in ("F", "MUJER", "1") else 0.0
    zona = 1.0 if str(record.get("zona", "urbano")).lower() == "rural" else 0.0
    ingreso = _safe_float(
        record.get("ingreso_per_capita"), m.get("ingreso_per_capita", 250.0)
    ) / 1000.0  # normalizar a miles de CLP

    num_carencias = _safe_float(
        record.get("num_carencias"), m.get("num_carencias", 1.0)
    )
    hacinamiento = _safe_bool(record.get("hacinamiento", False))

    imc = _safe_float(record.get("imc"), m.get("imc", 24.5))
    pantorrilla = _safe_float(
        record.get("circ_pantorrilla"), m.get("circ_pantorrilla", 33.0)
    )
    mna = _safe_float(record.get("puntaje_mna"), m.get("puntaje_mna", 22.0))
    perdio_peso = _safe_bool(record.get("perdio_peso", False))

    diabetes = _safe_bool(record.get("diabetes", False))
    hta = _safe_bool(record.get("hta", False))
    depresion = _safe_bool(record.get("depresion", False))
    lim_fisica = _safe_bool(record.get("limitacion_fisica", False))

    inseg_raw = record.get("inseg_alimentaria", 0)
    inseg = float(INSEG_MAP.get(inseg_raw, _safe_float(inseg_raw, 0.0)))

    acceso_pacam = _safe_bool(record.get("acceso_pacam", False))

    movilidad_raw = record.get("movilidad", 1)
    movilidad = float(MOVILIDAD_MAP.get(movilidad_raw, 1.0))

    vive_solo = _safe_bool(record.get("vive_solo", False))

    return np.array([
        edad, sexo, zona, ingreso, num_carencias, hacinamiento,
        imc, pantorrilla, mna, perdio_peso,
        diabetes, hta, depresion, lim_fisica,
        inseg, acceso_pacam, movilidad, vive_solo,
    ], dtype=float)


def build_training_matrix(
    df_personas: pd.DataFrame,
    df_nutric: pd.DataFrame,
    df_inseg: pd.DataFrame,
    df_acceso: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Fusiona las 4 hojas del dataset y construye X, y listos para sklearn.
    Retorna (X_df, y_series) donde y está codificada como entero.
    """
    # Normalizar ids
    for df in [df_personas, df_nutric, df_inseg, df_acceso]:
        df["id_persona"] = df["id_persona"].astype(str).str.strip()

    merged = (
        df_personas
        .merge(df_nutric,  on="id_persona", how="inner", suffixes=("", "_n"))
        .merge(df_inseg,   on="id_persona", how="left",  suffixes=("", "_i"))
        .merge(df_acceso,  on="id_persona", how="left",  suffixes=("", "_a"))
    )

    # Calcular medianas globales (usadas en inferencia)
    global MEDIANS
    MEDIANS["edad"]             = float(merged["edad"].median())
    MEDIANS["ingreso_per_capita"] = float(
        merged["ingreso_per_capita"].median()
    ) if "ingreso_per_capita" in merged.columns else 250_000.0
    MEDIANS["imc"]              = float(merged["imc"].median())
    MEDIANS["circ_pantorrilla"] = float(merged["circ_pantorrilla_cm"].median())
    MEDIANS["puntaje_mna"]      = float(merged["puntaje_mna"].median())
    MEDIANS["num_carencias"]    = float(
        merged.get("num_carencias_total", pd.Series([1])).median()
    )

    rows = []
    for _, r in merged.iterrows():
        record = {
            "edad":             r.get("edad"),
            "sexo":             r.get("sexo"),
            "zona":             "rural" if r.get("zona_urbano_rural") == 2 else "urbano",
            "ingreso_per_capita": r.get("ingreso_per_capita"),
            "num_carencias":    r.get("num_carencias_total", 1),
            "hacinamiento":     bool(r.get("hacinamiento", False)),
            "imc":              r.get("imc"),
            "circ_pantorrilla": r.get("circ_pantorrilla_cm"),
            "puntaje_mna":      r.get("puntaje_mna"),
            "perdio_peso":      bool(r.get("perdio_peso_3m", False)),
            "diabetes":         bool(r.get("diagnostico_diabetes", False)),
            "hta":              bool(r.get("diagnostico_hta", False)),
            "depresion":        bool(r.get("diagnostico_depresion", False)),
            "limitacion_fisica": bool(r.get("limitacion_fisica", False)),
            "inseg_alimentaria": r.get("nivel_inseguridad", 0),
            "acceso_pacam":     bool(r.get("beneficiario_pacam", False)),
            "movilidad":        r.get("movilidad", 1),
            "vive_solo":        bool(
                str(r.get("tipo_nucleo_familiar", "")).lower()
                in ("unipersonal", "solo")
            ),
        }
        rows.append(build_feature_vector(record, MEDIANS))

    X = pd.DataFrame(rows, columns=FEATURE_NAMES)

    # Target: nivel_riesgo → entero
    y = merged["nivel_riesgo"].map(NIVEL_RIESGO_MAP).fillna(1).astype(int)

    return X, y
