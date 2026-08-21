"""
Generador del Dataset Sintético Piloto Maule — NutricioNar
===========================================================
Crea `data/dataset_sintetico_maule.xlsx` con cuatro hojas
(personas_mayores, indicadores_nutric, inseg_alimentaria, acceso_programas)
en el formato que consumen `ml/train.py` y `scripts/load_dataset.py`
(dos filas de preámbulo + fila de encabezado → ``header=2``).

Variable objetivo: Índice Proxy de Riesgo Nutricional (IPRN)
-------------------------------------------------------------
La variable `nivel_riesgo` se construye mediante un Índice Proxy de Riesgo
Nutricional (IPRN) basado en los ítems del MNA-SF (Mini Nutritional Assessment
Short Form) que pueden aproximarse con datos administrativos y de encuesta
disponibles en Chile (ENS 2017, CASEN 2022, RSH/FPS).

Este enfoque está respaldado por la literatura epidemiológica que valida el
uso de proxies de tamizaje nutricional en estudios poblacionales donde la
aplicación del instrumento clínico completo no es factible (Kaiser et al., 2010;
Salvá et al., 2009; ESPEN Guidelines, Kondrup et al., 2003).

Correspondencia IPRN ↔ ítems MNA-SF:
    MNA-SF ítem 1 (disminución ingesta)   → inseg_alimentaria (FIES/CASEN) + perdio_peso
    MNA-SF ítem 2 (pérdida de peso)       → perdio_peso_3m (ENS 2017)
    MNA-SF ítem 3 (movilidad)             → movilidad + limitacion_fisica (ENS 2017)
    MNA-SF ítem 4 (estrés psicológico)    → depresion + comorbilidades (ENS 2017)
    MNA-SF ítem 5 (problemas neuropsic.)  → depresion (ENS 2017)
    MNA-SF ítem 6 (IMC / circ. pantorr.)  → imc + circ_pantorrilla (ENS 2017)

Nota metodológica: el puntaje MNA clínico (0–30) SÍ se simula aquí (dataset
sintético = "mundo con evaluación clínica completa"), pero en las fuentes de
datos reales del proyecto (ENS 2017, CASEN 2022) no existe: build_feature_vector()
lo aproxima mediante un proxy en ese caso (ver ml/features.py).

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
    ("07108", "San Clemente"), ("07304", "Molina"),
]


def _nivel_desde_iprn(iprn: float) -> str:
    """
    Clasifica el nivel de riesgo nutricional a partir del IPRN (0–1).

    Umbrales calibrados para replicar la distribución observada en estudios
    chilenos de adultos mayores (ESSALCAVI 2024, ENS 2017):
        crítico : ~17% (IPRN >= 0.62)
        alto    : ~32–36 %
        medio   : ~30–35 %
        bajo    : ~14–18 %
    """
    if iprn >= 0.62:
        return "critico"
    if iprn >= 0.42:
        return "alto"
    if iprn >= 0.22:
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

    # ── Puntaje MNA clínico simulado (0-30) ──────────────────────────────────
    # Correlacionado con los mismos factores de riesgo (mundo con evaluación
    # clínica completa). En datos reales este puntaje no existe y se aproxima
    # con un proxy — ver ml/features.py::_proxy_puntaje_mna().
    puntaje_mna = np.full(n, 30.0)
    puntaje_mna -= np.where(imc < 19, 6, np.where(imc < 21, 3, np.where(imc < 23, 1, 0)))
    puntaje_mna -= np.where(circ_pant < 31, 4, 0)
    puntaje_mna -= diabetes * 1.0
    puntaje_mna -= hta * 0.5
    puntaje_mna -= depresion * 3.0
    puntaje_mna -= np.where(movilidad == 0, 4, np.where(movilidad == 1, 2, 0))
    puntaje_mna -= inseg * 1.5
    puntaje_mna -= perdio_peso * 2.5
    puntaje_mna += rng.normal(0, 1.2, n)
    puntaje_mna = puntaje_mna.clip(0, 30)

    # ── Índice Proxy de Riesgo Nutricional (IPRN) → etiqueta nivel_riesgo ───
    #
    # El IPRN aproxima los 6 ítems del MNA-SF usando variables disponibles
    # en fuentes chilenas (ENS 2017, CASEN 2022, RSH/FPS), con el puntaje MNA
    # simulado como componente dominante (mundo con evaluación clínica).
    # Pesos calibrados con referencia a ESSALCAVI 2024 y ENS 2017.
    #
    # Puntaje MNA simulado (0-30): componente dominante, coherente con su
    # rol como instrumento de referencia clínica. Peso moderado para evitar
    # doble conteo, ya que el propio puntaje_mna correlaciona con imc/
    # circ_pant/comorbilidades/movilidad/inseg (ver más arriba).
    iprn = np.where(puntaje_mna < 17, 0.30, np.where(puntaje_mna < 23.5, 0.14, 0.0))

    # Ítem MNA-SF 6: IMC / circunferencia de pantorrilla
    #   - IMC < 18.5 → bajo peso severo; 18.5–22 → bajo peso leve
    #     (umbral 22 validado para adultos mayores, vs 25 en adultos; Abellan 2010)
    iprn += np.where(imc < 18.5, 0.12, np.where(imc < 22, 0.06, 0.0))
    #   - Circunferencia pantorrilla < 31 cm: sarcopenia proxy (Guigoz 2006)
    iprn += np.where(circ_pant < 31, 0.08, 0.0)

    # Ítem MNA-SF 1+2: disminución ingesta / pérdida de peso
    #   - Inseguridad alimentaria FIES severa/moderada (CASEN 2022)
    iprn += np.where(inseg == 3, 0.22, np.where(inseg == 2, 0.11, 0.0))
    #   - Pérdida de peso autoreportada en 3 meses (ENS 2017)
    iprn += perdio_peso * 0.16

    # Ítem MNA-SF 4+5: estrés psicológico / problemas neuropsicológicos
    iprn += depresion * 0.12

    # Ítem MNA-SF 3: movilidad
    iprn += np.where(movilidad == 0, 0.14, 0.0)   # confinado a cama/silla
    iprn += lim_fisica * 0.08

    # Factores contextuales chilenos (RSH/FPS, CASEN 2022)
    iprn += (tipo_nucleo == "unipersonal") * 0.07  # aislamiento social
    iprn += np.where(edad > 85, 0.09, np.where(edad > 75, 0.05, 0.0))
    iprn += num_carencias * 0.025
    iprn += hacinamiento * 0.04

    # Comorbilidades (ENS 2017)
    iprn += diabetes * 0.06 + hta * 0.03

    # Ruido aleatorio (simula variabilidad no capturada)
    iprn += rng.normal(0, 0.025, n)
    iprn = iprn.clip(0, 1)

    nivel_riesgo = np.array([_nivel_desde_iprn(s) for s in iprn])
    prob = iprn.round(3)
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
        "puntaje_mna": puntaje_mna.round(1),
        "diagnostico_diabetes": diabetes,
        "diagnostico_hta": hta,
        "diagnostico_depresion": depresion,
        "nivel_riesgo": nivel_riesgo,
        "prob_riesgo_desnutricion": prob,  # = valor IPRN normalizado
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
    """Escribe el Excel con 2 filas de preambulo (header en la 3.a fila)."""
    salida.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(salida, engine="openpyxl") as writer:
        for nombre, df in hojas.items():
            df.to_excel(writer, sheet_name=nombre, startrow=2, index=False)
            ws = writer.sheets[nombre]
            ws.cell(1, 1, "Dataset sintetico piloto Maule - NutricioNar")
            ws.cell(2, 1, f"Hoja: {nombre}")


def main():
    parser = argparse.ArgumentParser(
        description="Genera el dataset sintetico piloto del Maule"
    )
    parser.add_argument("--n", type=int, default=1200, help="N de personas")
    parser.add_argument("--seed", type=int, default=42, help="Semilla RNG")
    parser.add_argument(
        "--out", default="data/dataset_sintetico_maule.xlsx",
        help="Ruta de salida del Excel"
    )
    args = parser.parse_args()

    hojas, nivel = generar(args.n, args.seed)
    salida = Path(args.out)
    escribir_excel(hojas, salida)

    dist = dict(zip(*zip(*sorted(
        {k: int(v) for k, v in zip(*[iter([
            item for pair in zip(
                [str(x) for x in nivel],
                [1]*len(nivel)
            ) for item in pair
        ])]*2)}.items()
    ))))
    import pandas as pd_
    dist = pd_.Series(nivel).value_counts().to_dict()
    print(f"Dataset generado: {salida}  (n={args.n})")
    print(f"  Distribucion nivel_riesgo: {dist}")


if __name__ == "__main__":
    main()
