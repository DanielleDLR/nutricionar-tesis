import { useEffect, useState } from 'react'
import './KPIStrip.css'
import { KPI_DATA } from '../../data/mockData'
import { getResumen, filtersToParams } from '../../services/api'

/** Convierte la respuesta del endpoint /resumen en el formato de KPI_DATA */
function buildKpis(resumen) {
  const pctAlto  = parseFloat(resumen.pct_riesgo_alto  ?? 0).toFixed(1)
  const pctMedio = parseFloat(resumen.pct_riesgo_medio ?? 0).toFixed(1)
  const pctInseg = parseFloat(resumen.pct_inseguridad_alimentaria ?? 0).toFixed(1)
  const pctPacam = parseFloat(resumen.pct_beneficiarios_pacam ?? 0).toFixed(1)

  return [
    {
      label:     'Riesgo alto · Maule',
      value:     pctAlto,
      unit:      '%',
      delta:     `${resumen.total_adultos_mayores?.toLocaleString('es-CL') ?? '—'} personas`,
      deltaType: 'neutral',
      type:      'danger',
    },
    {
      label:     'Riesgo medio · Maule',
      value:     pctMedio,
      unit:      '%',
      delta:     'indice IPRN',
      deltaType: 'neutral',
      type:      'warn',
    },
    {
      label:     'Inseg. alimentaria',
      value:     pctInseg,
      unit:      '%',
      delta:     'moderada + severa',
      deltaType: 'neutral',
      type:      'neutral',
    },
    {
      label:     'Beneficiarios PACAM',
      value:     pctPacam,
      unit:      '%',
      delta:     'del total evaluado',
      deltaType: 'neutral',
      type:      'neutral',
    },
  ]
}

export default function KPIStrip({ filters = {} }) {
  const [kpis,    setKpis]    = useState(KPI_DATA)
  const [loading, setLoading] = useState(true)
  const [apiOk,   setApiOk]   = useState(false)

  const params = filtersToParams(filters)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getResumen(params).then(({ data, error }) => {
      if (cancelled) return
      if (data && !error) {
        setKpis(buildKpis(data))
        setApiOk(true)
      }
      setLoading(false)
    })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(params)])

  return (
    <div className="kpis">
      {kpis.map((kpi, i) => (
        <div key={i} className={`kpi ${kpi.type} ${loading ? 'kpi-loading' : ''}`}>
          <div className="kpi-label">{kpi.label}</div>
          <div className="kpi-value">
            {loading ? <span className="kpi-skeleton" /> : <>{kpi.value}<sup>{kpi.unit}</sup></>}
          </div>
          <div className={`kpi-delta ${kpi.deltaType}`}>
            {loading ? '' : kpi.delta}
          </div>
        </div>
      ))}
      {!loading && !apiOk && (
        <div className="kpi-notice">datos de muestra · API no disponible</div>
      )}
    </div>
  )
}
