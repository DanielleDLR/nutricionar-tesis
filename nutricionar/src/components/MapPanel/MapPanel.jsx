import { useEffect, useRef, useState } from 'react'
import { COMUNAS_MAULE, RISK_COLORS } from '../../data/mockData'
import './MapPanel.css'

export default function MapPanel() {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const [selected, setSelected] = useState(COMUNAS_MAULE[0])
  const [mapType, setMapType] = useState('burbujas')

  useEffect(() => {
    if (mapInstanceRef.current) return
    if (!window.L) return

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

    COMUNAS_MAULE.forEach(c => {
      const radius = Math.sqrt(c.n) * 1.2 + 4
      const marker = L.circleMarker([c.lat, c.lon], {
        radius,
        fillColor: RISK_COLORS[c.nivel],
        color: 'white',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.78,
      }).addTo(map)

      marker.on('click', () => setSelected(c))
      marker.bindTooltip(`<strong>${c.nombre}</strong><br/>${c.pct}% riesgo`)
    })

    mapInstanceRef.current = map
  }, [])

  return (
    <section className="panel map-panel">
      <div className="panel-head">
        <div className="panel-title">
          Mapa de zonas vulnerables{' '}
          <small>nivel comunal · Maule</small>
        </div>
        <div className="panel-actions">
          {['Coroplético','Burbujas','Calor'].map(t => (
            <button
              key={t}
              className={`panel-action ${mapType === t.toLowerCase() ? 'active' : ''}`}
              onClick={() => setMapType(t.toLowerCase())}
            >{t}</button>
          ))}
          <button className="panel-action">⛶ Pantalla completa</button>
        </div>
      </div>

      <div className="map-wrap">
        <div ref={mapRef} className="leaflet-map" />

        <aside className="map-side">
          {/* Detalle de la comuna seleccionada */}
          <div className="detail-card">
            <div className="selected-name">{selected.nombre}</div>
            <div className="selected-cut">CUT {selected.cod}</div>
            <div className={`selected-risk ${selected.nivel}`}>
              ● riesgo {selected.nivel} · {selected.pct}%
            </div>
          </div>

          <div className="stat-row"><span className="k">Adultos mayores</span><span className="v">{selected.n}</span></div>
          <div className="stat-row"><span className="k">Riesgo desnutrición</span><span className="v">{selected.pct}%</span></div>
          <div className="stat-row"><span className="k">Desnutrición est.</span><span className="v">4,5%</span></div>
          <div className="stat-row"><span className="k">Inseg. alim. severa</span><span className="v">5,7%</span></div>
          <div className="stat-row"><span className="k">Beneficiarios PACAM</span><span className="v">158 (60%)</span></div>
          <div className="stat-row"><span className="k">No retiran PACAM</span><span className="v">94 (59%)</span></div>

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
              { label: 'Crítico', range: '≥ 35%', color: 'var(--critico)' },
              { label: 'Alto',    range: '25–35%', color: 'var(--alto)' },
              { label: 'Medio',   range: '15–25%', color: 'var(--medio)' },
              { label: 'Bajo',    range: '< 15%',  color: 'var(--bajo)' },
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
