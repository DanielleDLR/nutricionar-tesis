"""
predict.py — Módulo de inferencia del modelo de riesgo nutricional
===================================================================
Carga los artefactos entrenados y expone una función predict() usada
por el router FastAPI. Soporta fallback heurístico si el modelo no está
disponible (útil en CI o entorno sin artefactos).
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np

from ml.features import (
    FEATURE_NAMES,
    NIVEL_RIESGO_INV,
    NIVEL_RIESGO_MAP,
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
            "Modelo ML no encontrado en %s — usando heurística de fallback",
            rf_path
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


def _heuristic_predict(record: dict) -> tuple[str, float, list[str]]:
    """
    Predicción heurística de fallback basada en reglas clínicas MNA.
    Se usa cuando el modelo .pkl no está disponible.
    """
    score = 0.0
    factors = []

    imc = float(record.get("imc") or 24)
    mna = float(record.get("puntaje_mna") or 22)
    inseg = record.get("inseg_alimentaria", 0)
    if isinstance(inseg, str):
        inseg = {"severo": 3, "moderado": 2, "leve": 1}.get(inseg, 0)

    # MNA puntaje (peso 40%)
    if mna < 17:
        score += 0.4
        factors.append("puntaje_mna_bajo")
    elif mna < 24:
        score += 0.2
        factors.append("puntaje_mna_riesgo")

    # IMC (peso 20%)
    if imc < 18.5:
        score += 0.2
        factors.append("imc_bajo_peso")
    elif imc < 22:
        score += 0.1
        factors.append("imc_limite")

    # Inseguridad alimentaria (peso 15%)
    if inseg >= 3:
        score += 0.15
        factors.append("inseg_alimentaria_severa")
    elif inseg >= 2:
        score += 0.07

    # Morbilidades (peso 15%)
    for key, label in [
        ("depresion", "depresion"),
        ("limitacion_fisica", "limitacion_fisica"),
        ("diabetes", "diabetes"),
    ]:
        if record.get(key):
            score += 0.05
            factors.append(label)

    # Vive solo (peso 5%)
    if record.get("vive_solo"):
        score += 0.05
        factors.append("vive_solo")

    score = min(1.0, score)

    if score >= 0.55:
        nivel = "critico"
    elif score >= 0.35:
        nivel = "alto"
    elif score >= 0.15:
        nivel = "medio"
    else:
        nivel = "bajo"

    return nivel, round(score, 3), factors[:5]


def predict(record: dict) -> tuple[str, float, list[str], list[dict]]:
    """
    Predice el nivel de riesgo nutricional para una persona.

    Parámetros:
        record: dict con features (ver ml/features.py para nombres)

    Retorna:
        (nivel_riesgo, probabilidad, factores_principales, todas_probabilidades)
        donde nivel_riesgo ∈ {"bajo","medio","alto","critico"}
        y probabilidad ∈ [0.0, 1.0]
    """
    model, medians = _load_model()

    if model is None:
        nivel, prob, factors = _heuristic_predict(record)
        probs_all = []
        return nivel, prob, factors, probs_all

    # Feature vector — usar DataFrame para conservar nombres de features
    import pandas as pd
    x_arr = build_feature_vector(record, medians)
    x = pd.DataFrame([x_arr], columns=FEATURE_NAMES)

    # Probabilidades por clase
    proba = model.predict_proba(x)[0]
    classes = model.classes_

    # Nivel predicho
    pred_class = int(classes[np.argmax(proba)])
    nivel = NIVEL_RIESGO_INV.get(pred_class, "medio")
    prob = float(np.max(proba))

    # Construir lista de probabilidades por nivel
    probs_all = [
        {"nivel": NIVEL_RIESGO_INV.get(int(c), str(c)), "probabilidad": round(float(p), 4)}
        for c, p in zip(classes, proba)
    ]

    # Factores principales: features con mayor importancia × valor del registro
    try:
        importances = model.feature_importances_
        x_arr = x.values[0]
        contribution = np.abs(importances * x_arr)
        top_idx = np.argsort(contribution)[::-1][:5]
        factors = [FEATURE_NAMES[i] for i in top_idx if contribution[i] > 0.0]
    except Exception:
        factors = ["imc", "puntaje_mna", "inseg_alimentaria"]

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
             