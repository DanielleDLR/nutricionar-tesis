"""
Generador del Dataset Sintético Piloto Maule — NutricioNar
===========================================================
Crea `data/dataset_sintetico_maule.xlsx` con cuatro hojas
(personas_mayores, indicadores_nutric, inseg_alimentaria, acceso_programas)
en el formato que consumen `ml/train.py` y `scripts/load_dataset.py`
(dos filas de preámbulo + fila de encabezado → ``header=2``).

Las variables se muestrean con distribuciones plausibles y la etiqueta
`nivel_riesgo` se deriva de un puntaje clínico tipo MNA con ruido, de modo
que el modelo aprenda una relación señal/ruido realista (no trivial).

Uso:
    python scripts/generar_dataset_sintetico.py
    python scripts/generar_dataset_sintetico.py --n 1200 --seed 42
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# Comunas del Maule (código CUT, nombre) para repartir la población.
COMUNAS = [
    ("07101", "Talca"), ("07401", "Linares"), ("07301", "Curicó"),
    ("07201", "Cauquenes"), ("07406", "Parral"), ("07102", "Constitución"),
    ("07108", "San Clemente"), ("07310", "Molina"),
]


def _nivel_desde_score(score: float) -> str:
    if score >= 0.62:
        return "critico"
    if score >= 0.42:
        return "alto"
    if score >= 0.20:
        return "medio"
    return "bajo"


def generar(n: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)

    ids = [f"P{idx:05d}" for idx in range(1, n + 1)]

    edad = rng.integers(60, 96, n)
    sexo = rng.choice([1, 2], n, p=[0.42, 0.58])           # 1=M, 2=F
    zona = rng.choice([1, 2], n, p=[0.70, 0.30])           # 1=urbano, 2=rural
    comuna_idx = rng.integers(0, len(COMUNAS), n)

    ingreso_pc = rng.normal(260_000, 90_000, n).clip(60_000, 1_200_000)
    num_carencias = rng.integers(0, 6, n)
    hacinamiento = (rng.random(n) < 0.18).astype(int)
    n_integrantes = rng.integers(1, 6, n)
    tipo_nucleo = np.where(rng.random(n) < 0.32, "unipersonal", "nuclear")

    imc = rng.normal(25.5, 4.8, n).clip(15, 40)
    circ_pant = rng.normal(32.5, 3.2, n).clip(23, 43)
    mna = rng.normal(23, 4.0, n).clip(5, 30)
    perdio_peso = (rng.random(n) < 0.22).astype(int)

    diabetes = (rng.random(n) < 0.26).astype(int)
    hta = (rng.random(n) < 0.52).astype(int)
    depresion = (rng.random(n) < 0.20).astype(int)
    lim_fisica = (rng.random(n) < 0.30).astype(int)
    movilidad = rng.choice([0, 1, 2], n, p=[0.10, 0.30, 0.60])

    inseg = rng.choice([0, 1, 2, 3], n, p=[0.55, 0.20, 0.15, 0.10])
    pacam = (rng.random(n) < 0.40).astype(int)
    motivo_no_retiro = rng.choice(
        ["lejania", "movilidad", "desconocimiento", "otro"],
        n, p=[0.32, 0.28, 0.24, 0.16],
    )

    # ── Puntaje clínico → etiqueta nivel_riesgo ──────────────────
    score = np.zeros(n)
    score += np.where(mna < 17, 0.42, np.where(mna < 23.5, 0.22, 0.0))
    score += np.where(imc < 18.5, 0.20, np.where(imc < 22, 0.10, 0.0))
    score += np.where(circ_pant < 31, 0.14, 0.0)
    score += np.where(inseg == 3, 0.18, np.where(inseg == 2, 0.09, 0.0))
    score += perdio_peso * 0.12
    score += depresion * 0.07 + diabetes * 0.05 + lim_fisica * 0.07
    score += (tipo_nucleo == "unipersonal") * 0.06
    score += np.where(edad > 85, 0.08, np.where(edad > 75, 0.04, 0.0))
    score += num_carencias * 0.02
    score += np.where(movilidad == 0, 0.10, 0.0)
    score += rng.normal(0, 0.02, n)        # ruido
    score = score.clip(0, 1)

    nivel_riesgo = np.array([_nivel_desde_score(s) for s in score])
    prob = score.round(3)
    imc_categoria = np.where(
        imc < 18.5, 0, np.where(imc < 25, 1, np.where(imc < 30, 2, 3))
    )

    df_personas = pd.DataFrame({
        "id_persona": ids,
        "region_cod": "07",
        "comuna_cod": [COMUNAS[i][0] for i in comuna_idx],
        "edad": edad,
        "sexo": sexo,
        "zona_urbano_rural": zona,
        "ingreso_per_capita": ingreso_pc.round(0),
        "ingreso_total_hogar": (ingreso_pc * n_integrantes).round(0),
        "num_integrantes_hogar": n_integrantes,
        "num_carencias_total": num_carencias,
        "hacinamiento": hacinamiento,
        "tramo_rsh": rng.choice(["40", "50", "60", "70"], n),
        "tipo_nucleo_familiar": tipo_nucleo,
        "movilidad": movilidad,
        "limitacion_fisica": lim_fisica,
        "perdio_peso_3m": perdio_peso,
        "motivo_no_retiro": motivo_no_retiro,
    })

    df_nutric = pd.DataFrame({
        "id_persona": ids,
        "imc": imc.round(1),
        "imc_categoria": imc_categoria,
        "circ_pantorrilla_cm": circ_pant.round(1),
        "puntaje_mna": mna.round(1),
        "diagnostico_diabetes": diabetes,
        "diagnostico_hta": hta,
        "diagnostico_depresion": depresion,
        "nivel_riesgo": nivel_riesgo,
        "prob_riesgo_desnutricion": prob,
    })

    df_inseg = pd.DataFrame({
        "id_persona": ids,
        "nivel_inseguridad": inseg,
    })

    df_acceso = pd.DataFrame({
        "id_persona": ids,
        "beneficiario_pacam": pacam,
    })

    return {
        "personas_mayores": df_personas,
        "indicadores_nutric": df_nutric,
        "inseg_alimentaria": df_inseg,
        "acceso_programas": df_acceso,
    }, nivel_riesgo


def escribir_excel(hojas: dict, salida: Path):
    """Escribe el Excel con 2 filas de preámbulo (header en la 3.ª fila)."""
    salida.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(salida, engine="openpyxl") as writer:
        for nombre, df in hojas.items():
            # startrow=2 → encabezado en índice 2 (compatible con header=2)
            df.to_excel(writer, sheet_name=nombre, startrow=2, index=False)
            ws = writer.sheets[nombre]
            ws.cell(1, 1, "Dataset sintético piloto Maule — NutricioNar")
            ws.cell(2, 1, f"Hoja: {nombre}")


def main():
    parser = argparse.ArgumentParser(
        description="Genera el dataset sintético piloto del Maule"
    )
    parser.add_argument("--n", type=int, default=1200, help="Nº de personas")
    parser.add_argument("--seed", type=int, default=42, help="Semilla RNG")
    parser.add_argument(
        "--out", default="data/dataset_sintetico_maule.xlsx",
        help="Ruta de salida del Excel"
    )
    args = parser.parse_args()

    hojas, nivel = generar(args.n, args.seed)
    salida = Path(args.out)
    escribir_excel(hojas, salida)

    dist = pd.Series(nivel).value_counts().to_dict()
    print(f"✓ Dataset generado: {salida}  (n={args.n})")
    print(f"  Distribución nivel_riesgo: {dist}")


if __name__ == "__main__":
    main()
