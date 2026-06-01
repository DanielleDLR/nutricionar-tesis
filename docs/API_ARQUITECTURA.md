# Documentación de API y Arquitectura — NutricioNar

> **Versión:** v1.0 · **Tesis de Magíster · Daniela Lavanderos · 2025–2026**

Este documento describe la arquitectura de la plataforma y el contrato
completo de su API REST.

---

## 1. Arquitectura general

NutricioNar sigue una arquitectura cliente–servidor de tres capas,
contenerizada con Docker:

```
┌──────────────────────┐      HTTP/JSON      ┌──────────────────────┐
│   Frontend (SPA)     │  ───────────────▶   │   Backend (API REST) │
│  React 18 + Vite     │                     │   FastAPI · Python    │
│  Leaflet · Router    │  ◀───────────────   │   SQLAlchemy ORM      │
└──────────────────────┘                     └───────────┬──────────┘
                                                          │ SQL
                                              ┌───────────▼──────────┐
                                              │  PostgreSQL 15       │
                                              │  hogares · personas  │
                                              │  indicadores · comunas│
                                              └──────────────────────┘
                                                          ▲
                                              ┌───────────┴──────────┐
                                              │  Modelo ML (pickle)  │
                                              │  RandomForest + medians│
                                              └──────────────────────┘
```

### 1.1 Componentes

| Componente | Tecnología | Responsabilidad |
|------------|-----------|-----------------|
| **Frontend** | React 18.3 + Vite 5 + React Router 6 + Leaflet 1.9 | SPA del dashboard, mapas y formularios. |
| **Backend** | Python 3.11 + FastAPI | API REST, lógica de agregación y servicio del modelo. |
| **Base de datos** | PostgreSQL 15 (SQLite en tests) | Persistencia relacional. |
| **Modelo ML** | scikit-learn RandomForestClassifier | Predicción de riesgo nutricional. |
| **Orquestación** | Docker Compose | Levanta backend + BD + frontend. |
| **CI/CD** | GitHub Actions | Lint (flake8), tests (pytest), build Docker. |

### 1.2 Estructura del backend

```
backend/
├── app/
│   ├── main.py            # App FastAPI, middlewares (CORS, GZip), routers
│   ├── database.py        # Engine, SessionLocal, get_db()
│   ├── cache.py           # Caché TTL en memoria (rendimiento)
│   ├── models/            # ORM: Hogar, Persona, IndicadorNutricional, ComunaResumen
│   └── routers/           # indicadores, beneficiarios, comunas, prediccion
├── ml/
│   ├── features.py        # Ingeniería de 18 features
│   ├── predict.py         # Inferencia + fallback heurístico
│   └── artefactos/        # modelo_rf.pkl, medians.pkl, metrics.json
├── scripts/               # ETL y utilidades (load_dataset, train_model...)
└── tests/                 # pytest: main, unit, load, user_acceptance
```

### 1.3 Decisiones de rendimiento

- **GZipMiddleware**: comprime respuestas JSON mayores a 500 bytes.
- **Caché TTL** (`app/cache.py`): los endpoints de agregación `/resumen` y
  `/stats` cachean su resultado durante `CACHE_TTL_SECONDS` (30 s por
  defecto), reduciendo JOINs repetidos sobre la base de datos.
- **`lru_cache`** en la carga del modelo ML (se deserializa una sola vez).
- **Índices** en columnas de filtro frecuente (`region`, `comuna`,
  `comuna_cod`, claves foráneas).

---

## 2. Modelo de datos

| Tabla | Descripción | Campos clave |
|-------|-------------|--------------|
| `hogares` | Hogar y características socioeconómicas. | `region`, `comuna`, `zona`, `quintil_ingreso`, `acceso_pacam`, `acceso_rsh` |
| `personas` | Adulto mayor (1..N por hogar). | `hogar_id` (FK), `edad`, `sexo`, `imc`, comorbilidades, `nivel_inseguridad` |
| `indicadores_nutricionales` | Salida del modelo por persona. | `persona_id` (FK), `nivel_riesgo`, `probabilidad_riesgo`, `estado_nutricional`, `fecha_calculo` |
| `comunas_resumen` | Estadísticas agregadas por comuna. | `comuna_cod` (UNIQUE), `pct_riesgo_alto_crit`, `nivel_riesgo_zona`, `pct_no_retiro_pacam` |

Relación: `hogares 1—N personas 1—N indicadores_nutricionales`.

---

## 3. Convenciones de la API

- **Base URL:** `http://localhost:8000`
- **Prefijo de versión:** `/api/v1`
- **Formato:** JSON (UTF-8). Respuestas comprimidas con GZip cuando aplica.
- **CORS:** habilitado para `http://localhost:5173` y `http://localhost:3000`.
- **Errores:** códigos HTTP estándar. `404` recurso no encontrado, `422`
  validación de entrada (Pydantic), `200` éxito.

---

## 4. Endpoints

### 4.1 Salud

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/` | Estado general (`{"status":"ok"}`). |
| `GET` | `/health` | Healthcheck (`{"status":"healthy"}`). |

### 4.2 Indicadores — `/api/v1/indicadores`

| Método | Ruta | Parámetros | Descripción |
|--------|------|-----------|-------------|
| `GET` | `/` | `region`, `zona` | Indicadores agregados desde la vista resumen regional. |
| `GET` | `/resumen` | — | Totales nacionales (KPIs). **Cacheado.** |
| `GET` | `/stats` | `region` | Distribuciones: riesgo, inseguridad, comorbilidades, quintil. **Cacheado.** |
| `GET` | `/tendencias` | `meses` (3–24, def. 6), `region` | Evolución mensual de indicadores. |

**Ejemplo — `GET /api/v1/indicadores/resumen`:**
```json
{
  "total_adultos_mayores": 1200,
  "pct_riesgo_alto": 28.4,
  "pct_beneficiarios_pacam": 41.2,
  "pct_inseguridad_alimentaria": 11.0
}
```

### 4.3 Comunas — `/api/v1/comunas`

| Método | Ruta | Parámetros | Descripción |
|--------|------|-----------|-------------|
| `GET` | `/` | `region_cod`, `nivel_riesgo` | Lista de comunas ordenadas por `pct_riesgo_alto_crit` desc. |
| `GET` | `/{comuna_cod}` | — | Detalle de una comuna. `404` si no existe. |

**Ejemplo — `GET /api/v1/comunas/?nivel_riesgo=critico`:**
```json
{
  "total": 1,
  "comunas": [
    {
      "comuna_cod": "07201",
      "comuna_nombre": "Cauquenes",
      "region_cod": "07",
      "total_personas": 120,
      "pct_riesgo_alto_crit": 47.5,
      "nivel_riesgo_zona": "critico"
    }
  ]
}
```

### 4.4 Beneficiarios — `/api/v1/beneficiarios`

| Método | Ruta | Parámetros | Descripción |
|--------|------|-----------|-------------|
| `GET` | `/` | `region`, `riesgo`, `zona`, `no_retira_pacam`, `page` (≥1), `page_size` (1–100) | Lista paginada de adultos mayores. |
| `GET` | `/{beneficiario_id}` | — | Ficha individual completa. `404` si no existe. |

`no_retira_pacam=true` filtra beneficiarios PACAM con riesgo alto o medio.

### 4.5 Predicción ML — `/api/v1/prediccion`

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/info` | Metadatos y métricas del modelo cargado. |
| `POST` | `/` | Predice el riesgo nutricional de un caso. |

**Entrada (`POST /api/v1/prediccion/`):**
```json
{
  "edad": 82, "sexo": "F", "zona": "rural",
  "imc": 18.0, "puntaje_mna": 16, "inseg_alimentaria": 3,
  "depresion": true, "vive_solo": true, "acceso_pacam": false
}
```

**Salida:**
```json
{
  "riesgo": "alto",
  "probabilidad": 0.78,
  "factores_principales": ["puntaje_mna", "imc", "inseg_alimentaria"],
  "probabilidades": [{"nivel": "alto", "probabilidad": 0.78}],
  "modelo": "RandomForestClassifier",
  "usa_fallback": false
}
```

> Si los artefactos del modelo no están disponibles, el endpoint responde con
> `usa_fallback: true` aplicando una heurística clínica basada en reglas MNA.

---

## 5. Modelo de Machine Learning

- **Algoritmo:** RandomForestClassifier (scikit-learn).
- **Features:** 18 variables (sociodemográficas, antropométricas,
  comorbilidades, inseguridad alimentaria, acceso a programas) — ver
  `ml/features.py`.
- **Variable objetivo:** `nivel_riesgo` (4 clases: bajo, medio, alto, crítico).
- **Entrenamiento:** dataset sintético piloto (N≈1.200). F1-macro CV 5-fold
  ≈ 0.81.
- **Inferencia:** `ml/predict.py` carga el modelo con `lru_cache`, construye
  el vector de features y devuelve nivel, probabilidad y factores por
  importancia. Incluye fallback heurístico.

---

## 6. Pruebas

| Suite | Cobertura |
|-------|-----------|
| `tests/test_main.py` | Endpoints principales y validaciones. |
| `tests/test_unit.py` | Caché TTL, ingeniería de features, heurística, casos de borde. |
| `tests/test_load.py` | Pruebas de carga concurrente con dataset sintético (latencia p50/p95/p99, throughput). |
| `tests/test_user_acceptance.py` | Pruebas de usuario (8 historias del analista MINSAL). |

Ejecución: `pytest tests/ -v`. La configuración de tests usa SQLite en
memoria y recrea la vista `vista_resumen_regional` adaptada.

---

## 7. Configuración y despliegue

Variables de entorno relevantes:

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `DATABASE_URL` | Cadena de conexión a la BD. | `postgresql://postgres:postgres@localhost:5432/nutricionar` |
| `CACHE_TTL_SECONDS` | TTL del caché de agregados. | `30` |
| `VITE_API_URL` | URL base de la API para el frontend. | `http://localhost:8000` |

Despliegue local: `docker-compose up --build`. La documentación interactiva
de la API queda disponible en `/docs` (Swagger UI) y `/redoc`.
