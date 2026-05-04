import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import TopBar from '../../components/TopBar/TopBar'
import { PATIENT_DETAIL } from '../../data/mockData'
import './PatientDetail.css'

export default function PatientDetail() {
  const navigate = useNavigate()
  const p = PATIENT_DETAIL
  const [contacto, setContacto] = useState('exitoso')
  const [seguimiento, setSeguimiento] = useState('15')
  const [nota, setNota] = useState('')

  const colorVar = nivel => `var(--${nivel})`

  return (
    <div className="page-detail">
      <TopBar subtitle="Vista detalle · Operador JUNAEB" showBack />

      <div className="profile-layout">

        {/* ── SIDEBAR ── */}
        <aside className="profile-sidebar">
          <div className="profile-avatar">{p.iniciales}</div>
          <div className="profile-name">{p.nombre}</div>
          <div className="profile-meta">
            RUT: <span className="light">{p.rut}</span> (protegido)<br/>
            Edad: <span className="light">{p.edad} años</span> · {p.sexo}<br/>
            Comuna: <span className="light">{p.comuna}</span><br/>
            Zona: <span className="light">{p.zona}</span><br/>
            Tramo RSH: <span className="light bold">{p.tramoRSH}</span> (máxima vulnerabilidad)
          </div>

          {/* Risk score */}
          <div className="profile-risk-card">
            <div className="risk-card-label">Score de riesgo predicho · Modelo ML v1.0</div>
            <div className="risk-big">{p.scoreRiesgo}<sup>/ 1.0</sup></div>
            <div style={{ marginTop: 10 }}>
              <span className={`pill ${p.nivelRiesgo}`}>● Riesgo crítico</span>
            </div>
            <div className="risk-gauge">
              <div className="gauge-track">
                <div className="gauge-fill" style={{ width: `${p.scoreRiesgo * 100}%` }} />
              </div>
              <div className="gauge-markers">
                {['0', '.25', '.45', '.70', '1.0'].map(m => <span key={m}>{m}</span>)}
              </div>
            </div>
            <div className="risk-recomendacion">
              <div className="recom-label">Recomendación automática</div>
              <div className="recom-text">⚠ {p.recomendacion}</div>
            </div>
          </div>

          {/* Contact */}
          <div className="sidebar-section">
            <h4>Contacto</h4>
            <div className="contact-row">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z"/>
              </svg>
              <span>{p.telefono}</span>
            </div>
            <div className="contact-row">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/>
              </svg>
              <span>{p.direccion}</span>
            </div>
          </div>

          {/* Actions */}
          <div className="sidebar-actions">
            <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}
              onClick={() => document.getElementById('visit-form').scrollIntoView({ behavior: 'smooth' })}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 5v14M5 12h14"/>
              </svg>
              Registrar visita domiciliaria
            </button>
            <button className="btn" style={{ width: '100%', justifyContent: 'center', background: 'transparent', color: '#B5AC97', borderColor: 'rgba(255,255,255,.15)' }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
              </svg>
              Iniciar inscripción PACAM
            </button>
          </div>
        </aside>

        {/* ── CONTENT ── */}
        <main className="profile-content">
          <div className="profile-breadcrumb">
            <span className="bc-link" onClick={() => navigate('/beneficiarios')}>Lista beneficiarios</span>
            <span className="bc-sep">›</span>
            <span className="bc-link">Curepto</span>
            <span className="bc-sep">›</span>
            <span>{p.nombre}</span>
            <span className="bc-badge">última visita hace 47 días</span>
          </div>

          <div className="content-grid">

            {/* MNA */}
            <div className="card">
              <div className="card-head">
                <div className="card-title">Estado nutricional <small>MNA · ENS 2017</small></div>
              </div>
              <div className="card-body">
                <div className="mna-radial">
                  <div className="mna-ring">
                    <svg viewBox="0 0 120 120">
                      <circle cx="60" cy="60" r="50" fill="none" stroke="#F2EEE5" strokeWidth="10"/>
                      <circle cx="60" cy="60" r="50" fill="none"
                        stroke="var(--critico)" strokeWidth="10"
                        strokeDasharray={`${(p.mnaPuntaje/14)*314.16} 314.16`}
                        strokeLinecap="round"/>
                    </svg>
                    <div className="mna-center">
                      <div className="mna-v" style={{ color: 'var(--critico)' }}>{p.mnaPuntaje}</div>
                      <div className="mna-l">de 14</div>
                    </div>
                  </div>
                  <div className="mna-detail">
                    <div style={{ marginBottom: 8 }}>
                      <span className={`pill ${p.mnaEstado}`}>{p.mnaEstadoLabel}</span>
                    </div>
                    {[
                      { k: 'Pérdida de peso (3m)', v: 'Sí', nivel: 'critico' },
                      { k: 'Movilidad', v: 'Se levanta, no sale', nivel: null },
                      { k: 'Estrés / enf. aguda', v: 'Sí', nivel: 'critico' },
                      { k: 'Demencia/depresión', v: 'Depresión leve', nivel: 'alto' },
                    ].map(item => (
                      <div key={item.k} className="mna-item">
                        <span className="k">{item.k}</span>
                        <span className="v" style={{ color: item.nivel ? `var(--${item.nivel})` : 'inherit' }}>
                          {item.v}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="mna-antropo">
                  <div className="stat-row"><span className="k">IMC</span><span className="v">19.8 <span style={{ color: 'var(--critico)', fontWeight: 400, fontSize: 11 }}>(bajo peso)</span></span></div>
                  <div className="stat-row"><span className="k">Circ. pantorrilla</span><span className="v">26.3 cm <span style={{ color: 'var(--critico)', fontWeight: 400, fontSize: 11 }}>(&lt;31)</span></span></div>
                  <div className="stat-row"><span className="k">Circ. braquial</span><span className="v">22.1 cm</span></div>
                </div>
              </div>
            </div>

            {/* Factores de riesgo */}
            <div className="card">
              <div className="card-head">
                <div className="card-title">Factores de riesgo <small>feature importance · modelo ML</small></div>
              </div>
              <div className="card-body">
                <p style={{ fontSize: 11, color: 'var(--ink-mute)', marginBottom: 12 }}>
                  Los 5 factores que más contribuyeron al score de <strong style={{ color: 'var(--ink)' }}>{p.scoreRiesgo}</strong>:
                </p>
                {p.factoresRiesgo.map(f => (
                  <div key={f.nombre} className="factor-row">
                    <span className="fname">{f.nombre}</span>
                    <div className="fbar"><div className="fbar-fill" style={{ width: `${f.pct}%`, background: colorVar(f.nivel) }} /></div>
                    <span className="fval">{f.pct}%</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Perfil clínico */}
            <div className="card">
              <div className="card-head">
                <div className="card-title">Perfil clínico <small>comorbilidades</small></div>
              </div>
              <div className="card-body">
                {p.comorbilidades.map(c => (
                  <div key={c.nombre} className="stat-row">
                    <span className="k">{c.nombre}</span>
                    <span className="v" style={{ color: c.nivel ? `var(--${c.nivel})` : 'inherit' }}>{c.valor}</span>
                  </div>
                ))}
                <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px dashed var(--line)' }}>
                  <div className="label-mono" style={{ marginBottom: 6 }}>Laboratorio (ene-2025)</div>
                  {p.laboratorio.map(l => (
                    <div key={l.nombre} className="stat-row">
                      <span className="k">{l.nombre}</span>
                      <span className="v" style={{ color: `var(--${l.nivel})` }}>
                        {l.valor} {l.nota && <span style={{ fontWeight: 400, fontSize: 10 }}>{l.nota}</span>}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Historial PACAM */}
            <div className="card">
              <div className="card-head">
                <div className="card-title">Historial PACAM <small>últimos 6 meses</small></div>
              </div>
              <div className="card-body">
                <div style={{ marginBottom: 14 }}>
                  <span className={`pill ${p.pacamEstado}`}>{p.pacamEstadoLabel}</span>
                  <p style={{ fontSize: 12, color: 'var(--ink-soft)', marginTop: 6 }}>
                    Motivo declarado: <strong style={{ color: 'var(--ink)' }}>{p.pacamMotivoDeclarado}</strong>
                  </p>
                </div>
                <div className="timeline">
                  {p.pacamHistorial.map((h, i) => (
                    <div key={i} className={`tl-item ${h.retiró ? 'ok' : 'missed'}`}>
                      <div className="tl-date">{h.mes}</div>
                      <div className="tl-action" style={{ color: h.retiró ? 'var(--bajo)' : 'var(--critico)' }}>
                        {h.retiró ? '✓ Retiró' : '✗ No retiró'}
                      </div>
                      {h.nota && <div className="tl-note">{h.nota}</div>}
                    </div>
                  ))}
                </div>
                <div className="pacam-summary">
                  <strong>Tasa de retiro 6 meses:</strong> 2 de 6 (33%) — 4 retiros perdidos
                </div>
              </div>
            </div>

            {/* Socioeconómico */}
            <div className="card">
              <div className="card-head">
                <div className="card-title">Perfil socioeconómico <small>RSH · CASEN</small></div>
              </div>
              <div className="card-body">
                <div className="stat-row"><span className="k">Tramo RSH</span><span className="v" style={{ color: 'var(--critico)' }}>{p.socioeconomico.tramo}</span></div>
                <div className="stat-row"><span className="k">Ingreso per cápita</span><span className="v">{p.socioeconomico.ingreso}</span></div>
                <div className="stat-row"><span className="k">Clasificación pobreza</span><span className="v" style={{ color: 'var(--critico)' }}>{p.socioeconomico.pobreza}</span></div>
                <div className="stat-row"><span className="k">Pobreza multidimensional</span><span className="v" style={{ color: 'var(--critico)' }}>{p.socioeconomico.pobrezaMulti}</span></div>
                <div className="stat-row"><span className="k">Integrantes hogar</span><span className="v">{p.socioeconomico.hogar}</span></div>
                <div className="stat-row"><span className="k">Estado civil</span><span className="v">{p.socioeconomico.estadoCivil}</span></div>
                <div className="stat-row"><span className="k">Tipo vivienda</span><span className="v">{p.socioeconomico.vivienda}</span></div>
                <div className="stat-row"><span className="k">Pensión</span><span className="v">{p.socioeconomico.pension}</span></div>
                <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px dashed var(--line)' }}>
                  <div className="label-mono" style={{ marginBottom: 8 }}>Carencias RSH</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {p.socioeconomico.carencias.map(c => (
                      <span key={c} style={{ padding: '3px 8px', background: 'var(--critico-bg)', color: 'var(--critico)', borderRadius: 99, fontSize: 10, fontFamily: 'var(--mono)' }}>{c}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Formulario visita */}
            <div className="card" id="visit-form">
              <div className="card-head" style={{ background: 'var(--teal)' }}>
                <div className="card-title" style={{ color: '#FFF' }}>
                  Registrar visita domiciliaria <small style={{ color: 'rgba(255,255,255,.6)' }}>US-09</small>
                </div>
              </div>
              <div className="card-body">
                <div className="form-group">
                  <label>Estado del contacto</label>
                  <div className="radio-pills">
                    {[
                      { val: 'exitoso', label: '✓ Contacto exitoso' },
                      { val: 'no-encontrado', label: '✗ No encontrado/a' },
                      { val: 'rechazo', label: '⊘ Rechazó atención' },
                    ].map(opt => (
                      <span
                        key={opt.val}
                        className={`r-pill ${contacto === opt.val ? 'active' : ''}`}
                        onClick={() => setContacto(opt.val)}
                      >{opt.label}</span>
                    ))}
                  </div>
                </div>
                <div className="form-group">
                  <label>Nota de observación (máx 300 caracteres)</label>
                  <textarea
                    className="form-textarea"
                    maxLength={300}
                    placeholder="Describa brevemente el resultado de la visita..."
                    value={nota}
                    onChange={e => setNota(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Programar seguimiento</label>
                  <div className="radio-pills">
                    {[
                      { val: '7', label: 'En 7 días' },
                      { val: '15', label: 'En 15 días' },
                      { val: '30', label: 'En 30 días' },
                      { val: 'none', label: 'Sin seguimiento' },
                    ].map(opt => (
                      <span
                        key={opt.val}
                        className={`r-pill ${seguimiento === opt.val ? 'active' : ''}`}
                        onClick={() => setSeguimiento(opt.val)}
                      >{opt.label}</span>
                    ))}
                  </div>
                </div>
                <div className="form-footer">
                  <div className="form-meta">
                    <span>📍 Geolocalización: -35.0901, -72.0231 (Curepto)</span><br/>
                    <span>👤 Operador: J. Muñoz · JUNAEB Maule</span>
                  </div>
                  <button className="btn btn-primary">Guardar registro</button>
                </div>
              </div>
            </div>

          </div>
        </main>
      </div>

      <div className="mockup-banner">Mockup S5 · Vista detalle adulto mayor</div>
    </div>
  )
}
