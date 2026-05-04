import './KPIStrip.css'
import { KPI_DATA } from '../../data/mockData'

export default function KPIStrip() {
  return (
    <div className="kpis">
      {KPI_DATA.map((kpi, i) => (
        <div key={i} className={`kpi ${kpi.type}`}>
          <div className="kpi-label">{kpi.label}</div>
          <div className="kpi-value">{kpi.value}<sup>{kpi.unit}</sup></div>
          <div className={`kpi-delta ${kpi.deltaType}`}>{kpi.delta}</div>
        </div>
      ))}
    </div>
  )
}
