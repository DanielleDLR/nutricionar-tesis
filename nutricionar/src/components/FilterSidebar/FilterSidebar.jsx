import { useState, useEffect } from 'react'
import './FilterSidebar.css'

const gruposOpts = ['65–74', '75–84', '85+']
const sexosOpts  = ['Mujer', 'Hombre']
const indicadoresOpts = [
  { label: 'Riesgo compuesto',        hint: 'ML' },
  { label: 'Riesgo IPRN',             hint: 'IPRN' },
  { label: 'Inseguridad alim. (FIES)',hint: 'CASEN' },
  { label: 'Adherencia PACAM',        hint: 'JUNAEB' },
  { label: 'IMC',                     hint: 'ENS' },
]
const riesgosOpts = [
  { label: 'Crítico', cls: 'critico', api: 'critico' },
  { label: 'Alto',    cls: 'alto',    api: 'alto' },
  { label: 'Medio',   cls: 'medio',   api: 'medio' },
  { label: 'Bajo',    cls: 'bajo',    api: 'bajo' },
]
const pacamOpts = ['Solo beneficiarios', 'No-retiradores', 'Sin cobertura']

const DEFAULT_STATE = {
  region:     '07',
  comuna:     '',
  grupos:     new Set(['65–74','75–84','85+']),
  sexos:      new Set(['Mujer','Hombre']),
  riesgos:    new Set(['Crítico','Alto']),
  pacam:      new Set(['No-retiradores']),
  indicador:  0,
}

/**
 * Serializa el estado interno en un objeto plano para que el padre pueda
 * pasárselo a la API sin conocer Sets ni detalles del componente.
 */
function toApiFilters(state) {
  return {
    region:      state.region,
    comuna:      state.comuna || undefined,
    // nivel_riesgo: si solo hay un valor activo se envía, si son todos vacío
    nivelRiesgo: state.riesgos.size === 1
      ? riesgosOpts.find(r => state.riesgos.has(r.label))?.api
      : undefined,
    // Conjunto completo de niveles activos (el mapa filtra client-side):
    // [] = ninguno seleccionado → sin burbujas; undefined = todos → sin filtro.
    nivelesRiesgo: state.riesgos.size === 0
      ? []
      : state.riesgos.size === riesgosOpts.length
        ? undefined
        : [...state.riesgos].map(r =>
            riesgosOpts.find(o => o.label === r)?.api).filter(Boolean),
    sexos:       [...state.sexos].map(s => s === 'Mujer' ? 'F' : 'M'),
    grupos:      [...state.grupos],
    // PACAM → valores que entiende el backend. 'Sin cobertura' aún no tiene
    // soporte en la API, por lo que solo se mapean los dos primeros.
    pacam: state.pacam.size === 1 && state.pacam.has('Solo beneficiarios')
      ? 'beneficiarios'
      : state.pacam.size === 1 && state.pacam.has('No-retiradores')
        ? 'no_beneficiarios'
        : undefined,
    indicador:   indicadoresOpts[state.indicador]?.label,
  }
}

export default function FilterSidebar({ onFiltersChange }) {
  const [state, setState] = useState(DEFAULT_STATE)

  // Notifica al padre cada vez que cambia cualquier filtro
  useEffect(() => {
    onFiltersChange?.(toApiFilters(state))
  }, [state]) // eslint-disable-line react-hooks/exhaustive-deps

  function toggle(key, val) {
    setState(prev => {
      const next = new Set(prev[key])
      next.has(val) ? next.delete(val) : next.add(val)
      return { ...prev, [key]: next }
    })
  }

  function set(key, val) {
    setState(prev => ({ ...prev, [key]: val }))
  }

  function reset() {
    setState(DEFAULT_STATE)
  }

  const activeCount = [
    state.grupos.size  < gruposOpts.length,
    state.sexos.size   < sexosOpts.length,
    state.riesgos.size < riesgosOpts.length,
    state.pacam.size   > 0,
    state.comuna       !== '',
  ].filter(Boolean).length

  return (
    <aside className="filters">
      <div className="filters-header">
        <h3>
          Filtros
          {activeCount > 0 && (
            <span className="filter-badge">{activeCount}</span>
          )}
        </h3>
        <button className="reset-btn" onClick={reset}>Limpiar</button>
      </div>

      {/* Región */}
      <div className="filter-group">
        <label>Región</label>
        <select
          className="f-select"
          value={state.region}
          onChange={e => set('region', e.target.value)}
        >
          <option value="07">Maule (07) — Piloto</option>
          <option disabled value="">Metropolitana (próx.)</option>
          <option disabled value="">Biobío (próx.)</option>
        </select>
      </div>

      {/* Comuna */}
      <div className="filter-group">
        <label>Comuna</label>
        <select
          className="f-select"
          value={state.comuna}
          onChange={e => set('comuna', e.target.value)}
        >
          <option value="">Todas las comunas (30)</option>
          <option value="07101">Talca</option>
          <option value="07301">Curicó</option>
          <option value="07401">Linares</option>
          <option value="07102">Constitución</option>
          <option value="07201">Cauquenes</option>
          <option value="07304">Molina</option>
          <option value="07103">Curepto</option>
          <option value="07104">Empedrado</option>
          <option value="07302">Hualañé</option>
          <option value="07404">Parral</option>
        </select>
      </div>

      {/* Grupo etario */}
      <div className="filter-group">
        <label>Grupo etario</label>
        <div className="chips">
          {gruposOpts.map(g => (
            <span
              key={g}
              className={`chip ${state.grupos.has(g) ? 'active' : ''}`}
              onClick={() => toggle('grupos', g)}
            >{g}</span>
          ))}
        </div>
      </div>

      {/* Sexo */}
      <div className="filter-group">
        <label>Sexo</label>
        <div className="chips">
          {sexosOpts.map(s => (
            <span
              key={s}
              className={`chip ${state.sexos.has(s) ? 'active' : ''}`}
              onClick={() => toggle('sexos', s)}
            >{s}</span>
          ))}
        </div>
      </div>

      {/* Indicador */}
      <div className="filter-group">
        <label>Indicador a visualizar</label>
        <div className="radio-group">
          {indicadoresOpts.map((ind, i) => (
            <div
              key={i}
              className={`radio-row ${state.indicador === i ? 'active' : ''}`}
              onClick={() => set('indicador', i)}
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
          {riesgosOpts.map(r => (
            <span
              key={r.label}
              className={`chip risk-chip ${r.cls} ${state.riesgos.has(r.label) ? 'active' : ''}`}
              onClick={() => toggle('riesgos', r.label)}
            >{r.label}</span>
          ))}
        </div>
      </div>

      {/* Beneficio PACAM */}
      <div className="filter-group">
        <label>Beneficio PACAM</label>
        <div className="chips">
          {pacamOpts.map(p => (
            <span
              key={p}
              className={`chip ${state.pacam.has(p) ? 'active' : ''}`}
              onClick={() => toggle('pacam', p)}
            >{p}</span>
          ))}
        </div>
      </div>

      <div className="applied-summary">
        Región <strong>Maule</strong>{state.comuna && ` · ${state.comuna}`}
        <br/>
        {state.riesgos.size} nivel(es) de riesgo activos
      </div>
    </aside>
  )
}
