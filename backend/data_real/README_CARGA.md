# Cargar datos reales del Maule — guía rápida

Este documento resume los pasos para desplegar los cambios de esta sesión
sobre una instancia de PostgreSQL real. Todo fue probado end-to-end contra
una base SQLite equivalente (no hay Postgres disponible en el entorno donde
se generó este paquete), así que antes de darlo por cerrado corre al menos
el paso 4 y verifica que los números cuadren con lo que se documenta abajo.

## 0. Si ya tienes una base de datos corriendo (no es instalación nueva)

```bash
psql -U postgres -d nutricionar -f backend/db/migrate_critico.sql
```

Esto agrega la clase `critico` al `CHECK constraint` de `nivel_riesgo`
(el esquema original solo permitía 3 clases, pero el modelo predice 4) y
actualiza la vista `vista_resumen_regional`. Si es una base nueva, este
paso no es necesario — `db/init.sql` ya lo incluye.

## 1. Cargar el dataset sintético (si no lo has hecho)

```bash
cd backend
python scripts/generar_dataset_sintetico.py --n 1200 --seed 42 --out data/dataset_sintetico_maule.xlsx
python scripts/load_dataset.py --file data/dataset_sintetico_maule.xlsx --reset
```

## 2. Cargar los datos reales del Maule (CASEN 2022 + ENS 2016-2017)

```bash
python scripts/load_real_data.py --file data_real/real_maule_poblacion_con_prediccion.csv
```

Carga las 3.352 personas con `fuente='CASEN_ENS_REAL'`. Puede convivir en
las mismas tablas que el dataset sintético porque el filtro `fuente` en la
API los mantiene separados.

**Limitación declarada**: la extracción de CASEN 2022 usada no incluye la
variable `comuna` (solo región). Cada persona se asigna a una comuna por
muestreo ponderado por población censal real 2017 (reproducible, no es un
dato observado) — ver `app/data_ref/pesos_comuna_maule.py` y la sección 7.5
de la memoria.

## 3. Poblar nombre/coordenadas de las 30 comunas

```bash
python scripts/load_comunas.py
```

Necesario independientemente de qué fuente cargaste — llena
`comunas_resumen` con nombre y lat/lon (usa `app/data_ref/comunas_maule_geo.py`,
cartografía pública INE). Sin este paso el mapa muestra códigos en vez de
nombres de comuna.

## 3.5. Cargar Vigilancia Nutricional REM P5 (MINSAL, registro oficial)

```bash
# 1. Si es una base ya desplegada (no nueva), agrega las columnas primero:
psql -U postgres -d nutricionar -f db/migrate_rem.sql

# 2. (Re)generar el CSV comunal a partir de los reportes REM crudos, si cambian:
python scripts/etl_real/step5_procesar_rem_p5.py \
    --normal ../data/MINSAL/VigilanciaNutricional_Indicador_pesoNormal_2026.xls \
    --bajo   ../data/MINSAL/VigilanciaNutricional_Indicador_pesoBajo_2026.xls \
    --out data_real/rem_p5_nutricional_maule_2026.csv

# 3. Cargar en comunas_resumen (requiere que el paso 3 ya se haya corrido):
python scripts/load_rem_comunas.py --file data_real/rem_p5_nutricional_maule_2026.csv
```

A diferencia de CASEN/ENS/sintético, esto **no** son personas individuales —
son los indicadores 7.3 (bajo peso) y 7.4 (normal) del REM P5, registro
administrativo de las ~92.700 personas mayores bajo control en la red
asistencial pública del Maule a junio (todo el universo en control, no una
muestra). Se cargan como 3 columnas fijas por comuna en `comunas_resumen`
(`n_control_rem`, `pct_normal_rem`, `pct_bajo_peso_rem`), independientes de
`fuente`/`pacam`/etc. — sirven de referencia de cobertura oficial para
contrastar con las estimaciones del modelo, no reemplazan al dataset
cargado en `personas`.

## 4. Verificar

```bash
# Debería devolver total_adultos_mayores = 3352
curl "http://localhost:8000/api/v1/indicadores/resumen?region=07&fuente=CASEN_ENS_REAL"

# Debería devolver 30 comunas, con total_personas sumando 3352 en conjunto
curl "http://localhost:8000/api/v1/comunas/?region_cod=07&fuente=CASEN_ENS_REAL"

# El detalle de una comuna debe coincidir con lo que muestra el listado
curl "http://localhost:8000/api/v1/comunas/07101?fuente=CASEN_ENS_REAL"

# pct_bajo_peso_rem de Talca debería ser 8.79 (independiente de "fuente")
curl "http://localhost:8000/api/v1/comunas/07101"
```

## 5. Frontend

No requiere cambios de configuración — el selector "Fuente de datos" ya
está en `FilterSidebar.jsx` (Sintético / Real — Maule). Al elegir "Real"
se muestra automáticamente la nota de limitación (proxy MNA, comuna
estimada, sin factores de expansión). Si `comunas_resumen` tiene los
campos REM cargados, el panel de detalle de comuna del mapa muestra
además "Bajo peso REM (oficial)" junto al `pct_desnutricion` del modelo.

```bash
cd nutricionar
npm install
npm run dev
```

## Qué se corrigió de paso (bugs preexistentes, no introducidos en esta sesión)

- `indicadores_nutricionales.nivel_riesgo` solo permitía 3 clases
  (`alto/medio/bajo`); el modelo predice 4. Corregido en `db/init.sql` +
  `db/migrate_critico.sql`.
- El endpoint `/api/v1/comunas/{comuna_cod}` (detalle) no recalculaba en
  vivo como sí lo hace el listado `/api/v1/comunas/` — devolvía cifras
  estáticas desactualizadas. Ahora ambos son consistentes entre sí y
  respetan los mismos filtros (`sexo`, `grupo_etario`, `pacam`, `fuente`).
- El `ORDER BY` de la distribución de riesgo en `/indicadores/stats` no
  incluía `critico` en el orden de clases.
