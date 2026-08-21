"""
Pruebas de carga con dataset sintético (S13 · Carta Gantt).

Siembra la base de datos de test (SQLite en memoria/archivo) con N hogares,
personas e indicadores sintéticos y golpea los endpoints clave de forma
concurrente, midiendo latencia (p50/p95/p99) y throughput. Las aserciones
verifican que el backend responde correctamente y dentro de umbrales
razonables bajo carga.

Ejecutar solo estas pruebas:
    pytest tests/test_load.py -v -s

Ajustar el tamaño del dataset con la variable de entorno LOAD_TEST_N
(por defecto 500 personas) y la concurrencia con LOAD_TEST_WORKERS (8).
"""
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.models import Hogar, Persona, IndicadorNutricional, ComunaResumen
from tests.conftest import TestingSessionLocal

# --- Parámetros configurables ------------------------------------------------
N_PERSONAS = int(os.getenv("LOAD_TEST_N", "500"))
N_WORKERS = int(os.getenv("LOAD_TEST_WORKERS", "8"))
N_REQUESTS = int(os.getenv("LOAD_TEST_REQUESTS", "240"))

# Umbrales de aceptación (segundos). Generosos para correr en CI/local.
P95_MAX_S = float(os.getenv("LOAD_TEST_P95_MAX", "1.5"))

# Comunas del Maule (subconjunto representativo) para repartir la población.
COMUNAS = [
    ("07101", "Talca"),
    ("07401", "Linares"),
    ("07301", "Curicó"),
    ("07201", "Cauquenes"),
    ("07406", "Parral"),
    ("07102", "Constitución"),
    ("07108", "San Clemente"),
    ("07310", "Molina"),
]
NIVELES_RIESGO = ["alto", "medio", "bajo"]
NIVELES_INSEG = ["seguro", "leve", "moderado", "severo"]


# --- Siembra del dataset sintético ------------------------------------------
@pytest.fixture(scope="module", autouse=True)
def seed_dataset():
    """Genera un dataset sintético determinista para las pruebas de carga."""
    random.seed(42)
    db = TestingSessionLocal()
    try:
        # Estado limpio para evitar colisiones con otros módulos de test
        # (p. ej. comuna_cod es UNIQUE en ComunaResumen).
        db.query(IndicadorNutricional).delete()
        db.query(Persona).delete()
        db.query(Hogar).delete()
        db.query(ComunaResumen).delete()
        db.commit()

        # Resumen comunal sintético
        for cod, nombre in COMUNAS:
            db.add(ComunaResumen(
                comuna_cod=cod, comuna_nombre=nombre, region_cod="07",
                total_personas=random.randint(50, 200),
                pct_desnutricion=round(random.uniform(2, 8), 1),
                pct_riesgo_mna=round(random.uniform(10, 45), 1),
                pct_inseg_severa=round(random.uniform(3, 12), 1),
                pct_riesgo_alto_crit=round(random.uniform(15, 50), 1),
                n_critico=random.randint(0, 20), n_alto=random.randint(5, 40),
                nivel_riesgo_zona=random.choice(["bajo", "medio", "alto", "critico"]),
            ))

        # Hogares + personas + indicadores
        for i in range(N_PERSONAS):
            cod, _ = random.choice(COMUNAS)
            hogar = Hogar(
                region="07", comuna=cod,
                zona=random.choice(["urbano", "rural"]),
                ingreso_total=random.uniform(150_000, 900_000),
                quintil_ingreso=random.randint(1, 5),
                n_integrantes=random.randint(1, 5),
                acceso_pacam=random.random() < 0.4,
                acceso_rsh=random.random() < 0.7,
            )
            db.add(hogar)
            db.flush()  # obtener hogar.id

            persona = Persona(
                hogar_id=hogar.id,
                edad=random.randint(60, 95),
                sexo=random.choice(["M", "F"]),
                imc=round(random.uniform(17, 34), 1),
                tiene_diabetes=random.random() < 0.25,
                tiene_hipertension=random.random() < 0.5,
                tiene_depresion=random.random() < 0.2,
                vive_solo=random.random() < 0.35,
                puntaje_elcsa=random.randint(0, 15),
                nivel_inseguridad=random.choice(NIVELES_INSEG),
                fuente="SINTETICO",
            )
            db.add(persona)
            db.flush()

            db.add(IndicadorNutricional(
                persona_id=persona.id,
                nivel_riesgo=random.choice(NIVELES_RIESGO),
                probabilidad_riesgo=round(random.random(), 3),
                estado_nutricional=random.choice(["normal", "bajo peso", "obesidad"]),
                factor_1="edad_avanzada",
            ))

        db.commit()
    finally:
        db.close()

    # Invalidar el caché para que los agregados reflejen los datos sembrados
    from app.cache import clear_cache
    clear_cache()
    yield


# --- Utilidades de medición --------------------------------------------------
def _percentile(values, pct):
    if not values:
        return 0.0
    ordered = sorted(values)
    k = int(round((pct / 100) * (len(ordered) - 1)))
    return ordered[k]


def _hammer(client, endpoint, n_requests, n_workers):
    """Lanza n_requests concurrentes contra un endpoint y mide latencias."""
    latencies = []
    errors = 0

    def _one(_):
        t0 = time.perf_counter()
        r = client.get(endpoint)
        dt = time.perf_counter() - t0
        return r.status_code, dt

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        for status, dt in pool.map(_one, range(n_requests)):
            latencies.append(dt)
            if status >= 400:
                errors += 1
    elapsed = time.perf_counter() - started

    return {
        "endpoint": endpoint,
        "n": n_requests,
        "errors": errors,
        "elapsed_s": elapsed,
        "throughput_rps": n_requests / elapsed if elapsed else 0,
        "p50": _percentile(latencies, 50),
        "p95": _percentile(latencies, 95),
        "p99": _percentile(latencies, 99),
    }


ENDPOINTS = [
    "/api/v1/indicadores/resumen",
    "/api/v1/comunas/",
    "/api/v1/indicadores/stats",
    "/api/v1/indicadores/",
]


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_carga_endpoint(client, endpoint):
    """Cada endpoint clave responde sin errores y dentro del umbral p95."""
    stats = _hammer(client, endpoint, N_REQUESTS, N_WORKERS)

    print(
        f"\n[CARGA] {stats['endpoint']:<32} "
        f"n={stats['n']} err={stats['errors']} "
        f"rps={stats['throughput_rps']:6.1f} "
        f"p50={stats['p50']*1000:6.1f}ms "
        f"p95={stats['p95']*1000:6.1f}ms "
        f"p99={stats['p99']*1000:6.1f}ms"
    )

    assert stats["errors"] == 0, f"{stats['errors']} respuestas con error en {endpoint}"
    assert stats["p95"] < P95_MAX_S, (
        f"p95={stats['p95']:.3f}s supera el umbral {P95_MAX_S}s en {endpoint}"
    )


def test_resumen_carga_global(client):
    """Resumen agregado de carga sobre todos los endpoints (informe en consola)."""
    print(f"\n{'='*72}")
    print(f"PRUEBA DE CARGA · dataset sintético: {N_PERSONAS} personas · "
          f"{N_WORKERS} workers · {N_REQUESTS} req/endpoint")
    print(f"{'='*72}")
    total_req = 0
    total_err = 0
    for endpoint in ENDPOINTS:
        s = _hammer(client, endpoint, N_REQUESTS, N_WORKERS)
        total_req += s["n"]
        total_err += s["errors"]
        print(
            f"  {s['endpoint']:<32} "
            f"rps={s['throughput_rps']:6.1f} "
            f"p95={s['p95']*1000:6.1f}ms "
            f"err={s['errors']}"
        )
    print(f"{'-'*72}")
    print(f"  TOTAL: {total_req} requests · {total_err} errores")
    print(f"{'='*72}\n")
    assert total_err == 0
