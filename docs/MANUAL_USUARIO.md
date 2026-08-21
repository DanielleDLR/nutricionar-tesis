# Manual de Usuario — Plataforma NutricioNar

> **Versión:** Dashboard v1.0
> **Público objetivo:** Analista del MINSAL · Operador de JUNAEB
> **Tesis de Magíster · Daniela Lavanderos · 2025–2026**

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
| **Operador JUNAEB** | Seguimiento de beneficiarios PACAM, identificación de quienes no retiran el beneficio. |

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
Mapa interactivo (Leaflet) con las comunas del Maule. Ofrece tres modos de
visualización seleccionables con los botones del panel:

| Modo | Qué muestra |
|------|-------------|
| **Coroplético** | Círculos uniformes coloreados por nivel de riesgo. |
| **Burbujas** | Tamaño proporcional a la población de adultos mayores. |
| **Calor** | Mapa de calor con intensidad según el % de riesgo. |

Al hacer **clic en una comuna** se despliega, en el panel lateral derecho, su
ficha de detalle: nombre, código CUT, nivel de riesgo, número de adultos
mayores, % de riesgo alto/crítico, desnutrición, inseguridad alimentaria
severa, beneficiarios PACAM y % de no retiro.

La leyenda de colores (panel lateral) indica los tramos:
**Crítico ≥ 40 %**, **Alto 25–40 %**, **Medio 10–25 %**, **Bajo < 10 %**.

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

- **Región / Comuna**
- **Nivel de riesgo** (crítico / alto / medio / bajo)
- **Grupo etario** (65–74, 75–84, 85+)
- **Sexo** (F / M)

Los filtros se aplican de forma dinámica y actualizan los KPI, el mapa, las
tendencias y las estadísticas. El botón **Restablecer** vuelve a los valores
por defecto.

---

## 5. Vista de "No retiran PACAM"

Pantalla dedicada para JUNAEB que lista a los **beneficiarios PACAM con riesgo
alto o medio** que no están retirando el beneficio. Permite priorizar
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
Social), ENS 2016–2017 (MINSAL), Registro Social de Hogares (RSH) y JUNAEB.
La incorporación de **datos reales** se realizará mediante el proceso ETL
descrito en `docs/PROTOCOLO_ETL_JUNAEB.md`.

---

## 9. Preguntas frecuentes

**¿Por qué veo el aviso "datos de muestra"?**
La aplicación no logró conectarse con la API/base de datos y está mostrando
valores sintéticos. Verifique que el backend esté en ejecución.

**¿Los datos de una persona se guardan al usar la predicción?**
No. El formulario de predicción evalúa el caso en el momento y no persiste la
información ingresada.

**¿Puedo exportar la información?**
La versión v1.0 prioriza la visualización. La exportación de reportes está
contemplada para versiones posteriores.

---

## 10. Soporte

Para incidencias o consultas técnicas, contactar al equipo de desarrollo de
la tesis. La documentación técnica complementaria se encuentra en:
- `docs/API_ARQUITECTURA.md` — API y arquitectura.
- `docs/PROTOCOLO_ETL_JUNAEB.md` — Protocolo de recepción de datos.
