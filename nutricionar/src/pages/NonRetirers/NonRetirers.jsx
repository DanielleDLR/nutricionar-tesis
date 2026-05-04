import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import TopBar from '../../components/TopBar/TopBar'
import { NON_RETIRERS } from '../../data/mockData'
import './NonRetirers.css'

function daysBadgeClass(dias) {
  if (dias >= 60) return 'red'
  if (dias >= 40) return 'orange'
  return 'yellow'
}

export default function NonRetirers() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')

  const filtered = NON_RETIRERS.filter(p =>
    p.nombre.toLowerCase().includes(search.toLowerCase()) ||
    p.rut.includes(search)
  )

  return (
    <div className="page-list">
      <TopBar subtitle="Gestión de terreno · Operador JUNAEB" />

      <div className="ops-layout">
        <div className="ops-header">
          <div className="ops-title">
            Beneficiarios <em>no-retiradores</em> PACAM
          </div>
          <div className="search-box">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
            </svg>
            <input
              type="text"
              placeholder="Buscar por nombre o RUT..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            <span className="search-hint">US-08</span>
          </div>
          <button className="btn btn-sm">Exportar CSV</button>
        </div>

        {/* Stats bar */}
        <div className="stats-bar">
          <div className="sbar-item danger"><span className="sv">18</span><span className="sl">no retiran (&gt;30 días)</span></div>
          <div className="sbar-item warn"><span className="sv">7</span><span className="sl">riesgo crítico</span></div>
          <div className="sbar-item"><span className="sv">4</span><span className="sl">sin visita reciente</span></div>
          <div className="sbar-item ok"><span className="sv">2</span><span className="sl">visitados esta semana</span></div>
        </div>

        <div className="card table-card">
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Beneficiario/a</th>
                  <th>Edad</th>
                  <th>Nivel riesgo</th>
                  <th>Días sin retiro</th>
                  <th>Motivo</th>
                  <th>Última visita</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(p => (
                  <tr key={p.id} onClick={() => navigate(`/beneficiario/${p.id}`)}>
                    <td>
                      <div className="name-cell">{p.nombre}</div>
                      <div className="sub">{p.rut} · {p.zona}</div>
                    </td>
                    <td>{p.edad}</td>
                    <td><span className={`pill ${p.nivel}`}>{p.nivel.charAt(0).toUpperCase()+p.nivel.slice(1)}</span></td>
                    <td><span className={`days-badge ${daysBadgeClass(p.dias)}`}>{p.dias} días</span></td>
                    <td className="motivo-cell">{p.motivo}</td>
                    <td className={p.visitaColor ? `visita-${p.visitaColor}` : 'visita-mute'}>{p.ultimaVisita}</td>
                    <td onClick={e => e.stopPropagation()}>
                      <button className="btn btn-sm btn-primary" onClick={() => navigate(`/beneficiario/${p.id}`)}>
                        Ver perfil
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="table-footer">
            <span>Mostrando <strong>{filtered.length}</strong> de 18 beneficiarios en <strong>Curepto</strong> · Ordenado por nivel de riesgo ↓</span>
            <div style={{ display: 'flex', gap: 6 }}>
              <button className="btn btn-sm">← Anterior</button>
              <button className="btn btn-sm">Siguiente →</button>
            </div>
          </div>
        </div>
      </div>

      <div className="mockup-banner">Mockup S5 · Lista No-Retiradores PACAM</div>
    </div>
  )
}
