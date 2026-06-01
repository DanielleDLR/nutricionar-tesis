"""
Pruebas unitarias del backend (S14 · Carta Gantt).

Cubren componentes aislados que no se ejercían en test_main.py:
- Caché TTL en memoria (app/cache.py): hit/miss, expiración, limpieza.
- Ingeniería de features (ml/features.py): codificación y robustez.
- Heurística de fallback del modelo (ml/predict.py): clasificación clínica.
- Casos de borde de endpoints: paginación, filtros y validación.
"""
import time

from app.cache import cache_get, cache_set, clear_cache, cache_stats
from ml.features import FEATURE_NAMES, build_feature_vector, INSEG_MAP
from ml.predict import _heuristic_predict


# ─── Caché TTL ───────────────────────────────────────────────
class TestCache:
    def setup_method(self):
        clear_cache()

    def test_miss_devuelve_none(self):
        assert cache_get("inexistente") is None

    def test_set_get_hit(self):
        cache_set("k", {"v": 1}, ttl=10)
        assert cache_get("k") == {"v": 1}

    def test_expiracion(self):
        cache_set("k", 123, ttl=1)
        assert cache_get("k") == 123
        # Forzar expiración con un TTL muy corto
        cache_set("k2", 9, ttl=0)
        time.sleep(0.01)
        assert cache_get("k2") is None

    def test_clear(self):
        cache_set("a", 1, ttl=10)
        cache_set("b", 2, ttl=10)
        clear_cache()
        assert cache_get("a") is None
        assert cache_get("b") is None

    def test_stats(self):
        clear_cache()
        cache_set("a", 1, ttl=10)
        stats = cache_stats()
        assert stats["entradas"] == 1
        assert stats["vigentes"] == 1


# ─── Ingeniería de features ──────────────────────────────────
class TestFeatures:
    def test_longitud_vector(self):
        vec = build_feature_vector({})
        assert len(vec) == len(FEATURE_NAMES) == 18

    def test_sexo_femenino_codifica_1(self):
        vec = build_feature_vector({"sexo": "F"})
        assert vec[FEATURE_NAMES.index("sexo_num")] == 1.0

    def test_sexo_masculino_codifica_0(self):
        vec = build_feature_vector({"sexo": "M"})
        assert vec[FEATURE_NAMES.index("sexo_num")] == 0.0

    def test_zona_rural_codifica_1(self):
        vec = build_feature_vector({"zona": "rural"})
        assert vec[FEATURE_NAMES.index("zona_num")] == 1.0

    def test_inseg_textual_se_mapea(self):
        assert INSEG_MAP["severo"] == 3
        vec = build_feature_vector({"inseg_alimentaria": "severo"})
        assert vec[FEATURE_NAMES.index("inseg_alimentaria")] == 3.0

    def test_valores_invalidos_usan_fallback(self):
        # Un IMC no numérico no debe romper la construcción del vector
        vec = build_feature_vector({"imc": "no-numerico", "edad": None})
        assert len(vec) == 18
        assert all(v == v for v in vec)  # sin NaN


# ─── Heurística de fallback del modelo ───────────────────────
class TestHeuristica:
    def test_caso_alto_riesgo(self):
        """MNA bajo + IMC bajo + inseguridad severa → alto/critico."""
        nivel, prob, factores = _heuristic_predict({
            "puntaje_mna": 15, "imc": 17.0, "inseg_alimentaria": "severo",
            "depresion": True, "vive_solo": True,
        })
        assert nivel in ("alto", "critico")
        assert prob > 0.3
        assert "puntaje_mna_bajo" in factores

    def test_caso_bajo_riesgo(self):
        """Persona sana, bien nutrida → riesgo bajo."""
        nivel, prob, factores = _heuristic_predict({
            "puntaje_mna": 28, "imc": 25.0, "inseg_alimentaria": 0,
        })
        assert nivel == "bajo"
        assert prob < 0.15

    def test_probabilidad_acotada(self):
        nivel, prob, factores = _heuristic_predict({
            "puntaje_mna": 5, "imc": 14, "inseg_alimentaria": "severo",
            "depresion": True, "limitacion_fisica": True,
            "diabetes": True, "vive_solo": True,
        })
        assert 0.0 <= prob <= 1.0
        assert len(factores) <= 5


# ─── Casos de borde de endpoints ─────────────────────────────
class TestEndpointsBorde:
    def test_beneficiarios_paginacion(self, client):
        r = client.get("/api/v1/beneficiarios/?page=2&page_size=5")
        assert r.status_code == 200
        data = r.json()
        assert data["page"] == 2
        assert data["page_size"] == 5

    def test_beneficiarios_page_size_invalido(self, client):
        # page_size > 100 debe fallar la validación (422)
        r = client.get("/api/v1/beneficiarios/?page_size=500")
        assert r.status_code == 422

    def test_comunas_filtro_region(self, client):
        r = client.get("/api/v1/comunas/?region_cod=07")
        assert r.status_code == 200
        assert "comunas" in r.json()

    def test_stats_filtro_region(self, client):
        r = client.get("/api/v1/indicadores/stats?region=07")
        assert r.status_code == 200
        assert "distribucion_riesgo" in r.json()

    def test_resumen_cacheado_consistente(self, client):
        """Dos llamadas consecutivas a /resumen devuelven el mismo payload."""
        r1 = client.get("/api/v1/indicadores/resumen")
        r2 = client.get("/api/v1/indicadores/resumen")
        assert r1.status_code == r2.status_code == 200
        assert r1.json() == r2.json()

    def test_tendencias_rango_invalido(self, client):
        # meses fuera de [3,24] debe fallar
        r = client.get("/api/v1/indicadores/tendencias?meses=99")
        assert r.status_code == 422

    def test_prediccion_edad_invalida(self, client):
        # edad < 60 viola la restricción ge=60
        r = client.post("/api/v1/prediccion/", json={"edad": 30, "sexo": "F"})
        assert r.status_code == 422
