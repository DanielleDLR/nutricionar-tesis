# Protocolo de Recepción de Datos y Pipeline ETL — NutricioNar

> **Versión:** v1.0 · **Tesis de Magíster · Daniela Lavanderos · 2025–2026**
> **Ámbito:** Preparación del proceso ETL para datos reales (CASEN / RSH /
> JUNAEB), partiendo del ETL sintético ya implementado.

Este documento define el **protocolo de recepción** de datos institucionales y
el **diseño del pipeline ETL** que reemplazará al dataset sintético piloto por
datos reales, manteniendo el mismo modelo de datos y contrato de API.

---

## 1. Objetivo

Establecer un proceso reproducible, trazable y conforme a la normativa de
protección de datos para incorporar a NutricioNar la información provista por
**JUNAEB** (programa PACAM), el **Registro Social de Hogares (RSH)** y la
**Encuesta CASEN 2022**, alimentando las tablas `hogares`, `personas`,
`indicadores_nutricionales` y `comunas_resumen`.

---

## 2. Principios de gobernanza de datos

1. **Minimización:** se solicitan únicamente las variables necesarias para el
   modelo (ver §5) y para la operación del dashboard.
2. **Seudonimización en origen:** los identificadores directos (RUT, nombre,
   dirección exacta) **no** ingresan a la plataforma. JUNAEB/MDS entregan un
   identificador interno seudonimizado (`id_persona`).
3. **Agregación geográfica:** el dato se publica a nivel **comunal**; no se
   exponen registros individuales reidentificables en las vistas públicas.
4. **Trazabilidad:** cada carga registra fuente, fecha, versión y número de
   registros (tabla/registro de auditoría de cargas).
5. **Base legal:** convenio de transferencia de datos entre la institución
   académica y los organismos (MINSAL/JUNAEB/MDS), con cláusulas de uso
   académico y resguardo (Ley 19.628 y normativa vigente).

---

## 3. Flujo de recepción (protocolo)

```
[JUNAEB / MDS / MINSAL]
        │  (1) Entrega segura: SFTP institucional / medio cifrado
        ▼
[Zona de aterrizaje cruda]  ──(2) Validación de formato y checksum──▶ rechazo si falla
        │
        ▼
[Validación de esquema y calidad]  (scripts/validate_data.py)
        │
        ▼
[Transformación y mapeo]  (scripts/load_dataset.py adaptado)
        │
        ▼
[Carga en PostgreSQL]  hogares · personas · indicadores · comunas_resumen
        │
        ▼
[Cálculo de indicadores ML]  (ml/predict.py por lote) ──▶ comunas_resumen
        │
        ▼
[Auditoría de carga]  fuente, fecha, versión, conteos
```

### Pasos del protocolo

| # | Etapa | Responsable | Control |
|---|-------|-------------|---------|
| 1 | **Entrega segura** del archivo (CSV/XLSX) por canal cifrado (SFTP). | Organismo emisor | Acuse de recepción y hash SHA-256. |
| 2 | **Verificación de integridad** (checksum, tamaño, cobertura temporal). | Equipo plataforma | Comparación de hash. |
| 3 | **Validación de esquema** (columnas, tipos, dominios). | ETL automático | `validate_data.py`. |
| 4 | **Transformación** y normalización de códigos. | ETL automático | Reglas de §6. |
| 5 | **Carga** transaccional con opción `--reset`. | ETL automático | Rollback ante error. |
| 6 | **Recalculo de agregados comunales** e indicadores ML. | Proceso por lote | Conteos esperados. |
| 7 | **Auditoría** y publicación. | Equipo plataforma | Registro de carga. |

---

## 4. Frecuencia y versionado

- **CASEN:** carga puntual por ola (cada 2–3 años).
- **RSH:** actualización trimestral o según convenio.
- **JUNAEB / PACAM:** actualización mensual (cobertura y retiro de beneficio).

Cada carga se etiqueta con `fuente` y `anio_encuesta` (o período) para
permitir comparaciones históricas y reproducibilidad.

---

## 5. Mapeo de campos por fuente

### 5.1 CASEN 2022 → `hogares` / `personas`

| Campo CASEN | Destino | Notas |
|-------------|---------|-------|
| `region` | `hogares.region` | Código INE de 2 dígitos. |
| `comuna` | `hogares.comuna` | Código CUT de 5 dígitos. |
| `zona` (urbano/rural) | `hogares.zona` | 1→urbano, 2→rural. |
| `ytothaj` / ingreso hogar | `hogares.ingreso_total` | Ingreso total del hogar. |
| quintil/decil ingreso | `hogares.quintil_ingreso` | 1–5. |
| `numper` | `hogares.n_integrantes` | Nº integrantes. |
| `edad` | `personas.edad` | Filtrar ≥ 60 años. |
| `sexo` | `personas.sexo` | 1→M, 2→F. |
| diagnósticos salud | `personas.tiene_*` | Diabetes, HTA, depresión. |

### 5.2 RSH → `hogares`

| Campo RSH | Destino | Notas |
|-----------|---------|-------|
| tramo RSH | `hogares.acceso_rsh` | Presencia de tramo socioeconómico. |
| carencias | (feature ML `num_carencias`) | 0–5. |
| hacinamiento | `hogares.hacinamiento` | Booleano. |

### 5.3 JUNAEB / PACAM → `hogares` / indicadores

| Campo JUNAEB | Destino | Notas |
|--------------|---------|-------|
| beneficiario PACAM | `hogares.acceso_pacam` | Booleano. |
| retiro de beneficio | `comunas_resumen.pct_no_retiro_pacam` | Agregado comunal. |
| nº beneficiarios | `comunas_resumen.n_benef_pacam` | Conteo comunal. |

### 5.4 Indicadores nutricionales / inseguridad alimentaria

| Campo origen | Destino | Notas |
|--------------|---------|-------|
| IMC | `personas.imc` | kg/m². |
| circunferencia pantorrilla | `personas.circunferencia_pantorrilla` | cm. |
| puntaje ELCSA / FIES | `personas.puntaje_elcsa` | 0–15. |
| nivel inseguridad | `personas.nivel_inseguridad` | seguro/leve/moderado/severo. |
| nivel de riesgo (MNA/modelo) | `indicadores_nutricionales.nivel_riesgo` | bajo/medio/alto/crítico. |

---

## 6. Reglas de transformación

El ETL actual (`backend/scripts/load_dataset.py`) ya implementa las
normalizaciones base, reutilizables para datos reales:

- **Zona:** `1 → urbano`, `2 → rural`.
- **Sexo:** `1 → M`, `2 → F`.
- **Inseguridad alimentaria (FIES):** `0→seguro`, `1→leve`, `2→moderado`,
  `3→severo`.
- **Estado nutricional (categoría IMC):** `0→bajo peso`, `1→normal`,
  `2→sobrepeso`, `3→obesidad`.
- **Nivel de riesgo:** mapeo textual/numérico a `bajo/medio/alto`.

Para datos reales se añadirán:
- Conversión de códigos de comuna a **CUT** estándar (5 dígitos con relleno
  de ceros) y validación contra catálogo oficial.
- Tratamiento de **valores faltantes** mediante medianas calculadas en
  entrenamiento (`ml/features.py` · `MEDIANS`).
- Deduplicación por `id_persona` seudonimizado.

---

## 7. Validaciones de calidad (gates)

`scripts/validate_data.py` debe verificar, antes de la carga:

1. **Completitud:** columnas obligatorias presentes.
2. **Dominios:** edad ≥ 60; sexo ∈ {1,2}; comuna en catálogo; IMC en rango
   plausible (10–60).
3. **Unicidad:** `id_persona` sin duplicados.
4. **Integridad referencial:** toda persona vinculada a un hogar.
5. **Cobertura:** nº de registros dentro del rango esperado por período.

Una validación fallida **detiene** la carga y genera un reporte de errores.

---

## 8. Carga y recálculo

Comando base (ya operativo para el dataset sintético; el mismo se adapta a las
fuentes reales una vez normalizadas a las hojas esperadas):

```bash
# Carga (con reinicio de tablas)
python backend/scripts/load_dataset.py --file <archivo.xlsx> --reset

# Recalcular agregados comunales (comunas_resumen)
python backend/scripts/load_comunas.py
```

Tras la carga se ejecuta la inferencia del modelo por lote para poblar
`indicadores_nutricionales` y se actualizan los porcentajes comunales que
alimentan el mapa y los KPI.

---

## 9. Seguridad y resguardo

- Transferencia por canal cifrado (SFTP/TLS); nunca por correo no cifrado.
- Almacenamiento de archivos crudos en zona de acceso restringido, eliminados
  tras la carga validada.
- Acceso a la base de datos por credenciales por entorno (`DATABASE_URL`),
  fuera del control de versiones.
- Registro de auditoría de cada carga (fuente, fecha, responsable, conteos).

---

## 10. Checklist de entrega del protocolo

- [x] Modelo de datos relacional definido y migrado.
- [x] ETL sintético operativo (`load_dataset.py`, `load_comunas.py`).
- [x] Script de validación de integridad (`validate_data.py`).
- [x] Mapeo de campos CASEN / RSH / JUNAEB documentado.
- [x] Reglas de transformación y normalización especificadas.
- [x] Gates de calidad definidos.
- [ ] Convenio de transferencia de datos formalizado (acción institucional).
- [ ] Primera carga con datos reales (fuera del alcance del piloto académico).
