"""
step4_entrenar_y_comparar.py — Entrenamiento sobre datos reales y comparación
================================================================================
1) Construye la matriz X (18 features, mismo orden que ml/features.py) a partir
   del archivo emparejado CASEN-ENS.
2) Ejecuta INFERENCIA con el modelo ya entrenado sobre el dataset sintético
   (modelo_rf.pkl) sobre estos datos reales — chequeo de validez de fachada,
   no requiere las etiquetas reales.
3) REENTRENA un RandomForest nuevo sobre los datos reales (con las etiquetas
   IPRN-proxy derivadas en el paso 3) y evalúa con validación cruzada
   estratificada, igual que en ml/train.py — guardando artefactos separados
   en ml/artefactos_real/ para no sobrescribir el modelo original (sintético).

IMPORTANTE — lo que esto SÍ y NO demuestra:
  SÍ demuestra que el pipeline puede recibir, transformar y predecir sobre
  datos reales de personas del Maule (los objetivos de esta tarea).
  NO constituye validación externa con desenlace clínico independiente,
  porque nivel_riesgo sigue derivándose de una fórmula (IPRN) aplicada sobre
  variables proxy, no de una evaluación MNA real en terreno.

Uso:
    python step4_entrenar_y_comparar.py --input real_maule_60_matched.csv
"""

import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier

REPO_ROOT = Path(__file__).resolve().parents[2]  # backend/
sys.path.insert(0, str(REPO_ROOT))

from ml.features import FEATURE_NAMES, NIVEL_RIESGO_MAP, build_feature_vector  # noqa: E402

ARTEFACTOS_SINTETICO = REPO_ROOT / "ml" / "artefactos"
ARTEFACTOS_REAL = REPO_ROOT / "ml" / "artefactos_real"


def construir_matriz(df: pd.DataFrame):
    rows = []
    for _, r in df.iterrows():
        record = {
            "edad": r.get("edad"),
            "sexo": r.get("sexo"),
            "zona": r.get("zona"),
            "ingreso_per_capita": r.get("ingreso_per_capita"),
            "num_carencias": r.get("num_carencias"),
            "hacinamiento": bool(r.get("hacinamiento", False)),
            "imc": r.get("imc"),
            "circ_pantorrilla": r.get("circ_pantorrilla"),
            "puntaje_mna": r.get("puntaje_mna_proxy"),
            "perdio_peso": bool(r.get("perdio_peso", False)),
            "diabetes": bool(r.get("diabetes", False)),
            "hta": bool(r.get("hta", False)),
            "depresion": bool(r.get("depresion", False)),
            "limitacion_fisica": bool(r.get("limitacion_fisica", False)),
            "inseg_alimentaria": r.get("inseg_alimentaria", 0),
            "acceso_pacam": bool(r.get("acceso_pacam", False)),
            "movilidad": r.get("movilidad", 1),
            "vive_solo": bool(r.get("vive_solo", False)),
        }
        rows.append(build_feature_vector(record))
    X = pd.DataFrame(rows, columns=FEATURE_NAMES)
    y = df["nivel_riesgo"].map(NIVEL_RIESGO_MAP).astype(int)
    return X, y


def inferencia_modelo_sintetico(X: pd.DataFrame) -> pd.Series:
    modelo_path = ARTEFACTOS_SINTETICO / "modelo_rf.pkl"
    if not modelo_path.exists():
        print(f"  [aviso] No se encontró {modelo_path}; se omite la comparación de inferencia.")
        return None
    with open(modelo_path, "rb") as f:
        modelo = pickle.load(f)
    pred = modelo.predict(X)
    inv = {0: "bajo", 1: "medio", 2: "alto", 3: "critico"}
    return pd.Series([inv[p] for p in pred])


def reentrenar_sobre_datos_reales(X: pd.DataFrame, y: pd.Series, k_folds: int = 3):
    print(f"\nEntrenando sobre datos reales (N={len(X)}, k={k_folds})...")

    dt = DecisionTreeClassifier(max_depth=8, min_samples_leaf=5, class_weight="balanced", random_state=42)
    dt.fit(X, y)
    dt_acc = dt.score(X, y)

    rf = RandomForestClassifier(
        n_estimators=150, max_depth=10, class_weight="balanced", random_state=42
    )
    rf.fit(X, y)
    rf_acc = rf.score(X, y)

    skf = StratifiedKFold(n_splits=k_folds, shuffle=True, random_state=42)
    cv_scores = cross_val_score(rf, X, y, cv=skf, scoring="f1_macro")

    from sklearn.model_selection import cross_val_predict
    y_pred_cv = cross_val_predict(rf, X, y, cv=skf)
    cm = confusion_matrix(y, y_pred_cv)
    report = classification_report(
        y, y_pred_cv, target_names=["bajo", "medio", "alto", "critico"], output_dict=True, zero_division=0
    )

    print(f"  DT train accuracy: {dt_acc:.4f}")
    print(f"  RF train accuracy: {rf_acc:.4f}")
    print(f"  RF F1-macro CV ({k_folds}-fold): {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print("\n  Matriz de confusión (CV, out-of-fold):")
    print(cm)
    print("\n  Reporte por clase:")
    for cls in ["bajo", "medio", "alto", "critico"]:
        r = report[cls]
        print(f"    {cls:8s} precision={r['precision']:.3f} recall={r['recall']:.3f} f1={r['f1-score']:.3f} support={int(r['support'])}")

    ARTEFACTOS_REAL.mkdir(parents=True, exist_ok=True)
    with open(ARTEFACTOS_REAL / "modelo_rf_real.pkl", "wb") as f:
        pickle.dump(rf, f)
    metrics = {
        "cv_f1_macro_mean": float(cv_scores.mean()),
        "cv_f1_macro_std": float(cv_scores.std()),
        "dt_train_accuracy": float(dt_acc),
        "rf_train_accuracy": float(rf_acc),
        "n_samples": int(len(X)),
        "k_folds": k_folds,
        "class_distribution": y.value_counts().to_dict(),
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
        "fuente": "CASEN 2022 + ENS 2016-2017, emparejamiento estadistico, Region del Maule 60+, etiquetas IPRN-proxy",
    }
    with open(ARTEFACTOS_REAL / "metrics_real.json", "w") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"\n  Artefactos guardados en {ARTEFACTOS_REAL}")
    return rf, metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--k-folds", type=int, default=3)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    X, y = construir_matriz(df)
    print(f"Matriz construida: X={X.shape}, distribución y=\n{y.value_counts()}")

    print("\n--- Paso A: inferencia con el modelo entrenado en datos sintéticos ---")
    pred_sintetico = inferencia_modelo_sintetico(X)
    if pred_sintetico is not None:
        real_labels = df["nivel_riesgo"].reset_index(drop=True)
        print("Distribución real (IPRN-proxy):")
        print(real_labels.value_counts(normalize=True).round(3))
        print("\nDistribución predicha por el modelo sintético sobre estos mismos datos:")
        print(pred_sintetico.value_counts(normalize=True).round(3))
        coincidencia = (pred_sintetico.values == real_labels.values).mean()
        print(f"\nCoincidencia exacta modelo-sintético vs etiqueta-proxy-real: {coincidencia:.3f}")

    print("\n--- Paso B: reentrenamiento sobre datos reales (etiquetas IPRN-proxy) ---")
    reentrenar_sobre_datos_reales(X, y, k_folds=args.k_folds)


if __name__ == "__main__":
    main()
