"""
step5_procesar_rem_p5.py — Vigilancia Nutricional REM P5 (MINSAL, Región del Maule)
====================================================================================
Procesa los reportes oficiales de Vigilancia Nutricional del MINSAL (indicadores
7.3 "Estado nutricional bajo peso" y 7.4 "Estado nutricional normal" en personas
de 65 y más años, REM P5 Sección B/A) y produce un resumen comunal.

A diferencia de CASEN/ENS (encuestas muestrales), estos reportes son registro
administrativo: cuentan a TODAS las personas mayores bajo control en la red
asistencial pública de cada comuna (denominador ~250.000 adultos mayores en la
Región del Maule), no una muestra. Sirven como referencia de cobertura oficial
para contrastar con las estimaciones del modelo (CASEN/ENS/sintético).

Los archivos fuente son HTML servido con extensión .xls (exportación estándar
de la plataforma DEIS/MINSAL), no formato binario XLS — se leen con
`pandas.read_html`. Cada archivo trae, además del detalle por establecimiento,
una fila "Total Departamento de Salud <comuna>" con el consolidado comunal, que
es la que se usa aquí (evita re-sumar y arriesgar doble conteo entre postas y
hospitales de una misma comuna).

Limitación declarada: los reportes están cortados a junio (corte semestral);
las columnas de diciembre vienen vacías hasta el cierre del año.

Uso:
    python scripts/etl_real/step5_procesar_rem_p5.py \\
        --normal ../data/MINSAL/VigilanciaNutricional_Indicador_pesoNormal_2026.xls \\
        --bajo   ../data/MINSAL/VigilanciaNutricional_Indicador_pesoBajo_2026.xls \\
        --out data_real/rem_p5_nutricional_maule_2026.csv
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from load_comunas import COMUNAS_MAULE  # noqa: E402

# nombre de comuna (tal como aparece en el reporte MINSAL) -> código CUT
NOMBRE_A_COD = {nombre: cod for cod, (nombre, _region) in COMUNAS_MAULE.items()}

PREFIJO_TOTAL = "Total Departamento de Salud "

# Columnas del detalle (orden fijo del reporte, ver docstring del módulo):
# comuna, código, establecimiento, numerador_jun, numerador_dic,
# denominador_jun, denominador_dic, cumplimiento_junio, cumplimiento_diciembre
COL_COMUNA = 0
COL_NUMERADOR_JUN = 3
COL_DENOMINADOR_JUN = 5


def _extraer_totales_comunales(path: str) -> pd.DataFrame:
    """Lee un reporte REM P5 (HTML con extensión .xls) y devuelve las filas
    'Total Departamento de Salud <comuna>' (consolidado comunal, jun.)."""
    tablas = pd.read_html(path, encoding="ISO-8859-2", header=None)
    # La tabla de datos es la más grande de las que trae el archivo (las
    # primeras 2 son metadatos/encabezado del reporte).
    detalle = max(tablas, key=lambda t: t.shape[0])

    es_total = detalle.iloc[:, COL_COMUNA].astype(str).str.startswith(PREFIJO_TOTAL)
    totales = detalle[es_total].copy()

    comuna = totales.iloc[:, COL_COMUNA].str[len(PREFIJO_TOTAL):]
    numerador = pd.to_numeric(totales.iloc[:, COL_NUMERADOR_JUN], errors="coerce").fillna(0)
    denominador = pd.to_numeric(totales.iloc[:, COL_DENOMINADOR_JUN], errors="coerce").fillna(0)

    return pd.DataFrame({
        "comuna_nombre": comuna.values,
        "numerador_jun": numerador.values,
        "denominador_jun": denominador.values,
    })


def procesar(path_normal: str, path_bajo: str) -> pd.DataFrame:
    normal = _extraer_totales_comunales(path_normal).rename(
        columns={"numerador_jun": "n_normal_jun"}
    )
    bajo = _extraer_totales_comunales(path_bajo).rename(
        columns={"numerador_jun": "n_bajo_peso_jun"}
    )

    # El denominador (N° de personas mayores en control) es el mismo universo
    # en ambos reportes; se valida en vez de traer ambas columnas.
    merged = normal.merge(
        bajo[["comuna_nombre", "n_bajo_peso_jun", "denominador_jun"]],
        on="comuna_nombre", suffixes=("", "_bajo"),
    )
    inconsistentes = merged[
        (merged["denominador_jun"] - merged["denominador_jun_bajo"]).abs() > 0
    ]
    if not inconsistentes.empty:
        print(
            "AVISO: denominador distinto entre reportes para "
            f"{len(inconsistentes)} comuna(s); se usa el de 'peso normal'.",
            file=sys.stderr,
        )
    merged = merged.drop(columns=["denominador_jun_bajo"])

    merged["comuna_cod"] = merged["comuna_nombre"].map(NOMBRE_A_COD)
    sin_mapear = merged[merged["comuna_cod"].isna()]
    if not sin_mapear.empty:
        print(
            "AVISO: comunas del reporte sin código Maule conocido (se omiten): "
            f"{list(sin_mapear['comuna_nombre'])}",
            file=sys.stderr,
        )
    merged = merged.dropna(subset=["comuna_cod"])

    merged["n_control_jun"] = merged["denominador_jun"].astype(int)
    merged["n_normal_jun"] = merged["n_normal_jun"].astype(int)
    merged["n_bajo_peso_jun"] = merged["n_bajo_peso_jun"].astype(int)
    merged["pct_normal_jun"] = (
        100.0 * merged["n_normal_jun"] / merged["n_control_jun"]
    ).round(2)
    merged["pct_bajo_peso_jun"] = (
        100.0 * merged["n_bajo_peso_jun"] / merged["n_control_jun"]
    ).round(2)

    cols = [
        "comuna_cod", "comuna_nombre", "n_control_jun",
        "n_normal_jun", "pct_normal_jun",
        "n_bajo_peso_jun", "pct_bajo_peso_jun",
    ]
    return merged[cols].sort_values("comuna_cod").reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(
        description="Procesa los reportes REM P5 de vigilancia nutricional (MINSAL Maule)"
    )
    parser.add_argument("--normal", required=True, help="Indicador 7.4 (estado nutricional normal)")
    parser.add_argument("--bajo", required=True, help="Indicador 7.3 (estado nutricional bajo peso)")
    parser.add_argument("--out", required=True, help="CSV de salida (resumen comunal)")
    args = parser.parse_args()

    df = procesar(args.normal, args.bajo)
    df.to_csv(args.out, index=False)

    print(f"{len(df)} comunas procesadas -> {args.out}")
    print(f"Total personas mayores en control (jun.): {df['n_control_jun'].sum():,}")
    print(
        f"Bajo peso (jun.): {df['n_bajo_peso_jun'].sum():,} "
        f"({100.0 * df['n_bajo_peso_jun'].sum() / df['n_control_jun'].sum():.1f}%)"
    )


if __name__ == "__main__":
    main()
