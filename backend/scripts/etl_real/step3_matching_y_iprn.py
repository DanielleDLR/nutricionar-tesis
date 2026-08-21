"""
step3_matching_y_iprn.py — Emparejamiento estadístico CASEN↔ENS y construcción
=================================================================================
del vector IPRN sobre datos reales (Región del Maule, 60+).

CASEN y ENS son encuestas independientes (no comparten id_persona), tal como
anticipa el Anexo A de la tesis (A.3 — "Emparejamiento estadístico (statistical
matching) entre ENS y CASEN por edad, sexo y región, dado que no comparten
identificador de persona"). Aquí se implementa ese emparejamiento:

    Para cada persona de ENS (N=293, aporta variables clínicas/antropométricas)
    se busca la persona de CASEN (N=3.352, aporta variables socioeconómicas)
    más cercana en edad, con sexo y zona idénticos, sin reemplazo.

Luego se construye un proxy del puntaje MNA a partir de variables disponibles
en fuentes reales (IMC, circunferencia de pantorrilla, comorbilidades,
inseguridad alimentaria, movilidad) — NO es el instrumento clínico MNA-SF
real, que requiere evaluación en terreno. Esta es una limitación metodológica
que debe declararse con la misma transparencia que la tesis ya aplica al
dataset sintético (ver sección 8.1).

Finalmente se aplica la misma fórmula de score usada en
`generar_dataset_sintetico.py` (con puntaje_mna reemplazado por el proxy) para
derivar `nivel_riesgo`, y se emite el archivo listo para ml/train.py.

Uso:
    python step3_matching_y_iprn.py \
        --casen casen_maule_60.csv --ens ens_maule_60.csv \
        --out real_maule_60_matched.csv
"""

import argparse

import numpy as np
import pandas as pd


def emparejar(df_ens: pd.DataFrame, df_casen: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    casen_disponible = df_casen.copy()
    casen_disponible["_usado"] = False

    filas = []
    ens_shuffled = df_ens.sample(frac=1, random_state=seed).reset_index(drop=True)

    for _, ens_row in ens_shuffled.iterrows():
        pool = casen_disponible[
            (~casen_disponible["_usado"])
            & (casen_disponible["sexo"] == ens_row["sexo"])
            & (casen_disponible["zona"] == ens_row["zona"])
        ]
        if pool.empty:
            # Relaja la restricción de zona si no hay candidatos
            pool = casen_disponible[
                (~casen_disponible["_usado"]) & (casen_disponible["sexo"] == ens_row["sexo"])
            ]
        if pool.empty:
            continue

        dist = (pool["edad"] - ens_row["edad"]).abs()
        idx_match = dist.idxmin()
        match = casen_disponible.loc[idx_match]
        casen_disponible.loc[idx_match, "_usado"] = True

        fila = {**ens_row.to_dict(), **{
            k: v for k, v in match.to_dict().items()
            if k not in ("edad", "sexo", "zona", "_usado")
        }}
        fila["edad_casen"] = match["edad"]
        fila["diff_edad_matching"] = abs(match["edad"] - ens_row["edad"])
        filas.append(fila)

    return pd.DataFrame(filas)


def construir_proxy_mna(df: pd.DataFrame) -> pd.Series:
    """
    Proxy del puntaje MNA (escala aproximada 0-30, mayor = mejor estado).
    Basado en los componentes disponibles en fuentes administrativas reales:
    IMC, circunferencia de pantorrilla, comorbilidades (diabetes/HTA/depresión),
    movilidad e inseguridad alimentaria. NO reemplaza la evaluación clínica MNA-SF.
    """
    score = pd.Series(30.0, index=df.index)  # parte del máximo, descuenta por factor de riesgo

    imc = df["imc"]
    score -= np.select(
        [imc < 19, (imc >= 19) & (imc < 21), (imc >= 21) & (imc < 23)],
        [6, 3, 1], default=0,
    )

    cp = df["circ_pantorrilla"]
    score -= np.where(cp < 31, 4, 0)

    score -= df["diabetes"].fillna(0) * 1.0
    score -= df["hta"].fillna(0) * 0.5
    score -= df["depresion"].fillna(0) * 3.0

    score -= (df["movilidad"] == 0).astype(float) * 4
    score -= (df["movilidad"] == 1).astype(float) * 2

    score -= df["inseg_alimentaria"].fillna(0) * 1.5

    return score.clip(lower=0, upper=30)


def _nivel_desde_score(score: float) -> str:
    if score >= 0.62:
        return "critico"
    if score >= 0.42:
        return "alto"
    if score >= 0.20:
        return "medio"
    return "bajo"


def construir_iprn(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["puntaje_mna_proxy"] = construir_proxy_mna(df)

    mna = df["puntaje_mna_proxy"]
    imc = df["imc"]
    cp = df["circ_pantorrilla"]
    inseg = df["inseg_alimentaria"].fillna(0)
    depresion = df["depresion"].fillna(0)
    diabetes = df["diabetes"].fillna(0)
    lim_fisica = df["limitacion_fisica"].fillna(0)
    vive_solo = df["vive_solo"].fillna(0)
    edad = df["edad"]
    num_carencias = df["num_carencias"].fillna(0)
    movilidad = df["movilidad"]
    perdio_peso = df["perdio_peso"].fillna(0)  # no disponible -> 0 por defecto (ver limitación)

    score = np.zeros(len(df))
    score += np.where(mna < 17, 0.42, np.where(mna < 23.5, 0.22, 0.0))
    score += np.where(imc < 18.5, 0.20, np.where(imc < 22, 0.10, 0.0))
    score += np.where(cp < 31, 0.14, 0.0)
    score += np.where(inseg == 3, 0.18, np.where(inseg == 2, 0.09, 0.0))
    score += perdio_peso * 0.12
    score += depresion * 0.07 + diabetes * 0.05 + lim_fisica * 0.07
    score += vive_solo * 0.06
    score += np.where(edad > 85, 0.08, np.where(edad > 75, 0.04, 0.0))
    score += num_carencias * 0.02
    score += np.where(movilidad == 0, 0.10, 0.0)
    score = np.clip(score, 0, 1)

    df["iprn_score"] = score
    df["nivel_riesgo"] = [_nivel_desde_score(s) for s in score]
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--casen", required=True)
    ap.add_argument("--ens", required=True)
    ap.add_argument("--out", default="real_maule_60_matched.csv")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    df_casen = pd.read_csv(args.casen)
    df_ens = pd.read_csv(args.ens)

    print(f"CASEN Maule 60+: {len(df_casen)} | ENS Maule 60+: {len(df_ens)}")

    matched = emparejar(df_ens, df_casen, seed=args.seed)
    print(f"Emparejados: {len(matched)} (limitado por N de ENS)")
    print(f"Diferencia de edad promedio en el matching: {matched['diff_edad_matching'].mean():.2f} años")

    final = construir_iprn(matched)
    final.to_csv(args.out, index=False)
    print(f"\nGuardado: {args.out}")
    print("\nDistribución nivel_riesgo:")
    print(final["nivel_riesgo"].value_counts(normalize=True).round(3))


if __name__ == "__main__":
    main()
