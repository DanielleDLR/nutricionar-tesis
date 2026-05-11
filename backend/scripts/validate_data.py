"""
Script de Validación de Integridad — NutricioNar
=================================================
Verifica la calidad e integridad de los datos cargados en PostgreSQL.
Genera un reporte detallado con resultados por categoría.

Uso:
    python scripts/validate_data.py
    python scripts/validate_data.py --json   (output en formato JSON)
"""

import argparse
import json
import os
import sys
from datetime import datetime

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/nutricionar",
)

CHECKS = []


def check(nombre, categoria):
    """Decorador para registrar validaciones."""
    def decorator(fn):
        CHECKS.append((nombre, categoria, fn))
        return fn
    return decorator


# ─── VALIDACIONES DE COMPLETITUD ─────────────────────────────

@check("Personas con hogar_id válido", "Integridad referencial")
def check_fk_persona_hogar(conn):
    r = conn.execute(text("""
        SELECT COUNT(*) FROM personas p
        LEFT JOIN hogares h ON h.id = p.hogar_id
        WHERE h.id IS NULL
    """)).scalar()
    return r == 0, f"{r} personas sin hogar válido"


@check("Indicadores con persona_id válido", "Integridad referencial")
def check_fk_indicador_persona(conn):
    r = conn.execute(text("""
        SELECT COUNT(*) FROM indicadores_nutricionales i
        LEFT JOIN personas p ON p.id = i.persona_id
        WHERE p.id IS NULL
    """)).scalar()
    return r == 0, f"{r} indicadores sin persona válida"


@check("Sin personas duplicadas por hogar", "Duplicados")
def check_no_duplicados(conn):
    r = conn.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT hogar_id, edad, sexo, fuente
            FROM personas
            GROUP BY hogar_id, edad, sexo, fuente
            HAVING COUNT(*) > 1
        ) t
    """)).scalar()
    return r == 0, f"{r} grupos duplicados encontrados"


# ─── VALIDACIONES DE RANGO ────────────────────────────────────

@check("Edades en rango válido (60-120)", "Rangos")
def check_edad(conn):
    r = conn.execute(text(
        "SELECT COUNT(*) FROM personas WHERE edad < 60 OR edad > 120"
    )).scalar()
    return r == 0, f"{r} personas con edad fuera de rango"


@check("IMC en rango válido (10-70)", "Rangos")
def check_imc(conn):
    r = conn.execute(text(
        "SELECT COUNT(*) FROM personas"
        " WHERE imc IS NOT NULL AND (imc < 10 OR imc > 70)"
    )).scalar()
    return r == 0, f"{r} personas con IMC fuera de rango"


@check("Probabilidad de riesgo entre 0 y 1", "Rangos")
def check_probabilidad(conn):
    r = conn.execute(text("""
        SELECT COUNT(*) FROM indicadores_nutricionales
        WHERE probabilidad_riesgo IS NOT NULL
          AND (probabilidad_riesgo < 0 OR probabilidad_riesgo > 1)
    """)).scalar()
    return r == 0, f"{r} indicadores con probabilidad fuera de rango"


# ─── VALIDACIONES DE COMPLETITUD ─────────────────────────────

@check("Todas las personas tienen indicador", "Completitud")
def check_todos_tienen_indicador(conn):
    r = conn.execute(text("""
        SELECT COUNT(*) FROM personas p
        WHERE NOT EXISTS (
            SELECT 1 FROM indicadores_nutricionales i
            WHERE i.persona_id = p.id
        )
    """)).scalar()
    return r == 0, f"{r} personas sin indicador nutricional"


@check("Campo nivel_riesgo sin valores nulos", "Completitud")
def check_nivel_riesgo_nulo(conn):
    r = conn.execute(text(
        "SELECT COUNT(*) FROM indicadores_nutricionales"
        " WHERE nivel_riesgo IS NULL"
    )).scalar()
    return r == 0, f"{r} indicadores con nivel_riesgo nulo"


@check("Personas con edad registrada", "Completitud")
def check_edad_no_nula(conn):
    r = conn.execute(text(
        "SELECT COUNT(*) FROM personas WHERE edad IS NULL"
    )).scalar()
    return r == 0, f"{r} personas sin edad"


# ─── VALIDACIONES DE CONSISTENCIA ────────────────────────────

@check("Nivel_riesgo solo contiene valores válidos", "Consistencia")
def check_nivel_riesgo_valores(conn):
    r = conn.execute(text("""
        SELECT COUNT(*) FROM indicadores_nutricionales
        WHERE nivel_riesgo NOT IN ('alto', 'medio', 'bajo')
    """)).scalar()
    return r == 0, f"{r} indicadores con nivel_riesgo inválido"


@check("Sexo solo contiene M o F", "Consistencia")
def check_sexo_valores(conn):
    r = conn.execute(text(
        "SELECT COUNT(*) FROM personas WHERE sexo NOT IN ('M', 'F')"
    )).scalar()
    return r == 0, f"{r} personas con sexo inválido"


@check("Zona solo contiene urbano o rural", "Consistencia")
def check_zona_valores(conn):
    r = conn.execute(text(
        "SELECT COUNT(*) FROM hogares"
        " WHERE zona IS NOT NULL AND zona NOT IN ('urbano', 'rural')"
    )).scalar()
    return r == 0, f"{r} hogares con zona inválida"


# ─── ESTADÍSTICAS GENERALES ───────────────────────────────────

def estadisticas_generales(conn) -> dict:
    """Retorna estadísticas descriptivas básicas."""
    return {
        "total_hogares": conn.execute(
            text("SELECT COUNT(*) FROM hogares")
        ).scalar(),
        "total_personas": conn.execute(
            text("SELECT COUNT(*) FROM personas")
        ).scalar(),
        "total_indicadores": conn.execute(
            text("SELECT COUNT(*) FROM indicadores_nutricionales")
        ).scalar(),
        "distribucion_riesgo": dict(conn.execute(text("""
            SELECT nivel_riesgo, COUNT(*) as n
            FROM indicadores_nutricionales
            GROUP BY nivel_riesgo
            ORDER BY nivel_riesgo
        """)).fetchall()),
        "distribucion_zonas": dict(conn.execute(text("""
            SELECT zona, COUNT(*) as n
            FROM hogares
            GROUP BY zona
        """)).fetchall()),
        "pct_con_imc": round(conn.execute(text("""
            SELECT 100.0 * COUNT(*) FILTER (WHERE imc IS NOT NULL)
            / NULLIF(COUNT(*), 0)
            FROM personas
        """)).scalar() or 0, 1),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Valida integridad de datos en NutricioNar"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Emitir resultado en formato JSON"
    )
    args = parser.parse_args()

    engine = create_engine(DATABASE_URL)
    resultados = []
    fallos = 0

    with engine.connect() as conn:
        stats = estadisticas_generales(conn)

        for nombre, categoria, fn in CHECKS:
            try:
                ok, detalle = fn(conn)
            except Exception as e:
                ok, detalle = False, str(e)
            resultados.append({
                "nombre": nombre,
                "categoria": categoria,
                "ok": ok,
                "detalle": detalle,
            })
            if not ok:
                fallos += 1

    if args.json:
        print(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "estadisticas": stats,
            "validaciones": resultados,
            "resumen": {
                "total": len(resultados),
                "ok": len(resultados) - fallos,
                "fallos": fallos,
            },
        }, indent=2, default=str))
    else:
        print("\n" + "=" * 60)
        print("  REPORTE DE VALIDACIÓN — NutricioNar")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        print("\n📊 Estadísticas generales:")
        print(f"   Hogares     : {stats['total_hogares']:,}")
        print(f"   Personas    : {stats['total_personas']:,}")
        print(f"   Indicadores : {stats['total_indicadores']:,}")
        print(f"   % con IMC   : {stats['pct_con_imc']}%")
        print(f"   Riesgo      : {stats['distribucion_riesgo']}")
        print(f"   Zonas       : {stats['distribucion_zonas']}")

        print("\n🔍 Validaciones:")
        cat_actual = ""
        for r in resultados:
            if r["categoria"] != cat_actual:
                cat_actual = r["categoria"]
                print(f"\n  [{cat_actual}]")
            icono = "✓" if r["ok"] else "✗"
            print(f"   {icono} {r['nombre']}: {r['detalle']}")

        print("\n" + "=" * 60)
        if fallos == 0:
            print(f"  ✓ TODAS LAS VALIDACIONES PASARON ({len(resultados)})")
        else:
            print(
                f"  ✗ {fallos} de {len(resultados)}"
                f" validaciones FALLARON"
            )
        print("=" * 60 + "\n")

    sys.exit(0 if fallos == 0 else 1)


if __name__ == "__main__":
    main()
