import { useState } from 'react'
import './FilterSidebar.css'

const grupos = ['65–74', '75–84', '85+']
const sexos  = ['Mujer', 'Hombre']
const indicadores = [
  { label: 'Riesgo compuesto',        hint: 'ML' },
  { label: 'Categoría MNA',           hint: 'ENS' },
  { label: 'Inseguridad alim. (FIES)',hint: 'CASEN' },
  { label: 'Adherencia PACAM',        hint: 'JUNAEB' },
  { label: 'IMC',                     hint: 'ENS' },
]
const riesgos = [
  { label: 'Crítico', cls: 'critico' },
  { label: 'Alto',    cls: 'alto' },
  { label: 'Medio',   cls: 'medio' },
  { label: 'Bajo',    cls: 'bajo' },
]
const pacam = ['Solo beneficiarios', 'No-retiradores', 'Sin cobertura']

export default function FilterSidebar({ onFiltersChange }) {
  const [activeGrupos,  setActiveGrupos]  = useState(new Set(['65–74','75–84','85+']))
  const [activeSexos,   setActiveSexos]   = useState(new Set(['Mujer','Hombre']))
  const [activeRiesgos, setActiveRiesgos] = useState(new Set(['Crítico','Alto']))
  const [activePacam,   setActivePacam]   = useState(new Set(['No-retiradores']))
  const [indicador,     setIndicador]     = useState(0)

  function toggle(set, setter, val) {
    const next = new Set(set)
    next.has(val) ? next.delete(val) : next.add(val)
    setter(next)
  }

  function reset() {
    setActiveGrupos(new Set(['65–74','75–84','85+']))
    setActiveSexos(new Set(['Mujer','Hombre']))
    setActiveRiesgos(new Set(['Crítico','Alto']))
    setActivePacam(new Set(['No-retiradores']))
    setIndicador(0)
  }

  return (
    <aside className="filters">
      <div className="filters-header">
        <h3>Filtros</h3>
        <button className="reset-btn" onClick={reset}>↺ limpiar</button>
      </div>

      {/* Región */}
      <div className="filter-group">
        <label>Región</label>
        <select className="f-select">
          <option>Maule (07) — Piloto</option>
          <option disabled>Metropolitana (próx.)</option>
          <option disabled>Biobío (próx.)</option>
        </select>
      </div>

      {/* Comuna */}
      <div className="filter-group">
        <label>Comuna</label>
        <select className="f-select">
          <option>Todas las comunas (30)</option>
          <option>Talca</option><option>Curicó</option>
          <option>Linares</option><option>Constitución</option>
          <option>Cauquenes</option>
        </select>
      </div>

      {/* Grupo etario */}
      <div className="filter-group">
        <label>Grupo etario</label>
        <div className="chips">
          {grupos.map(g => (
            <span
              key={g}
              className={`chip ${activeGrupos.has(g) ? 'active' : ''}`}
              onClick={() => toggle(activeGrupos, setActiveGrupos, g)}
            >{g}</span>
          ))}
        </div>
      </div>

      {/* Sexo */}
      <div className="filter-group">
        <label>Sexo</label>
        <div className="chips">
          {sexos.map(s => (
            <span
              key={s}
              className={`chip ${activeSexos.has(s) ? 'active' : ''}`}
              onClick={() => toggle(activeSexos, setActiveSexos, s)}
            >{s}</span>
          ))}
        </div>
      </div>

      {/* Indicador */}
      <div className="filter-group">
        <label>Indicador a visualizar</label>
        <div className="radio-group">
          {indicadores.map((ind, i) => (
            <div
              key={i}
              className={`radio-row ${indicador === i ? 'active' : ''}`}
              onClick={() => setIndicador(i)}
            >
              <span className="radio-dot"></span>
              <span>{ind.label}</span>
              <span className="hint">{ind.hint}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Nivel de riesgo */}
      <div className="filter-group">
        <label>Nivel de riesgo</label>
        <div className="chips">
          {riesgos.map(r => (
            <span
              key={r.label}
              className={`chip risk-chip ${r.cls} ${activeRiesgos.has(r.label) ? 'active' : ''}`}
              onClick={() => toggle(activeRiesgos, setActiveRiesgos, r.label)}
            >{r.label}</span>
          ))}
        </div>
      </div>

      {/* Beneficio PACAM */}
      <div className="filter-group">
        <label>Beneficio PACAM</label>
        <div className="chips">
          {pacam.map(p => (
            <span
              key={p}
              className={`chip ${activePacam.has(p) ? 'active' : ''}`}
              onClick={() => toggle(activePacam, setActivePacam, p)}
            >{p}</span>
          ))}
        </div>
      </div>

      <div className="applied-summary">
        Mostrando <strong>456</strong> de 1.200 personas<br/>
        en <strong>17</strong> comunas
      </div>
    </aside>
  )
}
