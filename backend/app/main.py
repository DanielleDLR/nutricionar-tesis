from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.routers import indicadores, beneficiarios, prediccion, comunas

app = FastAPI(
    title="NutricioNar API",
    description="API REST — Plataforma Predictiva de Riesgo de Desnutrición en Adultos Mayores",
    version="0.1.0",
)

# Compresión GZip de respuestas (>500 bytes) para reducir el payload de los
# endpoints de datos y mejorar el tiempo de transferencia (S14 · rendimiento).
app.add_middleware(GZipMiddleware, minimum_size=500)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(indicadores.router, prefix="/api/v1/indicadores", tags=["Indicadores"])
app.include_router(beneficiarios.router, prefix="/api/v1/beneficiarios", tags=["Beneficiarios"])
app.include_router(prediccion.router, prefix="/api/v1/prediccion", tags=["Predicción ML"])
app.include_router(comunas.router, prefix="/api/v1/comunas", tags=["Comunas"])


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "NutricioNar API corriendo"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
