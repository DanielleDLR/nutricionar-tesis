# NutricioNar — Plataforma Predictiva de Riesgo de Desnutrición en Adultos Mayores (Chile)

> Proyecto de Título · Ingeniería Civil Informática · Daniela Lavanderos · 2026

## Descripción

NutricioNar es una plataforma web interactiva que permite visualizar y predecir el riesgo de desnutrición en adultos mayores en Chile, a partir de datos de la Encuesta CASEN 2022, ENS 2016-2017 y registros del MINSAL. El piloto se desarrolla en la Región del Maule.

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend | React 18 + Vite + React Router + Leaflet |
| Backend | Python 3.11 + FastAPI |
| Base de datos | PostgreSQL 15 |
| Contenerización | Docker + Docker Compose |
| CI/CD | GitHub Actions |

## Estructura del repositorio

```
nutricionar-tesis/
├── .github/
│   └── workflows/
│       └── ci.yml          # Pipeline CI/CD
├── backend/
│   ├── app/
│   │   ├── main.py         # Entrada FastAPI
│   │   ├── routers/        # Endpoints REST
│   │   ├── models/         # Modelos ORM
│   │   └── schemas/        # Esquemas Pydantic
│   ├── Dockerfile
│   └── requirements.txt
├── nutricionar/             # Frontend React/Vite
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── data/                    # Datasets (excluidos del repo por .gitignore)
├── docker-compose.yml
└── README.md
```

## Cómo levantar el proyecto localmente

### Requisitos previos
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo
- [Git](https://git-scm.com/) instalado

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/nutricionar-tesis.git
cd nutricionar-tesis

# 2. Levantar todos los servicios
docker-compose up --build

# 3. Acceder a la aplicación
#    Frontend:  http://localhost:5173
#    Backend:   http://localhost:8000
#    API Docs:  http://localhost:8000/docs
```

### Desarrollo sin Docker

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (en otra terminal)
cd nutricionar
npm install
npm run dev
```

## Variables de entorno

Crea un archivo `.env` en la raíz del proyecto (no se sube al repo):

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/nutricionar
SECRET_KEY=cambia_esto_en_produccion
ENVIRONMENT=development
```

## CI/CD

Cada push a `main` o `develop` activa automáticamente:
1. **Lint** — `flake8` (Python) y `eslint` (JavaScript)
2. **Tests** — `pytest` (backend)
3. **Build** — Construcción de imagen Docker del frontend

## Datos

Los archivos de datos (`data/`) están excluidos del repositorio por razones de privacidad y tamaño. Ver `data/Mapa de datos.xlsx` para el inventario de fuentes.

## Licencia

Uso académico — Tesis Universidad. Todos los derechos reservados.
