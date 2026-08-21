import { useState, useEffect } from 'react'
import { getTendencias, filtersToParams } from '../../services/api'
import './TendenciasChart.css'

const SERIES = [
  { key: 'pct_riesgo_alto',          label: 'Riesgo alto',         color: 'var(--alto)' },
  { key: 'pct_riesgo_medio',         label: 'Riesgo medio',        color: 'var(--medio)' },
  { key: 'pct_inseg_moderada_severa',label: 'Inseg. mod./severa',  color: 'var(--critico)' },
]

/**
 * Serie sintética de respaldo (calibrada con el dataset Maule) para que el
 * gráfico nunca quede en blanco si la API no responde. Devuelve `n` meses.
 */
function serieFallback(n) {
  const baseAlto = [23.5, 24.4, 25.1, 28.5, 30.7, 32.0]
  const baseMedio = [6.1, 6.4, 6.9, 7.4, 7.9, 8.2]
  const baseInseg = [8.2, 9.0, 9.9, 12.2, 14.0, 15.1]
  const hoy = new Date()
  const out = []
  for (let k = n - 1; k >= 0; k--) {
    const d = new Date(hoy.getFullYear(), hoy.getMonth() - k, 1)
    const idx = (n - 1 - k) % baseAlto.length
    out.push({
      mes: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
      total: 1200,
      pct_riesgo_alto: baseAlto[idx],
      pct_riesgo_medio: baseMedio[idx],
      pct_inseg_moderada_severa: baseInseg[idx],
    })
  }
  return out
}

function SvgLineChart({ serie, width = 560, height = 160 }) {
  if (!serie || serie.length < 2) return null

  const padL = 36, padR = 12, padT = 12, padB = 32
  const W = width - padL - padR
  const H = height - padT - padB

  const allVals = SERIES.flatMap(s => serie.map(d => d[s.key] || 0))
  const maxVal = Math.max(...allVals, 1)

  const xPos = (i) => padL + (i / (serie.length - 1)) * W
  const yPos = (v) => padT + H - (v / maxVal) * H

  const yTicks = [0, 10, 20, 30, 40].filter(t => t <= maxVal + 5)

  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`} style={{ overflow: 'visible' }}>
      {/* Grid lines */}
      {yTicks.map(t => (
        <g key={t}>
          <line x1={padL} x2={padL + W} y1={yPos(t)} y2={yPos(t)}
            stroke="var(--border)" strokeWidth="0.5" strokeDasharray="3,3" />
          <text x={padL - 4} y={yPos(t) + 4} fontSize="9"
            fill="var(--ink-soft)" textAnchor="end" fontFamily="var(--mono)">
            {t}%
          </text>
        </g>
      ))}

      {/* X axis labels */}
      {serie.map((d, i) => (
        <text key={i} x={xPos(i)} y={height - 6} fontSize="9"
          fill="var(--ink-soft)" textAnchor="middle" fontFamily="var(--mono)">
          {d.mes.slice(5)}
        </text>
      ))}

      {/* Lines */}
      {SERIES.map(s => {
        const pts = serie.map((d, i) => `${xPos(i)},${yPos(d[s.key] || 0)}`).join(' ')
        return (
          <g key={s.key}>
            <polyline points={pts} fill="none" stroke={s.color} strokeWidth="2"
              strokeLinejoin="round" strokeLinecap="round" />
            {serie.map((d, i) => (
              <circle key={i} cx={xPos(i)} cy={yPos(d[s.key] || 0)} r="3"
                fill={s.color} stroke="var(--surface)" strokeWidth="1.5">
                <title>{s.label}: {d[s.key]}%</title>
              </circle>
            ))}
          </g>
        )
      })}
    </svg>
  )
}

export default function TendenciasChart({ filters = {} }) {
  const [serie, setSerie] = useState(null)
  const [esSintetica, setEsSintetica] = useState(false)
  const [meses, setMeses] = useState(6)
  const [loading, setLoading] = useState(true)

  const params = { meses, ...filtersToParams(filters) }

  useEffect(() => {
    setLoading(true)
    getTendencias(params).then(({ data }) => {
      if (data?.serie?.length) {
        setSerie(data.serie)
        setEsSintetica(data.es_sintetica)
      } else {
        // La API no respondió: se muestra la serie de respaldo en lugar de
        // dejar el gráfico vacío.
        setSerie(serieFallback(meses))
        setEsSintetica(true)
      }
      setLoading(false)
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(params)])

  return (
    <section className="panel tendencias-panel">
      <div className="panel-head">
        <div className="panel-title">
          Tendencias de riesgo e inseguridad alimentaria
          <small>evolución mensual · Región del Maule</small>
        </div>
        <div className="panel-actions">
          {[3, 6, 12].map(m => (
            <button key={m}
              className={`panel-action ${meses === m ? 'active' : ''}`}
              onClick={() => setMeses(m)}>
              {m}m
            </button>
          ))}
        </div>
        {esSintetica && <span className="mock-badge">muestra</span>}
      </div>

      <div className="chart-area tendencias-body">
        {loading ? (
          <div className="tendencias-loading">Cargando tendencias…</div>
        ) : (
          <>
            <div className="tendencias-chart-wrap">
              <SvgLineChart serie={serie} width={560} height={170} />
            </div>

            <div className="tendencias-legend">
              {SERIES.map(s => (
                <div key={s.key} className="tend-leg-item">
                  <span className="tend-dot" style={{ background: s.color }} />
                  <span className="tend-label">{s.label}</span>
                  {serie && (
                    <span className="tend-last" style={{ color: s.color }}>
                      {serie[serie.length - 1]?.[s.key]}%
                    </span>
                  )}
                </div>
              ))}
            </div>

            {serie && serie.length > 0 && (() => {
              const last = serie[serie.length - 1]
              const first = serie[0]
              const delta = ((last.pct_riesgo_alto || 0) - (first.pct_riesgo_alto || 0)).toFixed(1)
              const dir = delta > 0 ? '+' : delta < 0 ? '−' : '='
              const col = delta > 0 ? 'var(--alto)' : delta < 0 ? 'var(--bajo)' : 'var(--ink-soft)'
              return (
                <div className="tendencias-insight">
                  Riesgo alto: <strong style={{ color: col }}>{dir} {Math.abs(delta)} pp</strong> en los últimos {meses} meses
                  {esSintetica && ' (datos sintéticos calibrados)'}
                </div>
              )
            })()}
          </>
        )}
      </div>
    </section>
  )
}
