-- ============================================================
-- Migración: columnas REM P5 (Vigilancia Nutricional MINSAL) en comunas_resumen
-- ============================================================
-- Agrega el registro administrativo oficial de personas mayores en control
-- (indicadores 7.3 bajo peso / 7.4 normal, REM P5) como columnas estáticas
-- por comuna, independientes del dataset CASEN/ENS/sintético cargado en
-- personas/hogares/indicadores_nutricionales.
-- Ejecutar UNA VEZ sobre una base ya desplegada con db/init.sql
-- (si la base es nueva, basta con init.sql, que ya incluye esto).
--
-- Uso:
--   psql -U postgres -d nutricionar -f db/migrate_rem.sql
--   python scripts/load_rem_comunas.py --file data_real/rem_p5_nutricional_maule_2026.csv

ALTER TABLE comunas_resumen ADD COLUMN IF NOT EXISTS n_control_rem     INTEGER;
ALTER TABLE comunas_resumen ADD COLUMN IF NOT EXISTS pct_normal_rem    NUMERIC(5,2);
ALTER TABLE comunas_resumen ADD COLUMN IF NOT EXISTS pct_bajo_peso_rem NUMERIC(5,2);
