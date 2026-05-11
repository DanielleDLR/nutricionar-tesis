"""
Script ETL — Carga de Resumen Comunal
======================================
Lee la hoja 'resumen_comunal' del dataset_sintetico_maule.xlsx
y carga los datos en la tabla comunas_resumen de PostgreSQL.

Si la hoja no existe, genera el resumen directamente desde las
tablas hogares/personas/indicadores ya cargadas en la BD.

Uso:
    python scripts/load_comunas.py
    python scripts/load_comunas.py --file ruta/al/dataset_sintetico_maule.xlsx
    python scripts/load_comunas.py --reset
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/nutricionar",
)

# Comunas del Maule con código INE
COMUNAS_MAULE = {
    "07101": ("Talca", "07"),
    "07102": ("Constitución", "07"),
    "07103": ("Curepto", "07"),
    "07104": ("Empedrado", "07"),
    "07105": ("Maule", "07"),
    "07106": ("Pelarco", "07"),
    "07107": ("Pencahue", "07"),
    "07108": ("Río Claro", "07"),
    "07109": ("San Clemente", "07"),
    "07110": ("San Rafael", "07"),
    "07201": ("Cauquenes", "07"),
    "07202": ("Chanco", "07"),
    "07203": ("Pelluhue", "07"),
    "07301": ("Curicó", "07"),
    "07302": ("Hualañé", "07"),
    "07303": ("Licantén", "07"),
    "07304": ("Molina", "07"),
    "07305": ("Rauco", "07"),
    "07306": ("Romeral", "07"),
    "07307": ("Sagrada Familia", "07"),
    "07308": ("Teno", "07"),
    "07309": ("Vichuquén", "07"),
    "07401": ("Linares", "07"),
    "07402": ("Colbún", "07"),
    "07403": ("Longaví", "07"),
    "07404": ("Parral", "07"),
    "07405": ("Retiro", "07"),
    "07406": ("San Javier", "07"),
    "07407": ("Villa Alegre", "07"),
    "07408": ("Yerbas Buenas", "07"),
}


def clasificar_riesgo_zona(pct_riesgo_alto_crit: float) -> str:
    """Clasifica el nivel de riesgo de la zona según % de riesgo alto/crítico."""
    if pct_riesgo_alto_crit >= 40:
        return "critico"
    elif pct_riesgo_alto_crit >= 25:
        return "alto"
    elif pct_riesgo_alto_crit >= 10:
        return "medio"
    return "bajo"


def cargar_desde_excel(xl: pd.ExcelFile, engine) -> int:
    """Intenta leer la hoja 'resumen_comunal' del Excel."""
    df = xl.parse("resumen_comunal", header=1)
    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]

    insertados = 0
    with engine.begin() as conn:
        for _, row in df.iterrows():
            cod = str(row["comuna_cod"]).strip().zfill(5)
            nombre, region = COMUNAS_MAULE.get(cod, (str(row.get(
                "comuna_nombre", cod)), "07"))

            total = int(row.get("total_personas", 0))
            n_critico = int(row.get("n_critico", 0))
            n_alto = int(row.get("n_alto", 0))
            pct_rac = round(
                100.0 * (n_critico + n_alto) / total if total > 0 else 0, 2
            )

            conn.execute(text("""
                INSERT INTO comunas_resumen (
                    comuna_cod, comuna_nombre, region_cod,
                    total_personas, n_desnutricion, n_riesgo, n_normal,
                    pct_desnutricion, pct_riesgo_mna,
                    pct_inseg_severa, pct_inseg_mod_sev,
                    n_benef_pacam, pct_no_retiro_pacam,
                    n_critico, n_alto, pct_riesgo_alto_crit,
                    nivel_riesgo_zona
                ) VALUES (
                    :cod, :nombre, :region,
                    :total, :n_desnut, :n_riesgo, :n_normal,
                    :pct_desnut, :pct_mna,
                    :pct_inseg_sev, :pct_inseg_ms,
                    :n_pacam, :pct_no_retiro,
                    :n_critico, :n_alto, :pct_rac,
                    :nivel_zona
                )
                ON CONFLICT (comuna_cod) DO UPDATE SET
                    total_personas       = EXCLUDED.total_personas,
                    n_desnutricion       = EXCLUDED.n_desnutricion,
                    n_riesgo             = EXCLUDED.n_riesgo,
                    n_normal             = EXCLUDED.n_normal,
                    pct_desnutricion     = EXCLUDED.pct_desnutricion,
                    pct_riesgo_mna       = EXCLUDED.pct_riesgo_mna,
                    pct_inseg_severa     = EXCLUDED.pct_inseg_severa,
                    pct_inseg_mod_sev    = EXCLUDED.pct_inseg_mod_sev,
                    n_benef_pacam        = EXCLUDED.n_benef_pacam,
                    pct_no_retiro_pacam  = EXCLUDED.pct_no_retiro_pacam,
                    n_critico            = EXCLUDED.n_critico,
                    n_alto               = EXCLUDED.n_alto,
                    pct_riesgo_alto_crit = EXCLUDED.pct_riesgo_alto_crit,
                    nivel_riesgo_zona    = EXCLUDED.nivel_riesgo_zona
            """), {
                "cod": cod,
                "nombre": nombre,
                "region": region,
                "total": total,
                "n_desnut": int(row.get("n_desnutricion", 0)),
                "n_riesgo": int(row.get("n_riesgo", 0)),
                "n_normal": int(row.get("n_normal", 0)),
                "pct_desnut": float(row.get("pct_desnutricion", 0)),
                "pct_mna": float(row.get("pct_riesgo_mna", 0)),
                "pct_inseg_sev": float(row.get("pct_inseg_severa", 0)),
                "pct_inseg_ms": float(row.get("pct_inseg_mod_sev", 0)),
                "n_pacam": int(row.get("n_benef_pacam", 0)),
                "pct_no_retiro": float(row.get("pct_no_retiro_pacam", 0)),
                "n_critico": n_critico,
                "n_alto": n_alto,
                "pct_rac": pct_rac,
                "nivel_zona": clasificar_riesgo_zona(pct_rac),
            })
            insertados += 1

    return insertados


def cargar_desde_bd(engine) -> int:
    """
    Genera resumen comunal directamente desde las tablas de la BD.
    Distribuye las personas de la región Maule entre sus comunas
    de forma aleatoria pero reproducible (para el piloto sintético).
    """
    import random
    random.seed(42)

    with engine.begin() as conn:
        total_bd = conn.execute(text(
            "SELECT COUNT(*) FROM personas"
        )).scalar() or 0

        if total_bd == 0:
            print("  ⚠ No hay personas en la BD. Carga el dataset primero.")
            return 0

        # Obtener distribución real de riesgos
        dist = dict(conn.execute(text("""
            SELECT nivel_riesgo, COUNT(*) FROM indicadores_nutricionales
            GROUP BY nivel_riesgo
        """)).fetchall())

        pct_alto = dist.get("alto", 0) / total_bd
        pct_medio = dist.get("medio", 0) / total_bd

        # Obtener % inseguridad y pacam
        pct_inseg_sev = conn.execute(text("""
            SELECT ROUND(100.0 * COUNT(*) FILTER (
                WHERE nivel_inseguridad = 'severo')
            / NULLIF(COUNT(*), 0), 2)
            FROM personas
        """)).scalar() or 0

        pct_inseg_ms = conn.execute(text("""
            SELECT ROUND(100.0 * COUNT(*) FILTER (
                WHERE nivel_inseguridad IN ('moderado','severo'))
            / NULLIF(COUNT(*), 0), 2)
            FROM personas
        """)).scalar() or 0

        pct_pacam = conn.execute(text("""
            SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE acceso_pacam)
            / NULLIF(COUNT(*), 0), 2)
            FROM hogares
        """)).scalar() or 0

    comunas_list = list(COMUNAS_MAULE.items())
    n_comunas = len(comunas_list)

    # Distribuir total de personas entre las comunas (pesos aleatorios)
    weights = [random.randint(1, 10) for _ in comunas_list]
    total_w = sum(weights)
    totales = [max(1, round(total_bd * w / total_w)) for w in weights]

    insertados = 0
    with engine.begin() as conn:
        for i, (cod, (nombre, region)) in enumerate(comunas_list):
            total = totales[i]
            # Variación ±20% alrededor del promedio regional
            factor = random.uniform(0.80, 1.20)
            pct_a = round(min(100, pct_alto * 100 * factor), 2)
            pct_m = round(min(100 - pct_a, pct_medio * 100 * factor), 2)

            n_alto = round(total * pct_a / 100)
            n_critico = round(n_alto * random.uniform(0.2, 0.5))
            n_riesgo = round(total * pct_m / 100)
            n_normal = total - n_alto - n_riesgo
            n_desnut = round(n_alto * random.uniform(0.3, 0.6))

            pct_rac = round(100.0 * (n_critico + n_alto) / total
                            if total > 0 else 0, 2)
            pct_mna = round(pct_a + pct_m, 2)
            pct_i_sev = round(float(pct_inseg_sev) * factor, 2)
            pct_i_ms = round(float(pct_inseg_ms) * factor, 2)
            n_pacam = round(total * float(pct_pacam) / 100 * factor)
            pct_no_ret = round(random.uniform(10, 35), 2)

            conn.execute(text("""
                INSERT INTO comunas_resumen (
                    comuna_cod, comuna_nombre, region_cod,
                    total_personas, n_desnutricion, n_riesgo, n_normal,
                    pct_desnutricion, pct_riesgo_mna,
                    pct_inseg_severa, pct_inseg_mod_sev,
                    n_benef_pacam, pct_no_retiro_pacam,
                    n_critico, n_alto, pct_riesgo_alto_crit,
                    nivel_riesgo_zona
                ) VALUES (
                    :cod, :nombre, :region,
                    :total, :n_desnut, :n_riesgo, :n_normal,
                    :pct_desnut, :pct_mna,
                    :pct_inseg_sev, :pct_inseg_ms,
                    :n_pacam, :pct_no_retiro,
                    :n_critico, :n_alto, :pct_rac,
                    :nivel_zona
                )
                ON CONFLICT (comuna_cod) DO UPDATE SET
                    total_personas       = EXCLUDED.total_personas,
                    n_desnutricion       = EXCLUDED.n_desnutricion,
                    n_riesgo             = EXCLUDED.n_riesgo,
                    n_normal             = EXCLUDED.n_normal,
                    pct_desnutricion     = EXCLUDED.pct_desnutricion,
                    pct_riesgo_mna       = EXCLUDED.pct_riesgo_mna,
                    pct_inseg_severa     = EXCLUDED.pct_inseg_severa,
                    pct_inseg_mod_sev    = EXCLUDED.pct_inseg_mod_sev,
                    n_benef_pacam        = EXCLUDED.n_benef_pacam,
                    pct_no_retiro_pacam  = EXCLUDED.pct_no_retiro_pacam,
                    n_critico            = EXCLUDED.n_critico,
                    n_alto               = EXCLUDED.n_alto,
                    pct_riesgo_alto_crit = EXCLUDED.pct_riesgo_alto_crit,
                    nivel_riesgo_zona    = EXCLUDED.nivel_riesgo_zona
            """), {
                "cod": cod,
                "nombre": nombre,
                "region": region,
                "total": total,
                "n_desnut": n_desnut,
                "n_riesgo": n_riesgo,
                "n_normal": max(0, n_normal),
                "pct_desnut": round(100.0 * n_desnut / total, 2),
                "pct_mna": pct_mna,
                "pct_inseg_sev": pct_i_sev,
                "pct_inseg_ms": pct_i_ms,
                "n_pacam": n_pacam,
                "pct_no_retiro": pct_no_ret,
                "n_critico": n_critico,
                "n_alto": n_alto,
                "pct_rac": pct_rac,
                "nivel_zona": clasificar_riesgo_zona(pct_rac),
            })
            insertados += 1

    return insertados


def main():
    parser = argparse.ArgumentParser(
        description="Carga resumen comunal en PostgreSQL"
    )
    parser.add_argument(
        "--file",
        help="Ruta al archivo dataset_sintetico_maule.xlsx (opcional)"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Elimina datos existentes antes de cargar"
    )
    args = parser.parse_args()

    print(f"\nConectando a BD: {DATABASE_URL[:50]}...")
    engine = create_engine(DATABASE_URL)

    if args.reset:
        with engine.begin() as conn:
            conn.execute(text(
                "TRUNCATE comunas_resumen RESTART IDENTITY"
            ))
        print("  Tabla comunas_resumen limpiada.")

    # Intentar leer desde Excel si se provee archivo
    if args.file and Path(args.file).exists():
        print(f"\nLeyendo hoja 'resumen_comunal' de: {args.file}")
        xl = pd.ExcelFile(args.file)
        if "resumen_comunal" in xl.sheet_names:
            n = cargar_desde_excel(xl, engine)
            print(f"  → {n} comunas cargadas desde Excel.")
        else:
            print("  Hoja 'resumen_comunal' no encontrada. "
                  "Generando desde BD...")
            n = cargar_desde_bd(engine)
            print(f"  → {n} comunas generadas desde BD.")
    else:
        print("\nGenerando resumen comunal desde datos de la BD...")
        n = cargar_desde_bd(engine)
        print(f"  → {n} comunas generadas desde BD.")

    if n > 0:
        print(f"\n✓ {n} comunas cargadas exitosamente en comunas_resumen.")
    else:
        print("\n✗ No se cargaron comunas.")
        sys.exit(1)


if __name__ == "__main__":
    main()
