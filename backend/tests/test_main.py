from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_indicadores():
    response = client.get("/api/v1/indicadores/")
    assert response.status_code == 200
    data = response.json()
    assert "indicadores" in data


def test_indicadores_con_filtros():
    response = client.get("/api/v1/indicadores/?region=07&grupo_etario=60-74")
    assert response.status_code == 200
    data = response.json()
    assert data["region"] == "07"


def test_prediccion():
    payload = {
        "edad": 72,
        "sexo": "F",
        "region": "07",
        "imc": 21.5,
        "ingreso_hogar": 350000,
        "acceso_pacam": True,
        "vive_solo": False,
    }
    response = client.post("/api/v1/prediccion/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["riesgo"] in ["alto", "medio", "bajo"]
    assert 0.0 <= data["probabilidad"] <= 1.0
