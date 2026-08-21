"""
step1_extraer_casen.py — Extracción y filtrado de CASEN 2022 (Región del Maule, 60+)
=====================================================================================
Lee el CSV crudo de CASEN 2022 (';' como separador), filtra a la Región del Maule
(region == '7') y a personas de 60 años o más, y construye las variables
socioeconómicas necesarias para el vector IPRN.

Variables construidas:
    id_persona        folio + '_' + id_persona (llave única)
    edad, sexo, zona
    ingreso_per_capita (ypc)
    num_carencias      conteo de carencias 4D (Educación, Salud, Trabajo y Seg.
                        Social, Vivienda y Entorno) — 13 indicadores hh_d_*
    hacinamiento        hh_d_hacina
    inseg_alimentaria   escala FIES (r8a-r8h) recodificada a 0-3
    limitacion_fisica   s31_1
    movilidad           derivada de s32c (moverse en casa) y s32g (salir a la calle)
    vive_solo           n_nucleos/tot_per_h == 1 (hogar unipersonal)
    acceso_pacam        s4/s8 no nulos (recibió oferta PACAM)
    pacam_retiro        1 si retiró, 0 si no retiró (para contrastar con INTA 2024)

NOTA IMPORTANTE: esta extracción de CASEN 2022 no incluye la variable `comuna`
(solo `region`). Los resultados son representativos a nivel de Región del Maule,
no a nivel comunal. Si se requiere desagregación comunal, debe gestionarse el
acceso a la variable comuna con el equipo de datos (MDS/INE).

Uso:
    python step1_extraer_casen.py --input /ruta/Base_Casen_2022.csv --out casen_maule_60.csv
"""

import argparse
import csv

import numpy as np
import pandas as pd

REGION_MAULE = "7"

# Indicadores de carencia 4D (excluye la dimensión Redes y Cohesión Social,
# que solo se usa en la versión 5D). 13 indicadores oficiales MDS.
CARENCIAS_4D = [
    "hh_d_asis", "hh_d_rez", "hh_d_esc",          # Educación
    "hh_d_mal", "hh_d_prevs", "hh_d_acc",         # Salud
    "hh_d_act", "hh_d_cot", "hh_d_jub",           # Trabajo y Seguridad Social
    "hh_d_estado", "hh_d_hacina", "hh_d_servbas", "hh_d_entorno",  # Vivienda y Entorno
]

FIES_ITEMS = ["r8a", "r8b", "r8c", "r8d", "r8e", "r8f", "r8g", "r8h"]


def _to_float(series):
    return pd.to_numeric(series.astype(str).str.replace(",", "."), errors="coerce")


def _bin01(series):
    """Convierte 1/2 (Sí/No) o 0/1 a booleano 0/1, tratando negativos como NaN."""
    v = pd.to_numeric(series, errors="coerce")
    v = v.where(v >= 0, np.nan)
    return v.map({1: 1, 2: 0, 0: 0}).astype("float")


def cargar_casen_maule_60(input_path: str) -> pd.DataFrame:
    print(f"Leyendo CASEN desde: {input_path}")
    usecols = [
        "folio", "id_persona", "region", "area", "edad", "sexo",
        "ypc", "n_nucleos", "nucleo", "tot_per_h",
        "s31_1", "s32c", "s32g", "s4", "s8",
    ] + CARENCIAS_4D + FIES_ITEMS

    chunks = []
    reader = pd.read_csv(
        input_path, sep=";", usecols=lambda c: c in usecols,
        chunksize=200_000, low_memory=False, encoding="utf-8-sig",
    )
    for chunk in reader:
        chunk = chunk[chunk["region"].astype(str).str.strip() == REGION_MAULE]
        if len(chunk):
            chunks.append(chunk)
    df = pd.concat(chunks, ignore_index=True)
    df["edad"] = pd.to_numeric(df["edad"], errors="coerce")
    df = df[df["edad"] >= 60].copy()
    print(f"  Región del Maule, 60+: {len(df)} personas")
    return df


def construir_features_casen(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["id_persona_casen"] = df["folio"].astype(str) + "_" + df["id_persona"].astype(str)
    out["edad"] = df["edad"]
    out["sexo"] = df["sexo"].map({1: "M", 2: "F"})
    out["zona"] = df["area"].map({1: "urbano", 2: "rural"})
    out["ingreso_per_capita"] = _to_float(df["ypc"])

    # Carencias 4D: cuenta de dimensiones "carente" (valor 1) entre las 13 oficiales
    carencias_presentes = [c for c in CARENCIAS_4D if c in df.columns]
    car = df[carencias_presentes].apply(pd.to_numeric, errors="coerce")
    out["num_carencias"] = car.clip(lower=0).sum(axis=1, skipna=True)

    out["hacinamiento"] = _bin01(df.get("hh_d_hacina", pd.Series(index=df.index)))

    # FIES: suma de 8 ítems afirmativos (1=Sí, 2=No) -> 0-8 -> recodificado a 0-3
    fies_presentes = [c for c in FIES_ITEMS if c in df.columns]
    fies_bin = df[fies_presentes].apply(_bin01)
    fies_score = fies_bin.sum(axis=1, skipna=True)
    out["fies_score"] = fies_score
    out["inseg_alimentaria"] = pd.cut(
        fies_score, bins=[-1, 0, 2, 5, 8], labels=[0, 1, 2, 3]
    ).astype("float")

    out["limitacion_fisica"] = _bin01(df.get("s31_1", pd.Series(index=df.index)).map(
        {1: 1, 0: 2}  # s31_1 ya es 0/1 (0=No,1=Sí); remapeo a 1/2 para reusar _bin01
    ))
    # s31_1 es 0=No / 1=Sí directamente, mapeo directo es más simple:
    out["limitacion_fisica"] = pd.to_numeric(df.get("s31_1"), errors="coerce").clip(lower=0)

    # Movilidad: combina moverse en casa (s32c) y salir a la calle (s32g)
    # Escala origen 1=Ninguna..5=Extrema/No puede. Mapeo a 0=cama/silla,1=interior,2=sale
    s32g = pd.to_numeric(df.get("s32g"), errors="coerce")
    s32c = pd.to_numeric(df.get("s32c"), errors="coerce")

    def _movilidad(row):
        c, g = row["s32c"], row["s32g"]
        if pd.notna(c) and c >= 4:
            return 0  # dificultad severa/extrema para moverse en casa -> cama/silla
        if pd.notna(g) and g >= 3:
            return 1  # dificultad moderada+ para salir -> solo interior
        return 2  # sale con normalidad
    tmp = pd.DataFrame({"s32c": s32c, "s32g": s32g})
    out["movilidad"] = tmp.apply(_movilidad, axis=1)

    # vive_solo: núcleo unipersonal (heurística: tot_per_h == 1)
    tot = pd.to_numeric(df.get("tot_per_h"), errors="coerce")
    out["vive_solo"] = (tot == 1).astype(float)

    # PACAM: s4 o s8 no nulos => tuvo oferta/contacto con PACAM en el consultorio
    s4 = pd.to_numeric(df.get("s4"), errors="coerce")
    s8 = pd.to_numeric(df.get("s8"), errors="coerce")
    tiene_pacam_dato = s4.notna() | s8.notna()
    out["acceso_pacam"] = tiene_pacam_dato.astype(float)
    # retiró: s4==1 (Sí) o s8 in (1,2) (recibió algún producto); no retiró: código "No retiró"
    retiro = np.where(s4 == 1, 1, np.where(s4 == 2, 0, np.where(s8.isin([1, 2]), 1, np.where(s8 == 3, 0, np.nan))))
    out["pacam_retiro"] = retiro

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", default="casen_maule_60.csv")
    args = ap.parse_args()

    df_raw = cargar_casen_maule_60(args.input)
    df_feat = construir_features_casen(df_raw)
    df_feat.to_csv(args.out, index=False)
    print(f"Guardado: {args.out}  ({len(df_feat)} filas, {df_feat.shape[1]} columnas)")
    print("\nResumen de completitud (no-nulos):")
    print(df_feat.notna().sum())


if __name__ == "__main__":
    main()
