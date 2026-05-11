def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_indicadores_retorna_estructura(client):
    response = client.get("/api/v1/indicadores/")
    assert response.status_code == 200
    data = response.json()
    assert "filtros" in data
    assert "datos" in data


def test_indicadores_con_filtro_region(client):
    response = client.get("/api/v1/indicadores/?region=07")
    assert response.status_code == 200
    data = response.json()
    assert data["filtros"]["region"] == "07"


def test_indicadores_resumen(client):
    response = client.get("/api/v1/indicadores/resumen")
    assert response.status_code == 200


def test_beneficiarios_retorna_estructura(client):
    response = client.get("/api/v1/beneficiarios/")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_beneficiario_no_encontrado(client):
    response = client.get("/api/v1/beneficiarios/99999")
    assert response.status_code == 404


def test_comunas_retorna_estructura(client):
    response = client.get("/api/v1/comunas/")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "comunas" in data
    assert isinstance(data["comunas"], list)


def test_comuna_no_encontrada(client):
    response = client.get("/api/v1/comunas/99999")
    assert response.status_code == 404


def test_prediccion(client):
    payload = {
        "edad": 72,
        "sexo": "F",
        "region": "07",
        "imc": 21.5,
        "ingreso_per_capita": 350000,
        "acceso_pacam": True,
        "vive_solo": False,
    }
    response = client.post("/api/v1/prediccion/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["riesgo"] in ["bajo", "medio", "alto", "critico"]
    assert 0.0 <= data["probabilidad"] <= 1.0
    assert isinstance(data["factores_principales"], list)
    assert isinstance(data["usa_fallback"], bool)


def test_prediccion_campos_requeridos(client):
    """Falta 'sexo' requerido debe devolver 422."""
    response = client.post("/api/v1/prediccion/", json={"edad": 70})
    assert response.status_code == 422


def test_prediccion_info(client):
    response = client.get("/api/v1/prediccion/info")
    assert response.status_code == 200
    data = response.json()
    assert "modelo_disponible" in data
    assert "n_features" in data
    assert data["n_features"] == 18
