"""
Pruebas de usuario · Simulación analista MINSAL (S15 · Carta Gantt)
==================================================================
Hito: "Entrega: Dashboard v1.0 completo".

Estas pruebas de aceptación (UAT) recorren de extremo a extremo los flujos
reales que ejecutaría un analista del MINSAL al usar el Dashboard v1.0,
golpeando la API tal como lo hace el frontend. Cada test representa una
historia de usuario y valida que el recorrido entrega información coherente.

Se siembra un dataset sintético determinista para que los escenarios devuelvan
resultados con significado (no respuestas vacías).

Personas / historias de usuario cubiertas:
  HU-1  Vista general: el analista abre el panel y ve los KPI nacionales.
  HU-2  Exploración geográfica: revisa el mapa y prioriza la comuna más crítica.
  HU-3  Segmentación: filtra por región y nivel de riesgo.
  HU-4  Tendencias: analiza la evolución temporal de la inseguridad alimentaria.
  HU-5  Focalización PACAM: identifica beneficiarios en riesgo que no retiran.
  HU-6  Ficha individual: abre el detalle de un adulto mayor priorizado.
  HU-7  Predicción: evalúa el riesgo de un nuevo caso clínico.
  HU-8  Recorrido completo del dashboard (smoke E2E de todos los paneles).
"""
import random

import pytest

from app.cache import clear_cache
from app.models import Hogar, Persona, IndicadorNutricional, ComunaResumen
from tests.conftest import TestingSessionLocal

COMUNAS = [
    ("07101", "Talca"),
    ("07401", "Linares"),
    ("07301", "Curicó"),
    ("07201", "Cauquenes"),
]


@pytest.fixture(scope="module", autouse=True)
def seed_uat():
    """Dataset sintético determinista para los escenarios del analista."""
    random.seed(7)
    db = TestingSessionLocal()
    try:
        # Partir de un estado limpio para que los escenarios sean deterministas
        # e independientes del orden de ejecución de otros módulos de test.
        db.query(IndicadorNutricional).delete()
        db.query(Persona).delete()
        db.query(Hogar).delete()
        db.query(ComunaResumen).delete()
        db.commit()

        # Resúmenes comunales con un claro "peor caso" (Cauquenes) para HU-2.
        comuna_riesgo = {
            "07101": 22.0, "07401": 31.0, "07301": 18.0, "07201": 47.5,
        }
        for cod, nombre in COMUNAS:
            db.add(ComunaResumen(
                comuna_cod=cod, comuna_nombre=nombre, region_cod="07",
                total_personas=120,
                pct_desnutricion=round(random.uniform(3, 8), 1),
                pct_riesgo_mna=round(random.uniform(15, 45), 1),
                pct_inseg_severa=round(random.uniform(4, 12), 1),
                n_benef_pacam=random.randint(20, 80),
                pct_no_retiro_pacam=round(random.uniform(20, 60), 1),
                n_critico=random.randint(2, 15), n_alto=random.randint(10, 40),
                pct_riesgo_alto_crit=comuna_riesgo[cod],
                nivel_riesgo_zona=(
                    "critico" if comuna_riesgo[cod] >= 40 else "alto"
                    if comuna_riesgo[cod] >= 25 else "medio"
                ),
            ))

        # Población sintética: 200 adultos mayores con riesgo e inseguridad.
        for _ in range(200):
            cod, _nombre = random.choice(COMUNAS)
            hogar = Hogar(
                region="07", comuna=cod,
                zona=random.choice(["urbano", "rural"]),
                ingreso_total=random.uniform(150_000, 800_000),
                quintil_ingreso=random.randint(1, 5),
                n_integrantes=random.randint(1, 4),
                acceso_pacam=random.random() < 0.5,
                acceso_rsh=random.random() < 0.7,
            )
            db.add(hogar)
            db.flush()

            persona = Persona(
                hogar_id=hogar.id,
                edad=random.randint(60, 95),
                sexo=random.choice(["M", "F"]),
                imc=round(random.uniform(17, 33), 1),
                tiene_diabetes=random.random() < 0.25,
                tiene_hipertension=random.random() < 0.5,
                tiene_depresion=random.random() < 0.2,
                vive_solo=random.random() < 0.35,
                puntaje_elcsa=random.randint(0, 15),
                nivel_inseguridad=random.choice(
                    ["seguro", "leve", "moderado", "severo"]
                ),
                fuente="SINTETICO",
            )
            db.add(persona)
            db.flush()

            db.add(IndicadorNutricional(
                persona_id=persona.id,
                nivel_riesgo=random.choices(
                    ["alto", "medio", "bajo"], weights=[3, 4, 3]
                )[0],
                probabilidad_riesgo=round(random.random(), 3),
                estado_nutricional=random.choice(
                    ["normal", "bajo peso", "obesidad"]
                ),
                factor_1="edad_avanzada",
            ))

        db.commit()
    finally:
        db.close()

    clear_cache()
    yield


# ─── HU-1 · Vista general (KPIs nacionales) ──────────────────
def test_hu1_analista_ve_kpis_generales(client):
    r = client.get("/api/v1/indicadores/resumen")
    assert r.status_code == 200
    data = r.json()
    assert data["total_adultos_mayores"] > 0
    # Los porcentajes clave del KPIStrip deben estar presentes y acotados.
    for campo in ("pct_riesgo_alto", "pct_beneficiarios_pacam",
                  "pct_inseguridad_alimentaria"):
        assert campo in data
        assert 0.0 <= float(data[campo]) <= 100.0


# ─── HU-2 · Exploración geográfica (priorizar comuna crítica) ─
def test_hu2_analista_prioriza_comuna_mas_critica(client):
    r = client.get("/api/v1/comunas/")
    assert r.status_code == 200
    comunas = r.json()["comunas"]
    # Aparecen todas las comunas con al menos una persona registrada (incluso
    # las de riesgo bajo); el % se recalcula en vivo sobre las personas.
    assert len(comunas) == len(COMUNAS)
    # La API ordena por pct_riesgo_alto_crit desc → la primera es la prioritaria.
    pcts = [c["pct_riesgo_alto_crit"] for c in comunas]
    assert pcts == sorted(pcts, reverse=True)
    top = comunas[0]
    assert top["nivel_riesgo_zona"] in ("critico", "alto", "medio", "bajo")
    assert top["total_personas"] > 0

    # El analista abre el detalle de esa comuna (clic en el mapa).
    detalle = client.get(f"/api/v1/comunas/{top['comuna_cod']}")
    assert detalle.status_code == 200
    assert detalle.json()["comuna_cod"] == top["comuna_cod"]


# ─── HU-3 · Segmentación (filtros región + riesgo) ───────────
def test_hu3_analista_filtra_por_region_y_riesgo(client):
    # Filtro por región en estadísticas.
    stats = client.get("/api/v1/indicadores/stats?region=07")
    assert stats.status_code == 200
    body = stats.json()
    assert body["hay_datos"] is True
    assert len(body["distribucion_riesgo"]) >= 1

    # Filtro por nivel de riesgo en el listado de comunas.
    criticas = client.get("/api/v1/comunas/?nivel_riesgo=critico")
    assert criticas.status_code == 200
    for c in criticas.json()["comunas"]:
        assert c["nivel_riesgo_zona"] == "critico"


# ─── HU-4 · Tendencias temporales ────────────────────────────
def test_hu4_analista_revisa_tendencias(client):
    r = client.get("/api/v1/indicadores/tendencias?meses=6")
    assert r.status_code == 200
    serie = r.json()["serie"]
    assert len(serie) >= 3
    for punto in serie:
        assert "mes" in punto
        assert "pct_inseg_moderada_severa" in punto


# ─── HU-5 · Focalización PACAM (no retiran) ──────────────────
def test_hu5_analista_focaliza_no_retiran_pacam(client):
    r = client.get("/api/v1/beneficiarios/?no_retira_pacam=true")
    assert r.status_code == 200
    data = r.json()
    assert "total" in data and "items" in data
    # Todos los resultados deben cumplir el criterio (PACAM + riesgo alto/medio).
    for item in data["items"]:
        assert item["acceso_pacam"] in (True, 1)
        assert item["nivel_riesgo"] in ("alto", "medio")


# ─── HU-6 · Ficha individual del adulto mayor ────────────────
def test_hu6_analista_abre_ficha_individual(client):
    lista = client.get("/api/v1/beneficiarios/?page=1&page_size=1")
    assert lista.status_code == 200
    items = lista.json()["items"]
    assert len(items) == 1
    pid = items[0]["id"]

    ficha = client.get(f"/api/v1/beneficiarios/{pid}")
    assert ficha.status_code == 200
    detalle = ficha.json()
    assert detalle["id"] == pid
    # Campos que muestra la vista PatientDetail.
    for campo in ("edad", "sexo", "imc", "nivel_riesgo", "region"):
        assert campo in detalle


# ─── HU-7 · Predicción de un nuevo caso clínico ──────────────
def test_hu7_analista_evalua_nuevo_caso(client):
    caso = {
        "edad": 82, "sexo": "F", "zona": "rural",
        "imc": 18.0, "circ_pantorrilla": 28.5, "inseg_alimentaria": 3,
        "depresion": True, "vive_solo": True, "acceso_pacam": False,
    }
    r = client.post("/api/v1/prediccion/", json=caso)
    assert r.status_code == 200
    pred = r.json()
    assert pred["riesgo"] in ("bajo", "medio", "alto", "critico")
    assert 0.0 <= pred["probabilidad"] <= 1.0
    assert isinstance(pred["factores_principales"], list)


# ─── HU-8 · Recorrido completo del Dashboard v1.0 ────────────
def test_hu8_recorrido_completo_dashboard(client):
    """Smoke E2E: todos los paneles del dashboard responden 200."""
    recorrido = [
        ("GET", "/api/v1/indicadores/resumen"),     # KPIStrip
        ("GET", "/api/v1/comunas/"),                 # MapPanel
        ("GET", "/api/v1/indicadores/tendencias"),   # TendenciasChart
        ("GET", "/api/v1/indicadores/stats"),        # StatsPanel
        ("GET", "/api/v1/prediccion/info"),          # PredictionPanel
        ("GET", "/api/v1/beneficiarios/"),           # NonRetirers
    ]
    for metodo, url in recorrido:
        resp = client.request(metodo, url)
        assert resp.status_code == 200, f"Falló {metodo} {url}"
