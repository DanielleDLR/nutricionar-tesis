/**
 * api.js — Capa de servicios NutricioNar
 * ========================================
 * Centraliza todas las llamadas al backend FastAPI.
 * Usa la variable de entorno VITE_API_URL (default: http://localhost:8000).
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Wrapper generico con manejo de errores.
 * Retorna { data, error } para que los componentes manejen ambos casos.
 */
async function apiFetch(path, params = {}) {
  const url = new URL(`${BASE_URL}${path}`)
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') {
      url.searchParams.set(k, v)
    }
  })

  try {
    const res = await fetch(url.toString())
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`)
    }
    const data = await res.json()
    return { data, error: null }
  } catch (err) {
    console.warn(`[api] Error fetching ${path}:`, err.message)
    return { data: null, error: err.message }
  }
}

async function apiPost(path, body = {}) {
  const url = `${BASE_URL}${path}`
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}))
      throw new Error(`HTTP ${res.status}: ${JSON.stringify(errBody)}`)
    }
    const data = await res.json()
    return { data, error: null }
  } catch (err) {
    console.warn(`[api] Error posting ${path}:`, err.message)
    return { data: null, error: err.message }
  }
}

// === Indicadores ============================================================

/**
 * GET /api/v1/indicadores/resumen
 * Totales nacionales: total_adultos_mayores, pct_riesgo_alto, etc.
 */
export async function getResumen() {
  return apiFetch('/api/v1/indicadores/resumen')
}

/**
 * GET /api/v1/indicadores/
 * Distribucion por region/zona.
 * @param {Object} filters - { region?, zona? }
 */
export async function getIndicadores(filters = {}) {
  return apiFetch('/api/v1/indicadores/', filters)
}

/**
 * GET /api/v1/indicadores/stats
 * Distribuciones estadisticas: riesgo, inseguridad, comorbilidades, RSH.
 * @param {Object} filters - { region? }
 */
export async function getStats(filters = {}) {
  return apiFetch('/api/v1/indicadores/stats', filters)
}

// === Comunas ================================================================

/**
 * GET /api/v1/comunas/
 * Estadisticas por comuna con filtros opcionales.
 * @param {Object} filters - { region_cod?, nivel_riesgo? }
 */
export async function getComunas(filters = {}) {
  return apiFetch('/api/v1/comunas/', filters)
}

/**
 * GET /api/v1/comunas/:cod
 * Detalle de una comuna.
 */
export async function getComuna(comunaCod) {
  return apiFetch(`/api/v1/comunas/${comunaCod}`)
}

// === Beneficiarios ==========================================================

/**
 * GET /api/v1/beneficiarios/
 * Lista paginada de beneficiarios.
 * @param {Object} filters - { region?, riesgo?, page?, page_size? }
 */
export async function getBeneficiarios(filters = {}) {
  return apiFetch('/api/v1/beneficiarios/', filters)
}

/**
 * GET /api/v1/beneficiarios/:id
 * Detalle de un beneficiario.
 */
export async function getBeneficiario(id) {
  return apiFetch(`/api/v1/beneficiarios/${id}`)
}

/**
 * GET /api/v1/beneficiarios/no-retiro/motivos
 * Conteo de no-retiradores PACAM por motivo declarado.
 * @param {Object} filters - { region? }
 * @returns { total, motivos: [{ motivo, label, n, pct }] }
 */
export async function getMotivosNoRetiro(filters = {}) {
  return apiFetch('/api/v1/beneficiarios/no-retiro/motivos', filters)
}

// === Prediccion ML ==========================================================

/**
 * POST /api/v1/prediccion/
 * Predice nivel de riesgo nutricional individual.
 * @param {Object} record - campos del BeneficiarioInput (ver prediccion.py)
 * @returns { riesgo, probabilidad, factores_principales, probabilidades, usa_fallback }
 */
export async function predictRiesgo(record) {
  return apiPost('/api/v1/prediccion/', record)
}

/**
 * GET /api/v1/prediccion/info
 * Metadatos del modelo cargado.
 */
export async function getModelInfo() {
  return apiFetch('/api/v1/prediccion/info')
}

// === Health =================================================================

/**
 * GET /health
 * Verifica disponibilidad del backend.
 * @returns {boolean} true si el backend responde correctamente
 */
export async function checkHealth() {
  const { data } = await apiFetch('/health')
  return data?.status === 'healthy'
}

/**
 * GET /api/v1/indicadores/tendencias
 * Evolucion mensual de indicadores nutricionales.
 * @param {Object} params - { meses?, region? }
 */
export async function getTendencias(params = {}) {
  return apiFetch('/api/v1/indicadores/tendencias', params)
}
