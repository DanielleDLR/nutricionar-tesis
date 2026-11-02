-- ============================================================
-- Migración: soporte para la clase 'critico' + fuente CASEN_ENS_REAL
-- + vista actualizada
-- ============================================================
-- El modelo predice 4 clases (bajo/medio/alto/critico), pero el
-- esquema original solo permitía 3 en indicadores_nutricionales.
-- Además, personas.fuente solo permitía 'CASEN'/'ENS'/'SINTETICO':
-- scripts/load_real_data.py inserta 'CASEN_ENS_REAL' y violaría ese
-- CHECK constraint en una base ya desplegada si no se aplica esta
-- migración (bug detectado al integrar el dataset real del Maule).
-- Ejecutar UNA VEZ sobre una base ya desplegada con db/init.sql
-- (si la base es nueva, basta con init.sql, que ya incluye esto).
--
-- Uso:
--   psql -U postgres -d nutricionar -f db/migrate_critico.sql

ALTER TABLE indicadores_nutricionales
    DROP CONSTRAINT IF EXISTS indicadores_nutricionales_nivel_riesgo_check;

ALTER TABLE indicadores_nutricionales
    ADD CONSTRAINT indicadores_nutricionales_nivel_riesgo_check
    CHECK (nivel_riesgo IN ('critico', 'alto', 'medio', 'bajo'));

ALTER TABLE personas
    DROP CONSTRAINT IF EXISTS personas_fuente_check;

ALTER TABLE personas
    ADD CONSTRAINT personas_fuente_check
    CHECK (fuente IN ('CASEN', 'ENS', 'SINTETICO', 'CASEN_ENS_REAL'));

CREATE OR REPLACE VIEW vista_resumen_regional AS
SELECT
    h.region,
    h.zona,
    COUNT(DISTINCT p.id)                                    AS total_adultos_mayores,
    ROUND(AVG(p.imc)::NUMERIC, 2)                          AS imc_promedio,
    ROUND(100.0 * SUM(CASE WHEN i.nivel_riesgo = 'critico' THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_riesgo_critico,
    ROUND(100.0 * SUM(CASE WHEN i.nivel_riesgo = 'alto'  THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_riesgo_alto,
    ROUND(100.0 * SUM(CASE WHEN i.nivel_riesgo = 'medio' THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_riesgo_medio,
    ROUND(100.0 * SUM(CASE WHEN i.nivel_riesgo = 'bajo'  THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_riesgo_bajo,
    ROUND(100.0 * SUM(CASE WHEN h.acceso_pacam = TRUE    THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_beneficiarios_pacam,
    ROUND(100.0 * SUM(CASE WHEN p.nivel_inseguridad IN ('moderado', 'severo') THEN 1 ELSE 0 END) / COUNT(p.id), 2) AS pct_inseguridad_alimentaria
FROM hogares h
JOIN personas p                  ON p.hogar_id = h.id
JOIN indicadores_nutricionales i ON i.persona_id = p.id
GROUP BY h.region, h.zona;
