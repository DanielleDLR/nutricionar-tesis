"""
step2_extraer_ens.py — Extracción y filtrado de ENS 2016-2017 (Región del Maule, 60+)
=======================================================================================
Lee el CSV crudo de ENS 2016-2017 (';' como separador), filtra a la Región del
Maule (Region == '7') y a personas de 60 años o más, y construye las variables
clínicas/antropométricas necesarias para el vector IPRN.

Variables construidas:
    id_persona      IdEncuesta + '_' + IdPersona_1
    edad, sexo, zona
    imc              columna derivada IMC
    circ_pantorrilla m4p4_1 (cm) — medido en el submódulo antropométrico F2.
                     CORRECCIÓN vs. Tabla 6 de la tesis: SÍ se mide en el ENS
                     (submuestra; en el segmento 60+ del Maule está disponible
                     para el 100% de los casos, ver hallazgo de verificación).
    diabetes         di3 (diagnóstico médico autorreportado)
    hta              columna derivada HTA
    depresion        sd28_F1 (diagnóstico médico autorreportado)

NOTA: perdio_peso (pérdida de peso reciente, ítem MNA-SF 2) NO se localizó en
el cuestionario ENS F1/F2 — se confirma como variable ausente en fuentes
administrativas reales (coincide con Tabla 6 original de la tesis).

Uso:
    python step2_extraer_ens.py --input /ruta/Base_ENS.csv --out ens_maule_60.csv
"""

import argparse

import numpy as np
import pandas as pd

REGION_MAULE = "7"

MISSING_CODES = {"-9999", "-8888", "-7777", "-99", "-88", "-77", ""}


def _to_float(series):
    s = series.astype(str).str.replace(",", ".").str.strip()
    s = s.where(~s.isin(MISSING_CODES), np.nan)
    return pd.to_numeric(s, errors="coerce")


def cargar_ens_maule_60(input_path: str) -> pd.DataFrame:
    print(f"Leyendo ENS desde: {input_path}")
    usecols = [
        "IdEncuesta", "IdPersona_1", "Region", "Zona", "Edad", "Sexo",
        "IMC", "m4p4_1", "di3", "HTA", "sd28_F1",
    ]
    df = pd.read_csv(
        input_path, sep=";", usecols=lambda c: c in usecols,
        low_memory=False, encoding="utf-8-sig",
    )
    df = df[df["Region"].astype(str).str.strip() == REGION_MAULE].copy()
    df["Edad"] = pd.to_numeric(df["Edad"], errors="coerce")
    df = df[df["Edad"] >= 60].copy()
    print(f"  Región del Maule, 60+: {len(df)} personas")
    return df


def construir_features_ens(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["id_persona_ens"] = df["IdEncuesta"].astype(str) + "_" + df["IdPersona_1"].astype(str)
    out["edad"] = df["Edad"]
    out["sexo"] = df["Sexo"].map({"1": "M", "2": "F", 1: "M", 2: "F"})
    out["zona"] = df["Zona"].map({"1": "urbano", "2": "rural", 1: "urbano", 2: "rural"})

    out["imc"] = _to_float(df["IMC"])
    out["circ_pantorrilla"] = _to_float(df["m4p4_1"])

    diabetes = pd.to_numeric(df["di3"], errors="coerce")
    out["diabetes"] = diabetes.map({1: 1, 2: 0}).astype("float")

    hta = pd.to_numeric(df["HTA"], errors="coerce")
    # HTA es columna derivada 0/1 en la mayoría de las publicaciones ENS
    out["hta"] = hta.where(hta.isin([0, 1]), np.nan)

    depresion = pd.to_numeric(df["sd28_F1"], errors="coerce")
    out["depresion"] = depresion.map({1: 1, 2: 0}).astype("float")

    # perdio_peso: NO disponible en ENS/CASEN -> queda ausente (se imputa después)
    out["perdio_peso"] = np.nan

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", default="ens_maule_60.csv")
    args = ap.parse_args()

    df_raw = cargar_ens_maule_60(args.input)
    df_feat = construir_features_ens(df_raw)
    df_feat.to_csv(args.out, index=False)
    print(f"Guardado: {args.out}  ({len(df_feat)} filas, {df_feat.shape[1]} columnas)")
    print("\nResumen de completitud (no-nulos):")
    print(df_feat.notna().sum())


if __name__ == "__main__":
    main()
