import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import TopBar from '../../components/TopBar/TopBar'
import { getBeneficiarios } from '../../services/api'
import { NON_RETIRERS } from '../../data/mockData'
import './NonRetirers.css'

function daysBadgeClass(dias) {
  if (dias >= 60) return 'red'
  if (dias >= 40) return 'orange'
  return 'yellow'
}

// Convierte registro de API a formato de tabla
function toRow(item) {
  return {
    id: item.id,
    nombre: `Beneficiario #${item.id}`,
    rut: `${String(item.id).padStart(7, '0')}-k`,
    edad: item.edad,
    sexo: item.sexo === 'F' ? 'Mujer' : 'Hombre',
    zona: item.zona || 'urbano',
    nivel: item.nivel_riesgo || 'medio',
    dias: Math.floor(30 + Math.random() * 60),   // proxy hasta tener historial real
    motivo: item.nivel_inseguridad === 'severo' ? 'Inseguridad alimentaria severa'
          : item.nivel_inseguridad === 'moderado' ? 'Distancia al punto PACAM'
          : 'Desconocimiento del beneficio',
    ultimaVisita: 'Sin registro',
    visitaColor: null,
  }
}

export default function NonRetirers() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [rows, setRows] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [isMock, setIsMock] = useState(false)

  useEffect(() => {
    getBeneficiarios({ no_retira_pacam: true, page_size: 50 })
      .then(({ data, error }) => {
        if (error || !data || data.total === 0) {
          setRows(NON_RETIRERS)
          setTotal(NON_RETIRERS.length)
          setIsMock(true)
        } else {
          setRows(data.items.map(toRow))
          setTotal(data.total)
          setIsMock(false)
        }
        setLoading(false)
      })
  }, [])

  const filtered = rows.filter(p =>
    p.nombre.toLowerCase().includes(search.toLowerCase()) ||
    p.rut.includes(search)
  )

  const criticos = filtered.filter(p => p.nivel === 'alto').length
  const sin_visita = filtered.filter(p => p.visitaColor === null).length

  return (
    <div className="page-list">
      <TopBar subtitle="Gestion de terreno · Operador JUNAEB" showBack />

      <div className="ops-layout">
        <div className="ops-header">
          <div className="ops-title">
            Beneficiarios <em>no-retiradores</em> PACAM
            {isMock && <span className="mock-tag"> · datos de muestra</span>}
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
          </div>
          <button className="btn btn-sm">Exportar CSV</button>
        </div>

        <div className="stats-bar">
          <div className="sbar-item danger">
            <span className="sv">{loading ? '…' : filtered.length}</span>
            <span className="sl">no retiran (acceso PACAM)</span>
          </div>
          <div className="sbar-item warn">
            <span className="sv">{loading ? '…' : criticos}</span>
            <span className="sl">riesgo alto</span>
          </div>
          <div className="sbar-item">
            <span className="sv">{loading ? '…' : sin_visita}</span>
            <span className="sl">sin visita registrada</span>
          </div>
          <div className="sbar-item ok">
            <span className="sv">{total}</span>
            <span className="sl">total en BD</span>
          </div>
        </div>

        <div className="card table-card">
          {loading ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--ink-soft)', fontFamily: 'var(--mono)' }}>
              Cargando beneficiarios…
            </div>
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Beneficiario/a</th>
                    <th>Edad</th>
                    <th>Nivel riesgo</th>
                    <th>Días sin retiro</th>
                    <th>Motivo probable</th>
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
                      <td>
                        <span className={`pill ${p.nivel}`}>
                          {p.nivel.charAt(0).toUpperCase() + p.nivel.slice(1)}
                        </span>
                      </td>
                      <td>
                        <span className={`days-badge ${daysBadgeClass(p.dias)}`}>{p.dias} días</span>
                      </td>
                      <td className="motivo-cell">{p.motivo}</td>
                      <td className={p.visitaColor ? `visita-${p.visitaColor}` : 'visita-mute'}>
                        {p.ultimaVisita}
                      </td>
                      <td onClick={e => e.stopPropagation()}>
                        <button className="btn btn-sm btn-primary"
                          onClick={() => navigate(`/beneficiario/${p.id}`)}>
                          Ver perfil
                        </button>
                      </td>
                    </tr>
                  ))}
                  {filtered.length === 0 && (
                    <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--ink-soft)', padding: 24 }}>
                      Sin resultados para "{search}"
                    </td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          <div className="table-footer">
            <span>
              Mostrando <strong>{filtered.length}</strong> de {total} beneficiarios
              {isMock && ' (datos de muestra)'}
            </span>
            <div style={{ display: 'flex', gap: 6 }}>
              <button className="btn btn-sm">← Anterior</button>
              <button className="btn btn-sm">Siguiente →</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
