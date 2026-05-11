/**
 * api.js — Capa de servicios NutricioNar
 * ========================================
 * Centraliza todas las llamadas al backend FastAPI.
 * Usa la variable de entorno VITE_API_URL (default: http://localhost:8000).
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Wrapper genérico con manejo de errores.
 * Retorna { data, error } para que los componentes puedan manejar ambos casos.
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

// ─── Indicadores ────────────────────────────────────────────

/**
 * GET /api/v1/indicadores/resumen
 * Retorna totales nacionales: total_personas, pct_riesgo_alto, etc.
 */
export async function getResumen() {
  return apiFetch('/api/v1/indicadores/resumen')
}

/**
 * GET /api/v1/indicadores/
 * Retorna distribución por región/zona.
 * @param {Object} filters - { region?, zona? }
 */
export async function getIndicadores(filters = {}) {
  return apiFetch('/api/v1/indicadores/', filters)
}

// ─── Comunas ────────────────────────────────────────────────

/**
 * GET /api/v1/comunas/
 * Retorna estadísticas por comuna con filtros opcionales.
 * @param {Object} filters - { region_cod?, nivel_riesgo? }
 */
export async function getComunas(filters = {}) {
  return apiFetch('/api/v1/comunas/', filters)
}

/**
 * GET /api/v1/comunas/:cod
 * Retorna el detalle de una comuna.
 * @param {string} comunaCod - Código CUT de 5 dígitos (ej: "07101")
 */
export async function getComuna(comunaCod) {
  return apiFetch(`/api/v1/comunas/${comunaCod}`)
}

// ─── Beneficiarios ──────────────────────────────────────────

/**
 * GET /api/v1/beneficiarios/
 * Retorna lista paginada de beneficiarios.
 * @param {Object} filters - { region?, riesgo?, page?, page_size? }
 */
export async function getBeneficiarios(filters = {}) {
  return apiFetch('/api/v1/beneficiarios/', filters)
}

/**
 * GET /api/v1/beneficiarios/:id
 * Retorna el detalle de un beneficiario.
 * @param {number} id
 */
export async function getBeneficiario(id) {
  return apiFetch(`/api/v1/beneficiarios/${id}`)
}

// ─── Health ─────────────────────────────────────────────────

/**
 * GET /health
 * Verifica disponibilidad del backend.
 * @returns {boolean} true si el backend responde correctamente
 */
export async function checkHealth() {
  const { data } = await apiFetch('/health')
  return data?.status === 'healthy'
}
