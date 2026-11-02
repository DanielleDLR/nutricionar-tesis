# Manual de Usuario — Plataforma NutricioNar

> **Versión:** Dashboard v1.0
> **Público objetivo:** Analista del MINSAL · Equipo de atención primaria (APS)
> **Proyecto de Título · Ingeniería Civil Informática · Daniela Lavanderos · 2026**

---

## 1. ¿Qué es NutricioNar?

NutricioNar es una plataforma web interactiva para **visualizar y predecir el
riesgo de desnutrición en personas mayores** en Chile, con foco piloto en la
**Región del Maule**. Integra indicadores nutricionales, de seguridad
alimentaria y de acceso a programas sociales (PACAM), y permite focalizar
recursos hacia las comunas y personas de mayor vulnerabilidad.

La plataforma está diseñada para dos perfiles:

| Perfil | Uso principal |
|--------|---------------|
| **Analista MINSAL** | Vigilancia nutricional regional, priorización de comunas, análisis de tendencias. |
| **Equipo de atención primaria (APS)** | Seguimiento de beneficiarios PACAM, identificación de quienes no retiran el beneficio y gestión de terreno. |

> El PACAM es un programa del MINSAL que se entrega en los establecimientos de
> atención primaria; por eso el perfil operativo corresponde al equipo de APS.

---

## 2. Acceso a la plataforma

| Recurso | URL (entorno local) |
|---------|---------------------|
| Aplicación (Dashboard) | `http://localhost:5173` |
| API REST | `http://localhost:8000` |
| Documentación interactiva de la API (Swagger) | `http://localhost:8000/docs` |

> En producción estas direcciones serán reemplazadas por el dominio
> institucional definido en el despliegue.

---

## 3. Recorrido del Dashboard

La pantalla principal se organiza en paneles, de arriba hacia abajo:

### 3.1 Barra superior y encabezado
Muestra el título, la ruta de navegación (*Inicio / Vigilancia nutricional /
Mapa de riesgo regional*) y el contexto del análisis: región, número de
personas, comunas y período.

### 3.2 Indicadores clave (KPI)
Cuatro tarjetas resumen con los porcentajes regionales:
- **% Riesgo alto** de desnutrición (categoría MNA).
- **% Riesgo medio**.
- **% Inseguridad alimentaria** (moderada + severa).
- **% Beneficiarios PACAM**.

Si la API no está disponible, el panel muestra el aviso *"datos de muestra ·
API no disponible"* y utiliza valores sintéticos calibrados.

### 3.3 Mapa de zonas vulnerables
Mapa interactivo (Leaflet) con las 30 comunas del Maule. Cada comuna se
representa con una burbuja cuyo tamaño es proporcional al número de personas
mayores y cuyo color depende del indicador elegido en el panel de filtros
(*Indicador a visualizar*): riesgo compuesto, riesgo IPRN, inseguridad
alimentaria (FIES), adherencia al PACAM o IMC. El botón **Pantalla completa**
amplía el mapa.

Al hacer **clic en una comuna** se despliega, en el panel lateral derecho, su
ficha de detalle: nombre, código CUT, nivel de riesgo, número de adultos
mayores, % de riesgo alto/crítico, desnutrición, inseguridad alimentaria
severa, beneficiarios PACAM y % de no retiro.

La leyenda (panel lateral) cambia según el indicador. Para el riesgo, los
tramos se aplican al porcentaje de personas con riesgo alto o crítico en la
comuna: **Crítico ≥ 40 %**, **Alto 25–40 %**, **Medio 10–25 %** y
**Bajo < 10 %**. Para la inseguridad alimentaria severa son ≥ 15 %, 8–15 %,
3–8 % y < 3 %, y para el no retiro del PACAM, ≥ 60 %, 40–60 %, 20–40 % y
< 20 %.

> Los valores por comuna son estimaciones. En el piloto sintético se obtienen
> repartiendo los totales regionales entre las 30 comunas, y con datos reales
> la comuna se asigna según la población de 60 años y más del Censo 2017.
> Sirven para una lectura territorial agregada, no como medición comunal.

### 3.4 Tendencias
Gráfico de evolución mensual de los indicadores (riesgo alto/medio e
inseguridad alimentaria moderada/severa). Permite detectar variaciones a lo
largo del tiempo.

### 3.5 Estadísticas regionales
Panel con distribuciones: por nivel de riesgo, por nivel de inseguridad
alimentaria, por comorbilidades (hipertensión, diabetes, depresión) y por
quintil de ingreso.

### 3.6 Predicción individual
Formulario para estimar el riesgo de una persona mayor ingresando sus datos
(edad, sexo, IMC, puntaje MNA, comorbilidades, inseguridad alimentaria,
acceso a PACAM, etc.). El modelo devuelve el **nivel de riesgo**, la
**probabilidad** y los **factores principales** que más contribuyen.

---

## 4. Filtros

El panel lateral izquierdo permite segmentar toda la información del
dashboard:

- **Fuente de datos** (sintético piloto / real Maule preliminar)
- **Región / Comuna**
- **Grupo etario** (65–74, 75–84, 85+)
- **Sexo** (mujer / hombre)
- **Indicador a visualizar** en el mapa
- **Nivel de riesgo** (crítico / alto / medio / bajo)

Los filtros se aplican de forma dinámica y actualizan los KPI, el mapa, las
tendencias y las estadísticas. El botón **Limpiar** vuelve a los valores
por defecto.

---

## 5. Vista de "No retiran PACAM"

Pantalla dedicada al equipo de atención primaria que lista a los
**beneficiarios PACAM que no están retirando el beneficio**, con su nivel de
riesgo, los días sin retiro y el motivo probable (RUT enmascarado). El listado
puede exportarse a CSV. Permite priorizar
contactos y visitas domiciliarias. Cada fila enlaza a la **ficha individual**
del adulto mayor.

---

## 6. Ficha del adulto mayor

Detalle completo de una persona: datos demográficos, antropometría (IMC,
circunferencia de pantorrilla), comorbilidades, puntaje ELCSA / nivel de
inseguridad, datos del hogar (ingreso, quintil, acceso a programas) y la
evaluación nutricional con su nivel de riesgo, probabilidad y factores
detectados por el modelo.

---

## 7. Interpretación de los niveles de riesgo

| Nivel | Significado | Acción sugerida |
|-------|-------------|-----------------|
| **Crítico** | Riesgo muy alto de desnutrición. | Derivación / evaluación clínica prioritaria. |
| **Alto** | Riesgo elevado. | Seguimiento cercano y refuerzo nutricional. |
| **Medio** | Riesgo moderado. | Monitoreo periódico. |
| **Bajo** | Sin señales de riesgo relevante. | Control de rutina. |

> **Importante:** los resultados son una **ayuda a la decisión** basada en un
> modelo predictivo entrenado sobre datos sintéticos calibrados. No
> reemplazan la evaluación clínica profesional.

---

## 8. Origen de los datos

El piloto utiliza un **dataset sintético calibrado** con distribuciones de
ESSALCAVI 2024 (INTA, U. de Chile), CASEN 2022 (Ministerio de Desarrollo
Social), ENS 2016–2017 (MINSAL) y el Registro Social de Hogares (RSH).
Como primera aplicación con datos reales, la plataforma también carga
microdatos públicos de CASEN 2022 y ENS 2016–2017 del Maule (fuente
*Real — Maule (preliminar)* en el panel de filtros). La incorporación de
registros administrativos del PACAM (MINSAL y atención primaria) se realizará
mediante el proceso ETL descrito en `docs/PROTOCOLO_ETL.md`.

---

## 9. Preguntas frecuentes

**¿Por qué veo el aviso "datos de muestra"?**
La aplicación no logró conectarse con la API/base de datos y está mostrando
valores sintéticos. Verifique que el backend esté en ejecución.

**¿Los datos de una persona se guardan al usar la predicción?**
No. El formulario de predicción evalúa el caso en el momento y no persiste la
información ingresada.

**¿Puedo exportar la información?**
Sí. El botón **Exportar PDF** de la barra superior genera un reporte de la
vista actual, y la vista de beneficiarios que no retiran el PACAM permite
**Exportar CSV**.

---

## 10. Soporte

Para incidencias o consultas técnicas, contactar al equipo de desarrollo de
la tesis. La documentación técnica complementaria se encuentra en:
- `docs/API_ARQUITECTURA.md` — API y arquitectura.
- `docs/PROTOCOLO_ETL.md` — Protocolo de recepción de datos.
