import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Base de datos SQLite en memoria para tests (sin necesitar PostgreSQL)
TEST_DATABASE_URL = "sqlite:///./test.db"

engine_test = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Crea las tablas antes de los tests y las elimina al terminar."""
    Base.metadata.create_all(bind=engine_test)

    # Crear la vista manualmente adaptada a SQLite
    with engine_test.connect() as conn:
        conn.execute(text("""
            CREATE VIEW IF NOT EXISTS vista_resumen_regional AS
            SELECT
                h.region,
                h.zona,
                COUNT(DISTINCT p.id)    AS total_adultos_mayores,
                AVG(p.imc)              AS imc_promedio,
                0.0                     AS pct_riesgo_alto,
                0.0                     AS pct_riesgo_medio,
                0.0                     AS pct_riesgo_bajo,
                0.0                     AS pct_beneficiarios_pacam,
                0.0                     AS pct_inseguridad_alimentaria
            FROM hogares h
            JOIN personas p                  ON p.hogar_id = h.id
            JOIN indicadores_nutricionales i ON i.persona_id = p.id
            GROUP BY h.region, h.zona
        """))
        conn.commit()

    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine_test)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)
