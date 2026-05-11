"""
train.py — Entrenamiento del modelo de riesgo nutricional
==========================================================
Entrena un DecisionTreeClassifier y un RandomForestClassifier sobre el
dataset sintético Maule y guarda los artefactos en ml/artefactos/.

Uso:
    python -m ml.train --file data/dataset_sintetico_maule.xlsx
    python -m ml.train --file data/dataset_sintetico_maule.xlsx --eval
"""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier

from ml.features import (
    FEATURE_NAMES,
    MEDIANS,
    NIVEL_RIESGO_INV,
    build_training_matrix,
)

ARTEFACTOS_DIR = Path(__file__).parent / "artefactos"

try:
    import pickle
    _PICKLE = True
except ImportError:
    _PICKLE = False


def save_artefact(obj, name: str):
    """Guarda un objeto con pickle."""
    import pickle as pk
    ARTEFACTOS_DIR.mkdir(parents=True, exist_ok=True)
    path = ARTEFACTOS_DIR / name
    with open(path, "wb") as f:
        pk.dump(obj, f)
    print(f"  Guardado: {path}")


def cargar_dataset(excel_path: str):
    xl = pd.ExcelFile(excel_path)
    df_p = xl.parse("personas_mayores",   header=2).dropna(how="all")
    df_n = xl.parse("indicadores_nutric", header=2).dropna(how="all")
    df_i = xl.parse("inseg_alimentaria",  header=2).dropna(how="all")
    df_a = xl.parse("acceso_programas",   header=2).dropna(how="all")
    for df in [df_p, df_n, df_i, df_a]:
        df.columns = [str(c).strip() for c in df.columns]
    return df_p, df_n, df_i, df_a


def entrenar(excel_path: str, evaluar: bool = True) -> dict:
    print(f"\nLeyendo dataset: {excel_path}")
    df_p, df_n, df_i, df_a = cargar_dataset(excel_path)

    print("Construyendo matriz de features...")
    X, y = build_training_matrix(df_p, df_n, df_i, df_a)
    print(f"  → X: {X.shape}, y: {y.value_counts().to_dict()}")

    # ── Árbol de decisión ────────────────────────────────────────
    print("\nEntrenando DecisionTree...")
    dt = DecisionTreeClassifier(
        max_depth=8,
        min_samples_leaf=10,
        class_weight="balanced",
        random_state=42,
    )
    dt.fit(X, y)
    dt_acc = dt.score(X, y)
    print(f"  Train accuracy: {dt_acc:.3f}")

    # ── Random Forest (modelo principal) ─────────────────────────
    print("\nEntrenando RandomForest...")
    rf = RandomForestClassifier(
        n_estimators=150,
        max_depth=10,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X, y)
    rf_acc = rf.score(X, y)
    print(f"  Train accuracy: {rf_acc:.3f}")

    # ── Validación cruzada ───────────────────────────────────────
    metrics = {}
    if evaluar:
        print("\nValidación cruzada (5-fold, RandomForest)...")
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        scores = cross_val_score(rf, X, y, cv=cv, scoring="f1_macro")
        metrics["cv_f1_macro_mean"] = round(float(scores.mean()), 4)
        metrics["cv_f1_macro_std"]  = round(float(scores.std()), 4)
        print(
            f"  F1-macro: {scores.mean():.3f} ± {scores.std():.3f}"
        )

        y_pred = rf.predict(X)
        labels = sorted(y.unique())
        label_names = [NIVEL_RIESGO_INV[l] for l in labels]
        print("\nClassification report (train set):")
        print(classification_report(
            y, y_pred, labels=labels, target_names=label_names
        ))
        metrics["confusion_matrix"] = confusion_matrix(
            y, y_pred, labels=labels
        ).tolist()
        metrics["label_names"] = label_names

    # ── Importancia de features ──────────────────────────────────
    fi = pd.Series(rf.feature_importances_, index=FEATURE_NAMES)
    fi_top = fi.nlargest(10)
    print("\nTop 10 features (RandomForest):")
    for feat, imp in fi_top.items():
        print(f"  {feat:25s}: {imp:.4f}")

    metrics["feature_importances"] = fi.to_dict()
    metrics["dt_train_accuracy"] = round(dt_acc, 4)
    metrics["rf_train_accuracy"] = round(rf_acc, 4)
    metrics["n_samples"] = int(len(X))
    metrics["class_distribution"] = {
        NIVEL_RIESGO_INV[k]: int(v) for k, v in y.value_counts().to_dict().items()
    }
    metrics["medians"] = MEDIANS

    # ── Guardar artefactos ───────────────────────────────────────
    print("\nGuardando artefactos...")
    save_artefact(rf, "modelo_rf.pkl")
    save_artefact(dt, "modelo_dt.pkl")
    save_artefact(MEDIANS, "medians.pkl")
    save_artefact(FEATURE_NAMES, "feature_names.pkl")

    metrics_path = ARTEFACTOS_DIR / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"  Guardado: {metrics_path}")

    print("\n✓ Entrenamiento completado.")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Entrena modelo de riesgo nutricional"
    )
    parser.add_argument("--file", required=True, help="Ruta al Excel del dataset")
    parser.add_argument(
        "--eval", action="store_true", help="Realizar validación cruzada"
    )
    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"Error: archivo no encontrado: {args.file}")
        sys.exit(1)

    entrenar(args.file, evaluar=args.eval)
