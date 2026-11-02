"""
Script ETL — Carga de Vigilancia Nutricional REM P5 (MINSAL) por comuna
=========================================================================
Lee backend/data_real/rem_p5_nutricional_maule_2026.csv (generado por
backend/scripts/etl_real/step5_procesar_rem_p5.py) y actualiza las columnas
n_control_rem / pct_normal_rem / pct_bajo_peso_rem de comunas_resumen.

Es un UPDATE, no un INSERT: requiere que las 30 comunas ya existan en
comunas_resumen (poblar primero con scripts/load_comunas.py). Estos campos
son un registro administrativo oficial fijo por comuna — no dependen del
dataset (CASEN/ENS/sintético) cargado en personas/hogares/indicadores.

Uso:
    python scripts/load_rem_comunas.py --file data_real/rem_p5_nutricional_maule_2026.csv
"""

import argparse
import os

import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/nutricionar",
)


def cargar(df: pd.DataFrame, engine) -> tuple[int, list[str]]:
    actualizadas = 0
    sin_comuna = []
    with engine.begin() as conn:
        for _, row in df.iterrows():
            result = conn.execute(text("""
                UPDATE comunas_resumen
                SET n_control_rem     = :n_control,
                    pct_normal_rem    = :pct_normal,
                    pct_bajo_peso_rem = :pct_bajo
                WHERE comuna_cod = :cod
            """), {
                "n_control": int(row["n_control_jun"]),
                "pct_normal": float(row["pct_normal_jun"]),
                "pct_bajo": float(row["pct_bajo_peso_jun"]),
                "cod": str(row["comuna_cod"]).strip().zfill(5),
            })
            if result.rowcount:
                actualizadas += 1
            else:
                sin_comuna.append(row["comuna_cod"])
    return actualizadas, sin_comuna


def main():
    parser = argparse.ArgumentParser(
        description="Carga las columnas REM P5 en comunas_resumen"
    )
    parser.add_argument(
        "--file", required=True,
        help="Ruta a rem_p5_nutricional_maule_2026.csv"
    )
    args = parser.parse_args()

    print(f"Conectando a BD: {DATABASE_URL[:50]}...")
    engine = create_engine(DATABASE_URL)

    print(f"Leyendo {args.file}...")
    df = pd.read_csv(args.file, dtype={"comuna_cod": str})

    actualizadas, sin_comuna = cargar(df, engine)

    print(f"\n✓ Carga completada: {actualizadas} comuna(s) actualizadas")
    if sin_comuna:
        print(
            f"  Sin fila previa en comunas_resumen (ejecutar antes "
            f"scripts/load_comunas.py): {sin_comuna}"
        )


if __name__ == "__main__":
    main()
