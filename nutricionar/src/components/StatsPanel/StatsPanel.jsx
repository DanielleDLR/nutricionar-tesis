import { useState, useEffect } from 'react'
import { getStats, getMotivosNoRetiro, filtersToParams } from '../../services/api'
import './StatsPanel.css'

// Datos sinteticos de fallback (calibrados con dataset piloto Maule, seed=42, n=1200)
// Fuente: backend/scripts/generar_dataset_sintetico.py + metrics.json
// IPRN thresholds: critico>=0.62, alto>=0.42, medio>=0.22, bajo<0.22
const MOCK_STATS = {
  distribucion_riesgo: [
    { nivel: 'critico', n: 200, pct: 16.7 },
    { nivel: 'alto',    n: 354, pct: 29.5 },
    { nivel: 'medio',   n: 430, pct: 35.8 },
    { nivel: 'bajo',    n: 216, pct: 18.0 },
  ],
  distribucion_inseguridad: [
    { nivel: 'seguro',   n: 660, pct: 55.0 },
    { nivel: 'leve',     n: 240, pct: 20.0 },
    { nivel: 'moderado', n: 195, pct: 16.2 },
    { nivel: 'severo',   n: 105, pct: 8.8 },
  ],
  comorbilidades: [
    { nombre: 'Hipertension arterial', pct: 50.8 },
    { nombre: 'Diabetes mellitus',     pct: 27.5 },
    { nombre: 'Limitacion fisica',     pct: 29.3 },
    { nombre: 'Depresion',             pct: 19.9 },
  ],
  hay_datos: false,
}

const RIESGO_COLORS = {
  critico: 'var(--critico)',
  alto:    'var(--alto)',
  medio:   'var(--medio)',
  bajo:    'var(--bajo)',
}

/* ── Distribucion Riesgo ── */
function RiesgoPanel({ data, isMock }) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div className="panel-title">
          Distribución nivel de riesgo
          <small>modelo RandomForest · dataset piloto</small>
        </div>
        {isMock && <span className="mock-badge">muestra</span>}
      </div>
      <div className="chart-area">
        <div className="mna-stack">
          {data.map(d => (
            <div key={d.nivel} className="mna-segment"
              style={{ background: RIESGO_COLORS[d.nivel], width: `${d.pct}%` }}>
              {d.pct >= 10 && `${d.pct}%`}
            </div>
          ))}
        </div>
        <div className="mna-legend">
          {data.map(d => (
            <div key={d.nivel} className="mna-legend-item" style={{ borderColor: RIESGO_COLORS[d.nivel] }}>
              <div className="v">{d.pct}<sup>%</sup></div>
              <div className="l" style={{ textTransform: 'capitalize' }}>{d.nivel}</div>
              <div className="desc">{d.n.toLocaleString('es-CL')} personas</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ── FIES / Inseguridad ── */
function InseguridadPanel({ data, isMock }) {
  const [activeFilter, setActiveFilter] = useState('Todos')
  return (
    <section className="panel">
      <div className="panel-head">
        <div className="panel-title">
          Inseguridad alimentaria
          <small>escala FIES · CASEN 2022</small>
        </div>
        <div className="panel-actions">
          {['Todos', 'Mujer', 'Hombre'].map(f => (
            <button key={f}
              className={`panel-action ${activeFilter === f ? 'active' : ''}`}
              onClick={() => setActiveFilter(f)}>{f}</button>
          ))}
        </div>
        {isMock && <span className="mock-badge">muestra</span>}
      </div>
      <div className="chart-area">
        <div className="fies-list">
          {data.map(r => (
            <div key={r.nivel} className="fies-row">
              <span className="fies-lab">
                <span className="dot" style={{ background: RIESGO_COLORS[
                  r.nivel === 'severo' ? 'critico' :
                  r.nivel === 'moderado' ? 'alto' :
                  r.nivel === 'leve' ? 'medio' : 'bajo'
                ] }} />
                <span style={{ textTransform: 'capitalize' }}>{r.nivel}</span>
              </span>
              <div className="track">
                <div className="fill" style={{
                  width: `${r.pct}%`,
                  background: RIESGO_COLORS[
                    r.nivel === 'severo' ? 'critico' :
                    r.nivel === 'moderado' ? 'alto' :
                    r.nivel === 'leve' ? 'medio' : 'bajo'
                  ]
                }} />
              </div>
              <span className="fies-pct">{r.pct}%</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ── Comorbilidades ── */
function ComorbilidadesPanel({ data, isMock }) {
  const max = Math.max(...data.map(d => d.pct), 1)
  return (
    <section className="panel">
      <div className="panel-head">
        <div className="panel-title">
          Comorbilidades clínicas
          <small>prevalencia · ENS 2017 / dataset piloto</small>
        </div>
        {isMock && <span className="mock-badge">muestra</span>}
      </div>
      <div className="chart-area">
        <div className="comorb-list">
          {data.map((item, i) => (
            <div key={item.nombre} className="comorb-row">
              <span className="rank">{i + 1}</span>
              <span className="comorb-name">{item.nombre}</span>
              <div className="track">
                <div className="fill" style={{ width: `${(item.pct / max) * 100}%` }} />
              </div>
              <span className="comorb-pct">{item.pct}%</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ── PACAM · motivos de no retiro (API: /beneficiarios/no-retiro/motivos) ── */
const PACAM_COLORS = {
  lejania: '#8B1A1A',
  movilidad: '#C76123',
  desconocimiento: '#D9A847',
  otro: '#8A8B8D',
}
const PACAM_FALLBACK = [
  { motivo: 'lejania',        label: 'Lejanía / distancia',       pct: 32, n: 0 },
  { motivo: 'movilidad',      label: 'Movilidad reducida',        pct: 28, n: 0 },
  { motivo: 'desconocimiento', label: 'Desconocimiento del beneficio', pct: 24, n: 0 },
  { motivo: 'otro',           label: 'Otro',                      pct: 16, n: 0 },
]

function PacamPanel({ filters = {} }) {
  const [motivos, setMotivos] = useState(PACAM_FALLBACK)
  const [total, setTotal] = useState(0)
  const [isMock, setIsMock] = useState(true)

  const params = filtersToParams(filters)

  useEffect(() => {
    getMotivosNoRetiro(params).then(({ data, error }) => {
      if (!error && data && data.total > 0) {
        setMotivos(data.motivos)
        setTotal(data.total)
        setIsMock(false)
      } else {
        setMotivos(PACAM_FALLBACK)
        setTotal(0)
        setIsMock(true)
      }
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(params)])

  const circ = 2 * Math.PI * 40
  let offset = 0
  const arcs = motivos.map(s => {
    const color = PACAM_COLORS[s.motivo] || '#8A8B8D'
    const dash = (s.pct / 100) * circ
    const arc = { ...s, color, dash, offset }
    offset += dash
    return arc
  })

  return (
    <section className="panel">
      <div className="panel-head">
        <div className="panel-title">
          Adherencia PACAM
          <small>motivos de no retiro · JUNAEB</small>
        </div>
        {isMock && <span className="mock-badge">referencia</span>}
      </div>
      <div className="chart-area">
        <div className="pacam-wrap">
          <div className="pacam-donut">
            <svg viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" fill="none" stroke="#F2EEE5" strokeWidth="14"/>
              {arcs.map(arc => (
                <circle key={arc.motivo} cx="50" cy="50" r="40" fill="none"
                  stroke={arc.color} strokeWidth="14"
                  strokeDasharray={`${arc.dash} ${circ}`}
                  strokeDashoffset={`-${arc.offset}`}
                  transform="rotate(-90 50 50)"
                />
              ))}
            </svg>
            <div className="donut-center">
              <div className="dv">{isMock ? '—' : total}</div>
              <div className="dl">No retiro</div>
            </div>
          </div>
          <div className="pacam-legend">
            {arcs.map(arc => (
              <div key={arc.motivo} className="pacam-legend-item">
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
function RSHPanel({ rshData, isMock }) {
  // Usar distribucion de riesgo para construir barras apiladas por nivel
  const colors = [
    RIESGO_COLORS.critico,
    RIESGO_COLORS.alto,
    RIESGO_COLORS.medio,
    RIESGO_COLORS.bajo,
  ]

  // Fallback: tramos sinteticos si no hay datos RSH
  const tramos = rshData?.length > 0 ? rshData : [
    { tramo: 'Tramo A', total: 215, por_riesgo: { critico: 14, alto: 42, medio: 22, bajo: 22 } },
    { tramo: 'Tramo B', total: 261, por_riesgo: { critico: 9,  alto: 33, medio: 28, bajo: 30 } },
    { tramo: 'Tramo C', total: 298, por_riesgo: { critico: 5,  alto: 25, medio: 30, bajo: 40 } },
    { tramo: 'Tramo D', total: 237, por_riesgo: { critico: 3,  alto: 17, medio: 30, bajo: 50 } },
    { tramo: 'Tramo E', total: 189, por_riesgo: { critico: 1,  alto: 9,  medio: 28, bajo: 62 } },
  ]

  const maxN = Math.max(...tramos.map(t => t.total), 1)

  return (
    <section className="panel" style={{ gridColumn: 'span 2' }}>
      <div className="panel-head">
        <div className="panel-title">
          Distribución por tramo RSH y nivel de riesgo
          <small>cruce socioeconómico × nutricional</small>
        </div>
        {isMock && <span className="mock-badge">muestra</span>}
      </div>
      <div className="chart-area">
        <div className="dist-chart">
          {tramos.map(t => {
            const h = (t.total / maxN) * 200
            const niveles = ['critico', 'alto', 'medio', 'bajo']
            const pcts = niveles.map(n => {
              const val = t.por_riesgo?.[n] || 0
              return typeof val === 'number' && val <= 100 ? val
                : Math.round((val / t.total) * 100)
            })
            const grad = `linear-gradient(180deg, ${pcts.map((p, i) => {
              const prev = pcts.slice(0, i).reduce((a, b) => a + b, 0)
              return `${colors[i]} ${prev}%, ${colors[i]} ${prev + p}%`
            }).join(', ')})`
            return (
              <div key={t.tramo} className="dist-col">
                <div className="dist-v">{t.total}</div>
                <div className="dist-bar" style={{ height: h, background: grad }} />
                <div className="dist-lab">{t.tramo}</div>
              </div>
            )
          })}
        </div>
        <div className="dist-leyenda">
          {['Crítico', 'Alto', 'Medio', 'Bajo'].map((l, i) => (
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
export default function StatsPanel({ filters = {} }) {
  const [stats, setStats] = useState(null)
  const [isMock, setIsMock] = useState(false)

  const params = filtersToParams(filters)

  useEffect(() => {
    getStats(params).then(({ data, error }) => {
      if (error || !data || !data.hay_datos) {
        setStats(MOCK_STATS)
        setIsMock(true)
      } else {
        setStats(data)
        setIsMock(false)
      }
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(params)])

  const s = stats || MOCK_STATS

  return (
    <div className="stats-grid">
      <RiesgoPanel      data={s.distribucion_riesgo}      isMock={isMock} />
      <InseguridadPanel data={s.distribucion_inseguridad} isMock={isMock} />
      <ComorbilidadesPanel data={s.comorbilidades}        isMock={isMock} />
      <PacamPanel filters={filters} />
      <RSHPanel rshData={s.distribucion_rsh} isMock={isMock} />
    </div>
  )
}
