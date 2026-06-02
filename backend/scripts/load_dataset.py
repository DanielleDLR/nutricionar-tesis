"""
Script ETL — Carga del Dataset Sintético Piloto Maule
======================================================
Lee dataset_sintetico_maule.xlsx y carga los datos en PostgreSQL
mapeando a las tablas: hogares, personas, indicadores_nutricionales.

Uso:
    python scripts/load_dataset.py --file ruta/al/dataset_sintetico_maule.xlsx
    python scripts/load_dataset.py --file ruta/al/dataset_sintetico_maule.xlsx --reset
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# ─── Configuración ───────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/nutricionar",
)
FUENTE = "SINTETICO"
ANIO = 2026


def leer_hoja(xl: pd.ExcelFile, nombre: str) -> pd.DataFrame:
    """Lee una hoja del Excel saltando las 2 filas de encabezado."""
    df = xl.parse(nombre, header=1)
    df = df.dropna(how="all")
    return df


def limpiar_zona(valor) -> str:
    """Normaliza zona: 1 → urbano, 2 → rural."""
    mapping = {1: "urbano", 2: "rural", "1": "urbano", "2": "rural"}
    return mapping.get(valor, "urbano")


def limpiar_sexo(valor) -> str:
    """Normaliza sexo: 1/2 → M/F."""
    mapping = {1: "M", 2: "F", "1": "M", "2": "F"}
    return mapping.get(valor, "M")


def limpiar_inseguridad(valor) -> str:
    """Convierte código numérico FIES a etiqueta."""
    mapping = {
        0: "seguro", 1: "leve", 2: "moderado", 3: "severo",
        "0": "seguro", "1": "leve", "2": "moderado", "3": "severo",
    }
    return mapping.get(valor, "seguro")


def cargar_datos(xl: pd.ExcelFile, session) -> dict:
    """Carga todos los datos y retorna estadísticas."""
    stats = {}

    # ── 1. Leer todas las hojas ──────────────────────────────
    print("  Leyendo hojas del Excel...")
    df_personas = leer_hoja(xl, "personas_mayores")
    df_nutric = leer_hoja(xl, "indicadores_nutric")
    df_inseg = leer_hoja(xl, "inseg_alimentaria")
    df_acceso = leer_hoja(xl, "acceso_programas")

    # Limpiar nombres de columnas
    for df in [df_personas, df_nutric, df_inseg, df_acceso]:
        df.columns = [str(c).strip() for c in df.columns]

    # ── 2. Construir hogares (uno por persona en este dataset) ─
    print("  Insertando hogares...")
    hogares_insertados = 0
    id_persona_to_hogar = {}

    for _, row in df_personas.iterrows():
        id_persona = str(row["id_persona"]).strip()

        # Buscar si tiene beneficio PACAM
        acceso_row = df_acceso[
            df_acceso["id_persona"].astype(str).str.strip() == id_persona
        ]
        acceso_pacam = bool(
            acceso_row["beneficiario_pacam"].values[0]
        ) if len(acceso_row) > 0 else False
        acceso_rsh = str(row.get("tramo_rsh", "")).strip() != ""

        result = session.execute(text("""
            INSERT INTO hogares
                (region, zona, ingreso_total, quintil_ingreso,
                 n_integrantes, hacinamiento, acceso_pacam, acceso_rsh)
            VALUES
                (:region, :zona, :ingreso, :quintil,
                 :n_int, :hacinamiento, :acceso_pacam, :acceso_rsh)
            RETURNING id
        """), {
            "region": str(row.get("region_cod", "07")).strip(),
            "zona": limpiar_zona(row.get("zona_urbano_rural")),
            "ingreso": float(row["ingreso_total_hogar"])
            if pd.notna(row.get("ingreso_total_hogar")) else None,
            "quintil": None,
            "n_int": int(row["num_integrantes_hogar"])
            if pd.notna(row.get("num_integrantes_hogar")) else None,
            "hacinamiento": bool(row.get("hacinamiento", 0)),
            "acceso_pacam": acceso_pacam,
            "acceso_rsh": acceso_rsh,
        })
        hogar_id = result.fetchone()[0]
        id_persona_to_hogar[id_persona] = hogar_id
        hogares_insertados += 1

    session.flush()
    stats["hogares"] = hogares_insertados
    print(f"    → {hogares_insertados} hogares insertados")

    # ── 3. Insertar personas ──────────────────────────────────
    print("  Insertando personas...")
    personas_insertadas = 0
    id_persona_to_db = {}

    for _, row in df_personas.iterrows():
        id_persona = str(row["id_persona"]).strip()
        hogar_id = id_persona_to_hogar.get(id_persona)
        if not hogar_id:
            continue

        # Buscar inseguridad alimentaria
        inseg_row = df_inseg[
            df_inseg["id_persona"].astype(str).str.strip() == id_persona
        ]
        nivel_inseg = limpiar_inseguridad(
            inseg_row["nivel_inseguridad"].values[0]
        ) if len(inseg_row) > 0 else None

        # Buscar indicadores para IMC y diagnósticos
        nut_row = df_nutric[
            df_nutric["id_persona"].astype(str).str.strip() == id_persona
        ]
        imc = float(nut_row["imc"].values[0]) if (
            len(nut_row) > 0 and pd.notna(nut_row["imc"].values[0])
        ) else None
        pantorrilla = float(
            nut_row["circ_pantorrilla_cm"].values[0]
        ) if (
            len(nut_row) > 0
            and pd.notna(nut_row["circ_pantorrilla_cm"].values[0])
        ) else None
        diabetes = bool(
            nut_row["diagnostico_diabetes"].values[0]
        ) if len(nut_row) > 0 else False
        hta = bool(
            nut_row["diagnostico_hta"].values[0]
        ) if len(nut_row) > 0 else False
        depresion = bool(
            nut_row["diagnostico_depresion"].values[0]
        ) if len(nut_row) > 0 else False

        motivo = str(row.get("motivo_no_retiro", "") or "").strip().lower()
        if motivo not in ("lejania", "desconocimiento", "movilidad", "otro"):
            motivo = None

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
            "vive_solo": False,
            "imc": imc,
            "pantorrilla": pantorrilla,
            "diabetes": diabetes,
            "hta": hta,
            "depresion": depresion,
            "inseg": nivel_inseg,
            "motivo": motivo,
            "fuente": FUENTE,
            "anio": ANIO,
        })
        persona_db_id = result.fetchone()[0]
        id_persona_to_db[id_persona] = persona_db_id
        personas_insertadas += 1

    session.flush()
    stats["personas"] = personas_insertadas
    print(f"    → {personas_insertadas} personas insertadas")

    # ── 4. Insertar indicadores nutricionales ─────────────────
    print("  Insertando indicadores nutricionales...")
    indicadores_insertados = 0

    nivel_map = {
        "alto": "alto", "medio": "medio", "bajo": "bajo",
        0: "bajo", 1: "medio", 2: "alto",
    }

    for _, row in df_nutric.iterrows():
        id_persona = str(row["id_persona"]).strip()
        persona_db_id = id_persona_to_db.get(id_persona)
        if not persona_db_id:
            continue

        nivel_raw = str(row.get("nivel_riesgo", "medio")).strip().lower()
        nivel = nivel_map.get(nivel_raw, "medio")
        prob = float(row["prob_riesgo_desnutricion"]) if (
            pd.notna(row.get("prob_riesgo_desnutricion"))
        ) else None

        # Estado nutricional basado en IMC
        imc_cat = str(row.get("imc_categoria", "")).strip()
        estado_nut_map = {
            "0": "bajo peso", "1": "normal", "2": "sobrepeso", "3": "obesidad",
        }
        estado_nut = estado_nut_map.get(imc_cat, None)

        session.execute(text("""
            INSERT INTO indicadores_nutricionales
                (persona_id, nivel_riesgo, probabilidad_riesgo,
                 estado_nutricional, modelo_version)
            VALUES
                (:persona_id, :nivel, :prob, :estado, :version)
        """), {
            "persona_id": persona_db_id,
            "nivel": nivel,
            "prob": prob,
            "estado": estado_nut,
            "version": "v0.1-sintetico",
        })
        indicadores_insertados += 1

    session.flush()
    stats["indicadores"] = indicadores_insertados
    print(f"    → {indicadores_insertados} indicadores insertados")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Carga dataset sintético Maule en PostgreSQL"
    )
    parser.add_argument(
        "--file", required=True,
        help="Ruta al archivo dataset_sintetico_maule.xlsx"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Elimina datos existentes antes de cargar"
    )
    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"Error: archivo no encontrado: {args.file}")
        sys.exit(1)

    print(f"\nConectando a BD: {DATABASE_URL[:50]}...")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        if args.reset:
            print("  Limpiando datos existentes...")
            session.execute(
                text("TRUNCATE indicadores_nutricionales, personas, hogares"
                     " RESTART IDENTITY CASCADE")
            )
            print("  Tablas limpiadas.")

        print(f"\nLeyendo: {args.file}")
        xl = pd.ExcelFile(args.file)

        print("\nCargando datos...")
        stats = cargar_datos(xl, session)

        session.commit()
        print("\n✓ Carga completada exitosamente:")
        for tabla, n in stats.items():
            print(f"   {tabla}: {n:,} registros")

    except Exception as e:
        session.rollback()
        print(f"\n✗ Error durante la carga: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
