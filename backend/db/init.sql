-- ============================================================
-- NutricioNar — Esquema relacional inicial
-- Base de datos: nutricionar (PostgreSQL 15)
-- ============================================================

-- Extensiones
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ────────────────────────────────────────────────────────────
-- TABLA: hogares
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS hogares (
    id                  SERIAL PRIMARY KEY,
    region              CHAR(2)         NOT NULL,
    provincia           CHAR(3),
    comuna              CHAR(5),
    zona                VARCHAR(10)     CHECK (zona IN ('urbano', 'rural')),
    ingreso_total       NUMERIC(12, 2),
    quintil_ingreso     SMALLINT        CHECK (quintil_ingreso BETWEEN 1 AND 5),
    n_integrantes       SMALLINT,
    hacinamiento        BOOLEAN         DEFAULT FALSE,
    acceso_pacam        BOOLEAN         DEFAULT FALSE,
    acceso_rsh          BOOLEAN         DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_hogares_region  ON hogares(region);
CREATE INDEX IF NOT EXISTS idx_hogares_comuna  ON hogares(comuna);

-- ────────────────────────────────────────────────────────────
-- TABLA: personas
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS personas (
    id                          SERIAL PRIMARY KEY,
    hogar_id                    INTEGER         NOT NULL REFERENCES hogares(id) ON DELETE CASCADE,
    edad                        SMALLINT        NOT NULL CHECK (edad >= 60),
    sexo                        CHAR(1)         NOT NULL CHECK (sexo IN ('M', 'F')),
    fecha_nacimiento            DATE,
    estado_civil                VARCHAR(20),
    escolaridad                 VARCHAR(50),
    vive_solo                   BOOLEAN         DEFAULT FALSE,

    -- Antropometría
    peso_kg                     NUMERIC(5, 2),
    talla_cm                    NUMERIC(5, 2),
    imc                         NUMERIC(5, 2),
    circunferencia_pantorrilla  NUMERIC(5, 2),

    -- Morbilidades
    tiene_diabetes              BOOLEAN         DEFAULT FALSE,
    tiene_hipertension          BOOLEAN         DEFAULT FALSE,
    tiene_depresion             BOOLEAN         DEFAULT FALSE,

    -- Seguridad alimentaria
    puntaje_elcsa               SMALLINT        CHECK (puntaje_elcsa BETWEEN 0 AND 15),
    nivel_inseguridad           VARCHAR(10)     CHECK (nivel_inseguridad IN ('seguro', 'leve', 'moderado', 'severo')),

    -- Metadatos
    fuente                      VARCHAR(20)     CHECK (fuente IN ('CASEN', 'ENS', 'SINTETICO')),
    anio_encuesta               SMALLINT
);

CREATE INDEX IF NOT EXISTS idx_personas_hogar_id ON personas(hogar_id);
CREATE INDEX IF NOT EXISTS idx_personas_edad     ON personas(edad);
CREATE INDEX IF NOT EXISTS idx_personas_fuente   ON personas(fuente);

-- ────────────────────────────────────────────────────────────
-- TABLA: indicadores_nutricionales
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS indicadores_nutricionales (
    id                      SERIAL PRIMARY KEY,
    persona_id              INTEGER         NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    nivel_riesgo            VARCHAR(10)     NOT NULL CHECK (nivel_riesgo IN ('alto', 'medio', 'bajo')),
    probabilidad_riesgo     NUMERIC(5, 4)   CHECK (probabilidad_riesgo BETWEEN 0 AND 1),
    estado_nutricional      VARCHAR(20),
    riesgo_sarcopenia       VARCHAR(10),
    riesgo_desnutricion     VARCHAR(10),
    factor_1                VARCHAR(50),
    factor_2                VARCHAR(50),
    factor_3                VARCHAR(50),
    modelo_version          VARCHAR(20),
    fecha_calculo           TIMESTAMP       DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_indicadores_persona_id   ON indicadores_nutricionales(persona_id);
CREATE INDEX IF NOT EXISTS idx_indicadores_nivel_riesgo ON indicadores_nutricionales(nivel_riesgo);

-- ────────────────────────────────────────────────────────────
-- TABLA: comunas_resumen
-- Resumen estadístico precalculado por comuna (Región del Maule)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS comunas_resumen (
    id                      SERIAL PRIMARY KEY,
    comuna_cod              CHAR(5)         NOT NULL UNIQUE,
    comuna_nombre           VARCHAR(100)    NOT NULL,
    region_cod              CHAR(2)         NOT NULL,
    total_personas          INTEGER         DEFAULT 0,
    n_desnutricion          INTEGER         DEFAULT 0,
    n_riesgo                INTEGER         DEFAULT 0,
    n_normal                INTEGER         DEFAULT 0,
    pct_desnutricion        NUMERIC(5,2)    DEFAULT 0.0,
    pct_riesgo_mna          NUMERIC(5,2)    DEFAULT 0.0,
    pct_inseg_severa        NUMERIC(5,2)    DEFAULT 0.0,
    pct_inseg_mod_sev       NUMERIC(5,2)    DEFAULT 0.0,
    n_benef_pacam           INTEGER         DEFAULT 0,
    pct_no_retiro_pacam     NUMERIC(5,2)    DEFAULT 0.0,
    n_critico               INTEGER         DEFAULT 0,
    n_alto                  INTEGER         DEFAULT 0,
    pct_riesgo_alto_crit    NUMERIC(5,2)    DEFAULT 0.0,
    nivel_riesgo_zona       VARCHAR(20)
);

CREATE INDEX IF NOT EXISTS idx_comunas_region_cod ON comunas_resumen(region_cod);

-- ────────────────────────────────────────────────────────────
-- VISTA: resumen por región (útil para el dashboard)
-- ────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vista_resumen_regional AS
SELECT
    h.region,
    h.zona,
    COUNT(DISTINCT p.id)                                    AS total_adultos_mayores,
    ROUND(AVG(p.imc)::NUMERIC, 2)                          AS imc_promedio,
    ROUND(100.0 * SUM(CASE WHEN i.nivel_riesgo = 'alto'  THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_riesgo_alto,
    ROUND(100.0 * SUM(CASE WHEN i.nivel_riesgo = 'medio' THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_riesgo_medio,
    ROUND(100.0 * SUM(CASE WHEN i.nivel_riesgo = 'bajo'  THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_riesgo_bajo,
    ROUND(100.0 * SUM(CASE WHEN h.acceso_pacam = TRUE    THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_beneficiarios_pacam,
    ROUND(100.0 * SUM(CASE WHEN p.nivel_inseguridad IN ('moderado', 'severo') THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_inseguridad_alimentaria
FROM hogares h
JOIN personas p                  ON p.hogar_id = h.id
JOIN indicadores_nutricionales i ON i.persona_id = p.id
GROUP BY h.region, h.zona;
