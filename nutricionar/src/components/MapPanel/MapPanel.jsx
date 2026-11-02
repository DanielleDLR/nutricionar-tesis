import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import { COMUNAS_MAULE, RISK_COLORS } from '../../data/mockData'
import { getComunas, getStats, filtersToParams } from '../../services/api'
import './MapPanel.css'

/** Factores estáticos de respaldo para el panel lateral (si getStats falla). */
const FACTORES_FALLBACK = [
  { label: 'Limitación física', pct: 28, color: 'var(--alto)' },
  { label: 'Pérdida dentaria',  pct: 53, color: 'var(--alto)' },
  { label: 'Vive solo/a',       pct: 38, color: 'var(--alto)' },
  { label: 'Depresión',         pct: 19, color: 'var(--medio)' },
  { label: 'Diabetes',          pct: 28, color: 'var(--medio)' },
]

/** Índice estático de respaldo por código CUT (solo si la API no trae lat/lon) */
const COORDS = Object.fromEntries(
  COMUNAS_MAULE.map(c => [c.cod, { lat: c.lat, lon: c.lon, nombre: c.nombre }])
)

/**
 * Fusiona datos de la API. Prioriza las coordenadas lat/lon servidas por el
 * backend (comunas_resumen); recurre al índice estático solo como respaldo.
 */
function mergeWithCoords(apiComunas) {
  return apiComunas
    .map(c => {
      const geo = COORDS[c.comuna_cod] || {}
      const lat = c.lat ?? geo.lat
      const lon = c.lon ?? geo.lon
      if (lat == null || lon == null) return null
      return {
        cod:    c.comuna_cod,
        nombre: c.comuna_nombre || geo.nombre,
        lat,
        lon,
        n:      c.total_personas,
        pct:    c.pct_riesgo_alto_crit,
        nivel:  c.nivel_riesgo_zona || 'bajo',
        data:   c,   // objeto completo para el panel lateral
      }
    })
    .filter(Boolean)
}

/** Clasifica un valor en nivel de riesgo según umbrales [critico, alto, medio]. */
function nivelPorUmbral(valor, [uCritico, uAlto, uMedio]) {
  if (valor == null) return null
  if (valor >= uCritico) return 'critico'
  if (valor >= uAlto) return 'alto'
  if (valor >= uMedio) return 'medio'
  return 'bajo'
}

/**
 * Color de la burbuja según el indicador seleccionado en el sidebar.
 * Si la métrica no está disponible (modo muestra), cae al nivel de riesgo
 * compuesto de la comuna.
 */
function colorPorIndicador(c, indicador) {
  let nivel = null
  switch (indicador) {
    case 'Riesgo IPRN':
      // Riesgo critico+alto por comuna segun indice IPRN
      nivel = nivelPorUmbral(c.data?.pct_riesgo_alto_crit ?? c.pct, [40, 25, 10])
      break
    case 'Inseguridad alim. (FIES)':
      nivel = nivelPorUmbral(c.data?.pct_inseg_severa, [15, 8, 3])
      break
    case 'Adherencia PACAM':
      nivel = nivelPorUmbral(c.data?.pct_no_retiro_pacam, [60, 40, 20])
      break
    case 'IMC':
      // Proxy hasta tener dato real de IMC por comuna.
      nivel = nivelPorUmbral(c.data?.pct_riesgo_alto_crit ?? c.pct, [40, 25, 10])
      break
    default: // 'Riesgo compuesto'
      nivel = c.nivel
  }
  return RISK_COLORS[nivel ?? c.nivel] ?? RISK_COLORS.bajo
}

/** Leyenda (título + umbrales) según el indicador visualizado. */
const LEYENDAS = {
  'Riesgo compuesto': {
    titulo: 'nivel de riesgo',
    rangos: ['≥ 40%', '25–40%', '10–25%', '< 10%'],
  },
  'Riesgo IPRN': {
    titulo: 'riesgo alto/critico (IPRN)',
    rangos: ['≥ 40%', '25–40%', '10–25%', '< 10%'],
  },
  'Inseguridad alim. (FIES)': {
    titulo: 'inseguridad severa',
    rangos: ['≥ 15%', '8–15%', '3–8%', '< 3%'],
  },
  'Adherencia PACAM': {
    titulo: 'no retiro PACAM',
    rangos: ['≥ 60%', '40–60%', '20–40%', '< 20%'],
  },
  'IMC': {
    titulo: 'riesgo alto/crítico (proxy IMC)',
    rangos: ['≥ 40%', '25–40%', '10–25%', '< 10%'],
  },
}

export default function MapPanel({ filters = {} }) {
  const mapRef         = useRef(null)
  const mapInstanceRef = useRef(null)
  const layerGroupRef  = useRef(null)

  const [selected, setSelected]   = useState(null)
  const [comunas,  setComunas]    = useState([])
  const [loading,  setLoading]    = useState(true)
  const [apiOk,    setApiOk]      = useState(false)
  const [factoresPanel, setFactoresPanel] = useState(FACTORES_FALLBACK)

  // Carga datos comunales desde la API (con fallback a mockData). El flag
  // `cancelled` evita que una respuesta obsoleta pise a una más reciente
  // cuando los filtros cambian rápido (condición de carrera).
  useEffect(() => {
    let cancelled = false

    async function load() {
      // Un conjunto vacío significa que no hay personas que mostrar. Evita
      // consultar la API sin filtros, cuyo contrato interpreta el parámetro
      // ausente como "todos".
      if (
        (Array.isArray(filters.nivelesRiesgo) && filters.nivelesRiesgo.length === 0) ||
        (Array.isArray(filters.sexos) && filters.sexos.length === 0) ||
        (Array.isArray(filters.grupos) && filters.grupos.length === 0)
      ) {
        setComunas([])
        setSelected(null)
        setLoading(false)
        return
      }

      setLoading(true)
      // Todos los filtros activos. El nivel de riesgo va SIEMPRE como CSV de
      // los niveles seleccionados (no el valor único de filters.nivelRiesgo):
      // el backend filtra, el frontend solo muestra lo que retorna la API.
      const params = { ...filtersToParams(filters) }
      delete params.nivel_riesgo
      if (filters.nivelesRiesgo?.length > 0) {
        params.nivel_riesgo = filters.nivelesRiesgo.join(',')
      }
      if (filters.region) params.region_cod = filters.region

      const { data, error } = await getComunas(params)
      if (cancelled) return

      // Si hay una comuna seleccionada en los filtros, se restringe la vista a ella.
      const aplicarComuna = (lista) =>
        filters.comuna
          ? lista.filter(c => c.cod === filters.comuna)
          : lista

      if (data && !error && Array.isArray(data.comunas)) {
        // Respuesta válida de la API: se muestra tal cual, incluso si viene
        // vacía (0 comunas para los filtros activos ≠ API caída).
        const merged = aplicarComuna(mergeWithCoords(data.comunas))
        setComunas(merged)
        setSelected(merged[0] ?? null)
        setApiOk(true)
      } else {
        // Fallback a mockData (API caída). Imita el comportamiento del
        // backend aplicando el filtro de niveles para que la selección del
        // sidebar siga funcionando también en modo muestra.
        const fallback = aplicarComuna(COMUNAS_MAULE.map(c => ({
          cod:    c.cod,
          nombre: c.nombre,
          lat:    c.lat,
          lon:    c.lon,
          n:      c.n,
          pct:    c.pct,
          nivel:  c.nivel,
          data:   null,
        }))).filter(c =>
          !filters.nivelesRiesgo?.length || filters.nivelesRiesgo.includes(c.nivel)
        )
        setComunas(fallback)
        setSelected(fallback[0] ?? null)
        setApiOk(false)
      }
      setLoading(false)
    }

    load()
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify([
    filters.region, filters.comuna, filters.nivelesRiesgo,
    filters.sexos, filters.grupos, filters.pacam,
  ])])

  // Factores de riesgo del panel lateral: comorbilidades del subconjunto
  // filtrado (getStats), ordenadas de mayor a menor prevalencia. Si la
  // llamada falla se conservan los valores actuales (fallback silencioso).
  useEffect(() => {
    let cancelled = false

    getStats(filtersToParams(filters)).then(({ data, error }) => {
      if (cancelled || error || !data?.comorbilidades?.length) return
      const factores = [...data.comorbilidades]
        .sort((a, b) => (b.pct ?? 0) - (a.pct ?? 0))
        .map(c => ({
          label: c.nombre,
          pct: c.pct ?? 0,
          color: (c.pct ?? 0) >= 30 ? 'var(--alto)' : 'var(--medio)',
        }))
      setFactoresPanel(factores)
    })

    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(filtersToParams(filters))])

  // Inicializar el mapa Leaflet (solo una vez)
  useEffect(() => {
    if (mapInstanceRef.current || !mapRef.current) return

    const map = L.map(mapRef.current, {
      zoomControl: true,
      attributionControl: false,
    }).setView([-35.5, -71.7], 8)

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map)

    layerGroupRef.current = L.layerGroup().addTo(map)
    mapInstanceRef.current = map
  }, [])

  // Redibujar burbujas cuando cambian las comunas o el indicador a visualizar
  useEffect(() => {
    if (!mapInstanceRef.current) return

    const map = mapInstanceRef.current
    layerGroupRef.current.clearLayers()
    if (comunas.length === 0) return

    // Burbujas: radio según población, color según el indicador seleccionado
    comunas.forEach(c => {
      const radius = Math.sqrt(c.n) * 1.2 + 4
      const marker = L.circleMarker([c.lat, c.lon], {
        radius,
        fillColor: colorPorIndicador(c, filters.indicador),
        color:       'white',
        weight:      2,
        opacity:     1,
        fillOpacity: 0.78,
      })

      marker.on('click', () => setSelected(c))
      marker.bindTooltip(
        `<strong>${c.nombre}</strong><br/>${c.pct?.toFixed(1) ?? c.pct}% riesgo`
      )
      layerGroupRef.current.addLayer(marker)
    })

    // Reencuadre según las comunas visibles (responde al filtro de comuna).
    if (comunas.length === 1) {
      map.setView([comunas[0].lat, comunas[0].lon], 10)
    } else {
      map.setView([-35.5, -71.7], 8)
    }
  }, [comunas, filters.indicador])

  const sel = selected
  const leyenda = LEYENDAS[filters.indicador] || LEYENDAS['Riesgo compuesto']

  return (
    <section className="panel map-panel">
      <div className="panel-head">
        <div className="panel-title">
          Mapa de zonas vulnerables{' '}
          <small>nivel comunal · Maule</small>
          {!loading && !apiOk && (
            <span className="data-source-badge">datos de muestra</span>
          )}
        </div>
        <div className="panel-actions">
          <button className="panel-action" aria-label="Ver mapa en pantalla completa">
            Pantalla completa
          </button>
        </div>
      </div>

      <div className="map-wrap">
        <div
          ref={mapRef}
          className="leaflet-map"
          role="application"
          aria-label="Mapa interactivo de riesgo nutricional por comuna en la región del Maule"
        />

        <aside className="map-side">
          {sel ? (
            <>
              {/* Detalle de la comuna seleccionada */}
              <div className="detail-card">
                <div className="selected-name">{sel.nombre}</div>
                <div className="selected-cut">CUT {sel.cod}</div>
                <div className={`selected-risk ${sel.nivel}`}>
                  Riesgo {sel.nivel} · {
                    typeof sel.pct === 'number'
                      ? sel.pct.toFixed(1)
                      : sel.pct
                  }%
                </div>
              </div>

              <div className="stat-row">
                <span className="k">Adultos mayores</span>
                <span className="v">{sel.n?.toLocaleString('es-CL') ?? '—'}</span>
              </div>
              <div className="stat-row">
                <span className="k">Riesgo alto/crítico</span>
                <span className="v">{typeof sel.pct === 'number' ? sel.pct.toFixed(1) : sel.pct}%</span>
              </div>
              <div className="stat-row">
                <span className="k">Desnutrición estab.</span>
                <span className="v">
                  {sel.data
                    ? `${sel.data.pct_desnutricion?.toFixed(1) ?? '—'}%`
                    : '4,5%'}
                </span>
              </div>
              {sel.data?.pct_bajo_peso_rem != null && (
                <div className="stat-row">
                  <span className="k" title="Registro oficial REM P5 (MINSAL) — personas mayores en control, no la muestra del modelo">
                    Bajo peso REM (oficial)
                  </span>
                  <span className="v">{sel.data.pct_bajo_peso_rem.toFixed(1)}%</span>
                </div>
              )}
              <div className="stat-row">
                <span className="k">Inseg. alim. severa</span>
                <span className="v">
                  {sel.data
                    ? `${sel.data.pct_inseg_severa?.toFixed(1) ?? '—'}%`
                    : '5,7%'}
                </span>
              </div>
              <div className="stat-row">
                <span className="k">Beneficiarios PACAM</span>
                <span className="v">
                  {sel.data
                    ? `${sel.data.n_benef_pacam ?? '—'}`
                    : '158'}
                </span>
              </div>
              <div className="stat-row">
                <span className="k">No retiran PACAM</span>
                <span className="v">
                  {sel.data
                    ? `${sel.data.pct_no_retiro_pacam?.toFixed(1) ?? '—'}%`
                    : '59%'}
                </span>
              </div>
            </>
          ) : (
            <div className="detail-card">
              <div className="selected-name">
                {comunas.length === 0 && !loading
                  ? 'Sin comunas para los filtros activos'
                  : 'Selecciona una comuna'}
              </div>
            </div>
          )}

          <div className="factors-list">
            <h5>Factores de riesgo principales</h5>
            {factoresPanel.map(f => (
              <div key={f.label} className="factor">
                <span className="factor-name">{f.label}</span>
                <div className="bar">
                  <div className="bar-fill" style={{ width: `${Math.min(100, f.pct * 2)}%`, background: f.color }} />
                </div>
                <span className="pct">{f.pct}%</span>
              </div>
            ))}
          </div>

          <h4 style={{ marginTop: 24 }}>Leyenda: {leyenda.titulo}</h4>
          <div className="legend">
            {[
              { label: 'Crítico', color: 'var(--critico)' },
              { label: 'Alto',    color: 'var(--alto)' },
              { label: 'Medio',   color: 'var(--medio)' },
              { label: 'Bajo',    color: 'var(--bajo)' },
            ].map((l, i) => (
              <div key={l.label} className="legend-item">
                <div className="legend-swatch" style={{ background: l.color }} />
                <span className="label-l">{l.label}</span>
                <span className="range">{leyenda.rangos[i]}</span>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </section>
  )
}
