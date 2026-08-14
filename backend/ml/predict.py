"""
predict.py - Modulo de inferencia del modelo de riesgo nutricional
Carga los artefactos entrenados y expone predict() para el router FastAPI.
Soporta fallback heuristico si el modelo no esta disponible.
"""

import json
import logging
from functools import lru_cache
from pathlib import Path

import numpy as np

from ml.features import (
    FEATURE_NAMES,
    NIVEL_RIESGO_INV,
    build_feature_vector,
)

log = logging.getLogger(__name__)

ARTEFACTOS_DIR = Path(__file__).parent / "artefactos"


@lru_cache(maxsize=1)
def _load_model():
    """Carga el modelo RF y medianas una sola vez (cached)."""
    import pickle

    rf_path = ARTEFACTOS_DIR / "modelo_rf.pkl"
    med_path = ARTEFACTOS_DIR / "medians.pkl"

    if not rf_path.exists():
        log.warning(
            "Modelo ML no encontrado en %s - usando heuristica de fallback",
            rf_path,
        )
        return None, {}

    with open(rf_path, "rb") as f:
        model = pickle.load(f)
    medians = {}
    if med_path.exists():
        with open(med_path, "rb") as f:
            medians = pickle.load(f)

    log.info("Modelo ML cargado desde %s", rf_path)
    return model, medians


def _heuristic_predict(record: dict) -> tuple:
    """
    Prediccion heuristica de fallback basada en el IPRN (Indice Proxy de
    Riesgo Nutricional). Replica la formula del generador sintetico para
    mantener coherencia con el modelo entrenado. Se usa cuando el modelo
    .pkl no esta disponible.

    Nota: puntaje_mna NO se usa — no esta disponible en fuentes de datos
    reales (ENS 2017, CASEN 2022). Ver ml/features.py y la metodologia IPRN.
    """
    score = 0.0
    factors = []

    imc = float(record.get("imc") or 24.5)
    pant = float(record.get("circ_pantorrilla") or 33.0)
    inseg = record.get("inseg_alimentaria", 0)
    if isinstance(inseg, str):
        inseg = {"severo": 3, "moderado": 2, "leve": 1}.get(inseg, 0)
    edad = float(record.get("edad") or 72)
    movilidad = record.get("movilidad", 1)
    if isinstance(movilidad, str):
        movilidad = {"cama": 0, "interior": 1, "sale": 2}.get(movilidad, 1)

    # Item MNA-SF 6: IMC / circunferencia de pantorrilla
    if imc < 18.5:
        score += 0.30
        factors.append("imc_bajo_peso")
    elif imc < 22:
        score += 0.18
        factors.append("imc_limite_am")

    if pant < 31:
        score += 0.22
        factors.append("circ_pantorrilla_baja")

    # Items MNA-SF 1+2: ingesta / perdida de peso
    if inseg >= 3:
        score += 0.22
        factors.append("inseg_alimentaria_severa")
    elif inseg >= 2:
        score += 0.11
        factors.append("inseg_alimentaria_moderada")

    if record.get("perdio_peso"):
        score += 0.16
        factors.append("perdio_peso")

    # Items MNA-SF 4+5: salud psicologica
    if record.get("depresion"):
        score += 0.12
        factors.append("depresion")

    # Item MNA-SF 3: movilidad
    if movilidad == 0:
        score += 0.14
        factors.append("movilidad_reducida")

    if record.get("limitacion_fisica"):
        score += 0.08
        factors.append("limitacion_fisica")

    # Factores contextuales (RSH/FPS, CASEN 2022)
    if record.get("vive_solo"):
        score += 0.07
        factors.append("vive_solo")

    if edad > 85:
        score += 0.09
        factors.append("edad_avanzada")
    elif edad > 75:
        score += 0.05

    # Comorbilidades (ENS 2017)
    if record.get("diabetes"):
        score += 0.06
        factors.append("diabetes")
    if record.get("hta"):
        score += 0.03

    score = min(1.0, score)

    # Umbrales calibrados por percentiles IPRN (p17=0.22, p50=0.42, p83=0.62)
    if score >= 0.62:
        nivel = "critico"
    elif score >= 0.42:
        nivel = "alto"
    elif score >= 0.22:
        nivel = "medio"
    else:
        nivel = "bajo"

    return nivel, round(score, 3), factors[:5]


def predict(record: dict) -> tuple:
    """
    Predice el nivel de riesgo nutricional para una persona.

    Retorna:
        (nivel_riesgo, probabilidad, factores_principales, todas_probabilidades)
    """
    import pandas as pd

    model, medians = _load_model()

    if model is None:
        nivel, prob, factors = _heuristic_predict(record)
        return nivel, prob, factors, []

    x_arr = build_feature_vector(record, medians)
    x = pd.DataFrame([x_arr], columns=FEATURE_NAMES)

    proba = model.predict_proba(x)[0]
    classes = model.classes_

    pred_class = int(classes[np.argmax(proba)])
    nivel = NIVEL_RIESGO_INV.get(pred_class, "medio")
    prob = float(np.max(proba))

    probs_all = [
        {
            "nivel": NIVEL_RIESGO_INV.get(int(c), str(c)),
            "probabilidad": round(float(p), 4),
        }
        for c, p in zip(classes, proba)
    ]

    try:
        importances = model.feature_importances_
        x_vals = x.values[0]
        contribution = np.abs(importances * x_vals)
        top_idx = np.argsort(contribution)[::-1][:5]
        factors = [FEATURE_NAMES[i] for i in top_idx if contribution[i] > 0.0]
    except Exception:
        factors = ["circ_pantorrilla", "imc", "inseg_alimentaria"]

    return nivel, round(prob, 4), factors, probs_all


def model_info() -> dict:
    """Retorna metadatos del modelo cargado."""
    model, medians = _load_model()

    metrics_path = ARTEFACTOS_DIR / "metrics.json"
    metrics = {}
    if metrics_path.exists():
        with open(metrics_path) as f:
            metrics = json.load(f)

    return {
        "modelo_disponible": model is not None,
        "tipo": type(model).__name__ if model else "HeuristicFallback",
        "n_features": len(FEATURE_NAMES),
        "feature_names": FEATURE_NAMES,
        "metricas": {
            k: metrics.get(k)
            for k in [
                "rf_train_accuracy",
                "cv_f1_macro_mean",
                "cv_f1_macro_std",
                "n_samples",
                "class_distribution",
            ]
        },
    }
