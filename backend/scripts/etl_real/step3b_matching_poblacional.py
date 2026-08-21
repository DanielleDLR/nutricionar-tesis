"""
step3b_matching_poblacional.py — Emparejamiento CON reemplazo (dataset poblacional)
======================================================================================
A diferencia de step3_matching_y_iprn.py (que empareja SIN reemplazo y por eso
queda acotado por el N más chico, ENS=293), este script empareja CON reemplazo:
cada una de las 3.352 personas de CASEN Maule 60+ recibe las variables clínicas
de su donante ENS más parecido (mismo sexo y zona, edad más cercana), permitiendo
que un mismo donante ENS sea reutilizado para varios receptores CASEN similares.

USO PREVISTO: poblar el dashboard/mapa con una estimación de riesgo nutricional
para las 3.352 personas mayores del Maule presentes en CASEN 2022.

USO NO RECOMENDADO: entrenar o validar el modelo con este archivo. Al reutilizar
donantes, muchas filas comparten valores clínicos casi idénticos, lo que
optimiza artificialmente cualquier métrica de validación cruzada (fuga de
información entre folds). Para entrenar/evaluar, usar el dataset de
step3_matching_y_iprn.py (N=293, un donante por fila, sin reemplazo).

Uso:
    python step3b_matching_poblacional.py \
        --casen casen_maule_60.csv --ens ens_maule_60.csv \
        --out real_maule_poblacion_completa.csv
"""

import argparse

import numpy as np
import pandas as pd

from step3_matching_y_iprn import construir_iprn


def emparejar_con_reemplazo(df_casen: pd.DataFrame, df_ens: pd.DataFrame) -> pd.DataFrame:
    filas = []
    donantes_usados = {}  # cuenta cuántas veces se reutilizó cada donante (para reportar)

    for grupo_key, grupo_casen in df_casen.groupby(["sexo", "zona"]):
        sexo, zona = grupo_key
        pool = df_ens[(df_ens["sexo"] == sexo) & (df_ens["zona"] == zona)]
        if pool.empty:
            pool = df_ens[df_ens["sexo"] == sexo]
        if pool.empty:
            pool = df_ens  # último recurso: cualquier donante

        edades_pool = pool["edad"].to_numpy()
        for _, receptor in grupo_casen.iterrows():
            idx_local = np.argmin(np.abs(edades_pool - receptor["edad"]))
            donante = pool.iloc[idx_local]
            donante_id = donante["id_persona_ens"]
            donantes_usados[donante_id] = donantes_usados.get(donante_id, 0) + 1

            fila = receptor.to_dict()
            for col in ["imc", "circ_pantorrilla", "diabetes", "hta", "depresion", "perdio_peso"]:
                fila[col] = donante[col]
            fila["id_persona_ens_donante"] = donante_id
            fila["diff_edad_matching"] = abs(donante["edad"] - receptor["edad"])
            filas.append(fila)

    df_final = pd.DataFrame(filas)
    print(f"Donantes ENS únicos utilizados: {len(donantes_usados)} de {len(df_ens)}")
    reuse = pd.Series(donantes_usados).describe()
    print(f"Reutilización por donante -> media: {reuse['mean']:.1f}, máx: {reuse['max']:.0f}")
    return df_final


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--casen", required=True)
    ap.add_argument("--ens", required=True)
    ap.add_argument("--out", default="real_maule_poblacion_completa.csv")
    args = ap.parse_args()

    df_casen = pd.read_csv(args.casen)
    df_ens = pd.read_csv(args.ens)
    print(f"CASEN Maule 60+ (receptor): {len(df_casen)} | ENS Maule 60+ (donante): {len(df_ens)}")

    matched = emparejar_con_reemplazo(df_casen, df_ens)
    print(f"Población final: {len(matched)} personas (= 100% de CASEN Maule 60+)")
    print(f"Diferencia de edad promedio en el matching: {matched['diff_edad_matching'].mean():.2f} años")

    final = construir_iprn(matched)
    final.to_csv(args.out, index=False)
    print(f"\nGuardado: {args.out}")
    print("\nDistribución nivel_riesgo (poblacional, con reemplazo):")
    print(final["nivel_riesgo"].value_counts(normalize=True).round(3))


if __name__ == "__main__":
    main()
