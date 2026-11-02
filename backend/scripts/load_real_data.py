"""
Script ETL — Carga del Dataset Real del Maule (CASEN 2022 + ENS 2016-2017)
============================================================================
Lee backend/data_real/real_maule_poblacion_con_prediccion.csv (generado por
backend/scripts/etl_real/, ver sección 7.5 de la memoria) y lo carga en las
mismas tablas que usa el dataset sintético (hogares, personas,
indicadores_nutricionales), etiquetado con fuente='CASEN_ENS_REAL' para que
pueda filtrarse por separado en el dashboard.

Limitación declarada — asignación de comuna:
    La extracción de CASEN 2022 disponible no incluye la variable comuna
    (solo región). Cada persona real se asigna a una comuna del Maule por
    muestreo aleatorio PONDERADO por la población real de 60+ años de esa
    comuna (Censo 2017, ver app/data_ref/pesos_comuna_maule.py) — no es un
    dato observado, es una estimación reproducible (seed fija) para poblar
    el mapa de forma representativa a nivel agregado. No debe leerse como
    la comuna real de una persona específica.

Uso:
    python scripts/load_real_data.py --file data_real/real_maule_poblacion_con_prediccion.csv
    python scripts/load_real_data.py --file data_real/real_maule_poblacion_con_prediccion.csv --reset
"""

import argparse
import os
import random
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.data_ref.pesos_comuna_maule import PESOS_COMUNA_MAULE_60PLUS  # noqa: E402

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/nutricionar",
)
FUENTE = "CASEN_ENS_REAL"
ANIO = 2022
SEED = 42

NIVEL_RIESGO_VALIDOS = {"bajo", "medio", "alto", "critico"}


def _asignar_comuna(n: int, seed: int = SEED) -> list[str]:
    """Asigna comuna a `n` personas por muestreo ponderado por población
    real de 60+ (censo), reproducible. Ver limitación en el docstring."""
    rng = random.Random(seed)
    comunas = list(PESOS_COMUNA_MAULE_60PLUS.keys())
    pesos = list(PESOS_COMUNA_MAULE_60PLUS.values())
    return rng.choices(comunas, weights=pesos, k=n)


def limpiar_zona(valor) -> str:
    v = str(valor).strip().lower()
    return "rural" if v == "rural" else "urbano"


def limpiar_sexo(valor) -> str:
    v = str(valor).strip().upper()
    return "F" if v in ("F", "MUJER") else "M"


def limpiar_inseguridad(valor) -> str | None:
    mapping = {0: "seguro", 1: "leve", 2: "moderado", 3: "severo"}
    try:
        return mapping.get(int(float(valor)))
    except (TypeError, ValueError):
        return None


def cargar_datos(df: pd.DataFrame, session) -> dict:
    stats = {"hogares": 0, "personas": 0, "indicadores": 0, "omitidos": 0}

    comunas_asignadas = _asignar_comuna(len(df))

    for idx, row in df.reset_index(drop=True).iterrows():
        nivel = str(row.get("prediccion_modelo_real", "")).strip().lower()
        if nivel not in NIVEL_RIESGO_VALIDOS:
            stats["omitidos"] += 1
            continue

        comuna_cod = comunas_asignadas[idx]

        # ── hogar ──────────────────────────────────────────────
        ingreso_pc = row.get("ingreso_per_capita")
        result = session.execute(text("""
            INSERT INTO hogares
                (region, comuna, zona, ingreso_total, quintil_ingreso,
                 n_integrantes, hacinamiento, acceso_pacam, acceso_rsh)
            VALUES
                (:region, :comuna, :zona, :ingreso, NULL,
                 NULL, :hacinamiento, :acceso_pacam, :acceso_rsh)
            RETURNING id
        """), {
            "region": "07",
            "comuna": comuna_cod,
            "zona": limpiar_zona(row.get("zona")),
            "ingreso": float(ingreso_pc) if pd.notna(ingreso_pc) else None,
            "hacinamiento": bool(row.get("hacinamiento", False)),
            "acceso_pacam": bool(row.get("acceso_pacam", False)),
            "acceso_rsh": True,  # CASEN es la fuente del RSH/pobreza multidim.
        })
        hogar_id = result.fetchone()[0]
        stats["hogares"] += 1

        # ── persona ────────────────────────────────────────────
        result = session.execute(text("""
            INSERT INTO personas
                (hogar_id, edad, sexo, vive_solo, peso_kg, talla_cm, imc,
                 circunferencia_pantorrilla, tiene_diabetes, tiene_hipertension,
                 tiene_depresion, nivel_inseguridad, motivo_no_retiro,
                 fuente, anio_encuesta)
            VALUES
                (:hogar_id, :edad, :sexo, :vive_solo, NULL, NULL, :imc,
                 :pantorrilla, :diabetes, :hta,
                 :depresion, :inseg, :motivo, :fuente, :anio)
            RETURNING id
        """), {
            "hogar_id": hogar_id,
            "edad": int(row["edad"]) if pd.notna(row.get("edad")) else 65,
            "sexo": limpiar_sexo(row.get("sexo")),
            "vive_solo": bool(row.get("vive_solo", False)),
            "imc": float(row["imc"]) if pd.notna(row.get("imc")) else None,
            "pantorrilla": float(row["circ_pantorrilla"])
            if pd.notna(row.get("circ_pantorrilla")) else None,
            "diabetes": bool(row.get("diabetes", False)),
            "hta": bool(row.get("hta", False)),
            "depresion": bool(row.get("depresion", False)),
            "inseg": limpiar_inseguridad(row.get("inseg_alimentaria")),
            "motivo": None,  # no disponible en CASEN para no-beneficiarios
            "fuente": FUENTE,
            "anio": ANIO,
        })
        persona_id = result.fetchone()[0]
        stats["personas"] += 1

        # ── indicador ──────────────────────────────────────────
        prob_col = f"prob_{nivel}"
        prob = float(row[prob_col]) if prob_col in row and pd.notna(row[prob_col]) else None

        imc_val = row.get("imc")
        estado_nut = None
        if pd.notna(imc_val):
            imc_val = float(imc_val)
            estado_nut = (
                "bajo peso" if imc_val < 18.5 else
                "normal" if imc_val < 25 else
                "sobrepeso" if imc_val < 30 else "obesidad"
            )

        session.execute(text("""
            INSERT INTO indicadores_nutricionales
                (persona_id, nivel_riesgo, probabilidad_riesgo,
                 estado_nutricional, modelo_version)
            VALUES
                (:persona_id, :nivel, :prob, :estado, :version)
        """), {
            "persona_id": persona_id,
            "nivel": nivel,
            "prob": prob,
            "estado": estado_nut,
            "version": "v0.1-real-maule-preliminar",
        })
        stats["indicadores"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Carga el dataset real del Maule (CASEN+ENS) en PostgreSQL"
    )
    parser.add_argument(
        "--file", required=True,
        help="Ruta a real_maule_poblacion_con_prediccion.csv"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Elimina registros previos de fuente=CASEN_ENS_REAL antes de cargar"
    )
    args = parser.parse_args()

    print(f"Conectando a BD: {DATABASE_URL[:50]}...")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    if args.reset:
        print("Eliminando registros previos de fuente=CASEN_ENS_REAL...")
        session.execute(text("""
            DELETE FROM hogares WHERE id IN (
                SELECT DISTINCT h.id FROM hogares h
                JOIN personas p ON p.hogar_id = h.id
                WHERE p.fuente = :fuente
            )
        """), {"fuente": FUENTE})
        session.commit()

    print(f"Leyendo {args.file}...")
    df = pd.read_csv(args.file)
    print(f"  {len(df)} personas en el archivo")

    print("Cargando en PostgreSQL (fuente=CASEN_ENS_REAL)...")
    try:
        stats = cargar_datos(df, session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    print(f"\n✓ Carga completada:")
    print(f"  Hogares:     {stats['hogares']}")
    print(f"  Personas:    {stats['personas']}")
    print(f"  Indicadores: {stats['indicadores']}")
    if stats["omitidos"]:
        print(f"  Omitidos (nivel_riesgo inválido): {stats['omitidos']}")
    print(
        "\nRecordatorio: la comuna de cada persona es una ESTIMACIÓN "
        "ponderada por población censal 2017, no un dato observado en "
        "CASEN (que no incluye comuna en esta extracción). Ver docstring "
        "de este script y sección 7.5 de la memoria."
    )


if __name__ == "__main__":
    main()
