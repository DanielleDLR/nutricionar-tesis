import { useEffect, useRef, useState, useCallback } from 'react'
import { COMUNAS_MAULE, RISK_COLORS } from '../../data/mockData'
import { getComunas } from '../../services/api'
import './MapPanel.css'

/** Índice estático lat/lon por código CUT (la API no almacena coordenadas) */
const COORDS = Object.fromEntries(
  COMUNAS_MAULE.map(c => [c.cod, { lat: c.lat, lon: c.lon, nombre: c.nombre }])
)

/** Fusiona datos de la API con coordenadas estáticas */
function mergeWithCoords(apiComunas) {
  return apiComunas
    .map(c => {
      const geo = COORDS[c.comuna_cod]
      if (!geo) return null
      return {
        cod:    c.comuna_cod,
        nombre: c.comuna_nombre || geo.nombre,
        lat:    geo.lat,
        lon:    geo.lon,
        n:      c.total_personas,
        pct:    c.pct_riesgo_alto_crit,
        nivel:  c.nivel_riesgo_zona || 'bajo',
        data:   c,   // objeto completo para el panel lateral
      }
    })
    .filter(Boolean)
}

export default function MapPanel({ filters = {} }) {
  const mapRef         = useRef(null)
  const mapInstanceRef = useRef(null)
  const layerGroupRef  = useRef(null)
  const heatLayerRef   = useRef(null)

  const [selected, setSelected]   = useState(null)
  const [comunas,  setComunas]    = useState([])
  const [loading,  setLoading]    = useState(true)
  const [apiOk,    setApiOk]      = useState(false)
  const [mapType,  setMapType]    = useState('burbujas')

  // Carga datos comunales desde la API (con fallback a mockData)
  const loadComunas = useCallback(async () => {
    setLoading(true)
    const params = {}
    if (filters.region)     params.region_cod   = filters.region
    if (filters.nivelRiesgo) params.nivel_riesgo = filters.nivelRiesgo

    const { data, error } = await getComunas(params)

    if (data && !error && data.comunas?.length > 0) {
      const merged = mergeWithCoords(data.comunas)
      setComunas(merged)
      setSelected(merged[0] ?? null)
      setApiOk(true)
    } else {
      // Fallback a mockData
      const fallback = COMUNAS_MAULE.map(c => ({
        cod:    c.cod,
        nombre: c.nombre,
        lat:    c.lat,
        lon:    c.lon,
        n:      c.n,
        pct:    c.pct,
        nivel:  c.nivel,
        data:   null,
      }))
      setComunas(fallback)
      setSelected(fallback[0])
      setApiOk(false)
    }
    setLoading(false)
  }, [filters.region, filters.nivelRiesgo])

  useEffect(() => { loadComunas() }, [loadComunas])

  // Inicializar el mapa Leaflet (solo una vez)
  useEffect(() => {
    if (mapInstanceRef.current || !window.L || !mapRef.current) return

    const L = window.L
    const map = L.map(mapRef.current, {
      zoomControl: true,
      attributionControl: false,
    }).setView([-35.5, -71.7], 8)

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}@2x.png', {
      maxZoom: 18, subdomains: 'abcd',
    }).addTo(map)

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}@2x.png', {
      maxZoom: 18, subdomains: 'abcd',
    }).addTo(map)

    layerGroupRef.current = L.layerGroup().addTo(map)
    mapInstanceRef.current = map
  }, [])

  // Redibujar capas cuando cambian las comunas o el tipo de mapa
  useEffect(() => {
    if (!mapInstanceRef.current || !window.L || comunas.length === 0) return

    const L = window.L
    const map = mapInstanceRef.current

    // Limpiar capas previas (marcadores y calor)
    layerGroupRef.current.clearLayers()
    if (heatLayerRef.current) {
      map.removeLayer(heatLayerRef.current)
      heatLayerRef.current = null
    }

    if (mapType === 'calor' && L.heatLayer) {
      // Mapa de calor: intensidad proporcional al % de riesgo de la comuna
      const points = comunas.map(c => [c.lat, c.lon, Math.min((c.pct ?? 0) / 50, 1)])
      heatLayerRef.current = L.heatLayer(points, {
        radius: 35,
        blur: 25,
        maxZoom: 10,
        minOpacity: 0.35,
        gradient: { 0.3: '#2C5530', 0.5: '#D9A847', 0.7: '#C76123', 1.0: '#8B1A1A' },
      }).addTo(map)
      return
    }

    // Coroplético / Burbujas: círculos coloreados por nivel de riesgo
    comunas.forEach(c => {
      const radius = mapType === 'coropletico' ? 13 : Math.sqrt(c.n) * 1.2 + 4
      const marker = L.circleMarker([c.lat, c.lon], {
        radius,
        fillColor: RISK_COLORS[c.nivel] ?? RISK_COLORS.bajo,
        color:       'white',
        weight:      2,
        opacity:     1,
        fillOpacity: mapType === 'coropletico' ? 0.9 : 0.78,
      })

      marker.on('click', () => setSelected(c))
      marker.bindTooltip(
        `<strong>${c.nombre}</strong><br/>${c.pct?.toFixed(1) ?? c.pct}% riesgo`
      )
      layerGroupRef.current.addLayer(marker)
    })
  }, [comunas, mapType])

  const sel = selected

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
        <div className="panel-actions" role="group" aria-label="Tipo de visualización del mapa">
          {['Coroplético','Burbujas','Calor'].map(t => (
            <button
              key={t}
              className={`panel-action ${mapType === t.toLowerCase() ? 'active' : ''}`}
              onClick={() => setMapType(t.toLowerCase())}
              aria-pressed={mapType === t.toLowerCase()}
            >{t}</button>
          ))}
          <button className="panel-action" aria-label="Ver mapa en pantalla completa">
            <span aria-hidden="true">⛶</span> Pantalla completa
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
                  ● riesgo {sel.nivel} · {
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
              <div className="selected-name">Selecciona una comuna</div>
            </div>
          )}

          <div className="factors-list">
            <h5>Factores de riesgo principales</h5>
            {[
              { label: 'Limitación física', pct: 28, color: 'var(--alto)' },
              { label: 'Pérdida dentaria',  pct: 53, color: 'var(--alto)' },
              { label: 'Vive solo/a',       pct: 38, color: 'var(--alto)' },
              { label: 'Depresión',         pct: 19, color: 'var(--medio)' },
              { label: 'Diabetes',          pct: 28, color: 'var(--medio)' },
            ].map(f => (
              <div key={f.label} className="factor">
                <span className="factor-name">{f.label}</span>
                <div className="bar">
                  <div className="bar-fill" style={{ width: `${f.pct*2}%`, background: f.color }} />
                </div>
                <span className="pct">{f.pct}%</span>
              </div>
            ))}
          </div>

          <h4 style={{ marginTop: 24 }}>Leyenda: nivel de riesgo</h4>
          <div className="legend">
            {[
              { label: 'Crítico', range: '≥ 40%', color: 'var(--critico)' },
              { label: 'Alto',    range: '25–40%', color: 'var(--alto)' },
              { label: 'Medio',   range: '10–25%', color: 'var(--medio)' },
              { label: 'Bajo',    range: '< 10%',  color: 'var(--bajo)' },
            ].map(l => (
              <div key={l.label} className="legend-item">
                <div className="legend-swatch" style={{ background: l.color }} />
                <span className="label-l">{l.label}</span>
                <span className="range">{l.range}</span>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </section>
  )
}
