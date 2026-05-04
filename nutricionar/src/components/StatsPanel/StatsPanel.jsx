import { useState } from 'react'
import './StatsPanel.css'

/* ── MNA Distribution ── */
function MNAPanel() {
  return (
    <section className="panel">
      <div className="panel-head">
        <div className="panel-title">Estado nutricional MNA <small>variable objetivo · ENS 2017</small></div>
        <div className="panel-actions">
          <button className="panel-action active">%</button>
          <button className="panel-action">N</button>
        </div>
      </div>
      <div className="chart-area">
        <div className="mna-stack">
          <div className="mna-segment" style={{ background: 'var(--critico)', width: '5.6%' }} />
          <div className="mna-segment" style={{ background: 'var(--alto)', width: '32.3%' }}>32,3%</div>
          <div className="mna-segment" style={{ background: 'var(--bajo)', width: '62.1%' }}>62,1%</div>
        </div>
        <div className="mna-legend">
          {[
            { pct: '5,6', color: 'var(--critico)', label: 'Desnutrición', desc: '67 personas · MNA 0–7' },
            { pct: '32,3', color: 'var(--alto)',   label: 'Riesgo',       desc: '388 personas · MNA 8–11' },
            { pct: '62,1', color: 'var(--bajo)',   label: 'Normal',       desc: '745 personas · MNA 12–14' },
          ].map(item => (
            <div key={item.label} className="mna-legend-item" style={{ borderColor: item.color }}>
              <div className="v">{item.pct}<sup>%</sup></div>
              <div className="l">{item.label}</div>
              <div className="desc">{item.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ── FIES Distribution ── */
function FIESPanel() {
  const [activeFilter, setActiveFilter] = useState('Todos')
  const rows = [
    { label: 'Seguro',   pct: 75.1, color: 'var(--bajo)' },
    { label: 'Leve',     pct: 13.2, color: 'var(--medio)' },
    { label: 'Moderada', pct: 4.5,  color: 'var(--alto)' },
    { label: 'Severa',   pct: 7.2,  color: 'var(--critico)' },
  ]
  const items = [
    { label: 'Preocupación por quedarse sin alimentos',   pct: '24,9%' },
    { label: 'Reducción de variedad por motivos económicos', pct: '21,2%' },
    { label: 'Salteo de comidas',                          pct: '9,4%' },
    { label: 'Día completo sin comer',                     pct: '5,4%' },
  ]

  return (
    <section className="panel">
      <div className="panel-head">
        <div className="panel-title">Inseguridad alimentaria <small>escala FIES · CASEN 2022</small></div>
        <div className="panel-actions">
          {['Todos','Mujer','Hombre'].map(f => (
            <button key={f} className={`panel-action ${activeFilter === f ? 'active' : ''}`} onClick={() => setActiveFilter(f)}>{f}</button>
          ))}
        </div>
      </div>
      <div className="chart-area">
        <div className="fies-list">
          {rows.map(r => (
            <div key={r.label} className="fies-row">
              <span className="fies-lab">
                <span className="dot" style={{ background: r.color }} />
                {r.label}
              </span>
              <div className="track"><div className="fill" style={{ width: `${r.pct}%`, background: r.color }} /></div>
              <span className="fies-pct">{r.pct}%</span>
            </div>
          ))}
        </div>
        <div className="fies-items">
          <div className="label-mono" style={{ marginBottom: 8 }}>Ítems FIES más reportados</div>
          {items.map(it => (
            <div key={it.label} className="stat-row">
              <span className="k">{it.label}</span>
              <span className="v">{it.pct}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ── Comorbidities ── */
function ComorbilidadesPanel() {
  const list = [
    { rank: 1, nombre: 'Hipertensión arterial', pct: 60 },
    { rank: 2, nombre: 'Pérdida dentaria',       pct: 51 },
    { rank: 3, nombre: 'Dificultad visual',      pct: 52 },
    { rank: 4, nombre: 'Diabetes mellitus',      pct: 28 },
    { rank: 5, nombre: 'Limitación física',      pct: 27 },
    { rank: 6, nombre: 'Osteoporosis',           pct: 25 },
    { rank: 7, nombre: 'Depresión',              pct: 19 },
    { rank: 8, nombre: 'Demencia / det. cognitivo', pct: 9 },
  ]

  return (
    <section className="panel">
      <div className="panel-head">
        <div className="panel-title">Comorbilidades clínicas <small>prevalencia ENS 2017</small></div>
      </div>
      <div className="chart-area">
        <div className="comorb-list">
          {list.map(item => (
            <div key={item.rank} className="comorb-row">
              <span className="rank">{item.rank}</span>
              <span className="comorb-name">{item.nombre}</span>
              <div className="track"><div className="fill" style={{ width: `${item.pct}%` }} /></div>
              <span className="comorb-pct">{item.pct}%</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ── PACAM Adherence ── */
function PacamPanel() {
  const circ = 2 * Math.PI * 40 // ~251.3
  const segments = [
    { pct: 30, color: '#8B1A1A', label: 'Distancia' },
    { pct: 28, color: '#C76123', label: 'Movilidad reducida' },
    { pct: 22, color: '#D9A847', label: 'Desconocimiento' },
    { pct: 12, color: '#1F4E58', label: 'Calidad percibida' },
    { pct: 8,  color: '#8A8B8D', label: 'Otro' },
  ]

  let offset = 0
  const arcs = segments.map(s => {
    const dash = (s.pct / 100) * circ
    const arc = { ...s, dash, offset }
    offset += dash
    return arc
  })

  return (
    <section className="panel">
      <div className="panel-head">
        <div className="panel-title">Adherencia PACAM <small>motivos de no retiro · JUNAEB</small></div>
      </div>
      <div className="chart-area">
        <div className="pacam-wrap">
          <div className="pacam-donut">
            <svg viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" fill="none" stroke="#F2EEE5" strokeWidth="14"/>
              {arcs.map(arc => (
                <circle key={arc.label} cx="50" cy="50" r="40" fill="none"
                  stroke={arc.color} strokeWidth="14"
                  strokeDasharray={`${arc.dash} ${circ}`}
                  strokeDashoffset={`-${arc.offset}`}
                  transform="rotate(-90 50 50)"
                />
              ))}
            </svg>
            <div className="donut-center">
              <div className="dv">62<sup>%</sup></div>
              <div className="dl">No retiro</div>
            </div>
          </div>
          <div className="pacam-legend">
            {arcs.map(arc => (
              <div key={arc.label} className="pacam-legend-item">
                <div className="sw" style={{ background: arc.color }} />
                <span>{arc.label}</span>
                <span className="ppct">{arc.pct}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

/* ── RSH Distribution ── */
function RSHPanel() {
  const tramos = [
    { label: 'Tramo A', sub: 'máx. vulnerable', n: 215, pcts: [14, 42, 22, 22] },
    { label: 'Tramo B', sub: '', n: 261, pcts: [9, 33, 28, 30] },
    { label: 'Tramo C', sub: '', n: 298, pcts: [5, 25, 30, 40] },
    { label: 'Tramo D', sub: '', n: 237, pcts: [3, 17, 30, 50] },
    { label: 'Tramo E', sub: 'mín. vulnerable', n: 189, pcts: [1, 9, 28, 62] },
  ]
  const colors = ['var(--critico)', 'var(--alto)', 'var(--medio)', 'var(--bajo)']
  const maxN = Math.max(...tramos.map(t => t.n))

  return (
    <section className="panel" style={{ gridColumn: 'span 2' }}>
      <div className="panel-head">
        <div className="panel-title">Distribución por tramo RSH y nivel de riesgo <small>cruce socioeconómico × nutricional</small></div>
        <div className="panel-actions">
          <button className="panel-action active">Apilado</button>
          <button className="panel-action">Agrupado</button>
        </div>
      </div>
      <div className="chart-area">
        <div className="dist-chart">
          {tramos.map(t => {
            const h = (t.n / maxN) * 200
            const grad = `linear-gradient(180deg, ${t.pcts.map((p, i) => {
              const prev = t.pcts.slice(0, i).reduce((a, b) => a + b, 0)
              return `${colors[i]} ${prev}%, ${colors[i]} ${prev + p}%`
            }).join(', ')})`
            return (
              <div key={t.label} className="dist-col">
                <div className="dist-v">{t.n}</div>
                <div className="dist-bar" style={{ height: h, background: grad }} />
                <div className="dist-lab">{t.label}{t.sub && <><br/><span>{t.sub}</span></>}</div>
              </div>
            )
          })}
        </div>
        <div className="dist-leyenda">
          {['Crítico','Alto','Medio','Bajo'].map((l, i) => (
            <span key={l} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11, fontFamily: 'var(--mono)', color: 'var(--ink-soft)' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: colors[i], display: 'inline-block' }} />
              {l}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ── Main export ── */
export default function StatsPanel() {
  return (
    <div className="stats-grid">
      <MNAPanel />
      <FIESPanel />
      <ComorbilidadesPanel />
      <PacamPanel />
      <RSHPanel />
    </div>
  )
}
