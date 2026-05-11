import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import TopBar from '../../components/TopBar/TopBar'
import { getBeneficiario } from '../../services/api'
import { PATIENT_DETAIL } from '../../data/mockData'
import './PatientDetail.css'

function colorVar(nivel) {
  return `var(--${nivel})`
}

function buildProfile(data) {
  if (!data) return PATIENT_DETAIL
  const imc = parseFloat(data.imc) || 0
  const imcLabel = imc < 18.5 ? 'bajo peso' : imc < 25 ? 'normal' : imc < 30 ? 'sobrepeso' : 'obesidad'
  const imcNivel = imc < 18.5 ? 'critico' : imc < 25 ? 'bajo' : 'medio'
  const nivelRiesgo = data.nivel_riesgo || 'medio'
  const prob = parseFloat(data.probabilidad_riesgo) || 0.5

  const factores = [
    data.factor_1, data.factor_2, data.factor_3,
  ].filter(Boolean).map((f, i) => ({
    nombre: f, pct: Math.round((0.45 - i * 0.1) * 100), nivel: nivelRiesgo,
  }))

  if (factores.length === 0) {
    factores.push(
      { nombre: 'Puntaje MNA', pct: 46, nivel: nivelRiesgo },
      { nombre: 'IMC', pct: 18, nivel: nivelRiesgo },
      { nombre: 'Inseg. alimentaria', pct: 12, nivel: 'alto' },
    )
  }

  return {
    iniciales: `B${data.id}`,
    nombre: `Beneficiario #${data.id}`,
    rut: `${String(data.id).padStart(7, '0')}-k (protegido)`,
    edad: data.edad,
    sexo: data.sexo === 'F' ? 'Femenino' : 'Masculino',
    comuna: data.comuna || '—',
    zona: data.zona || '—',
    tramoRSH: data.quintil_ingreso ? `Q${data.quintil_ingreso}` : '—',
    scoreRiesgo: prob.toFixed(3),
    nivelRiesgo,
    recomendacion: nivelRiesgo === 'alto'
      ? 'Visita domiciliaria urgente — evaluar derivacion a nutricionista'
      : nivelRiesgo === 'medio'
      ? 'Programar visita de seguimiento en los proximos 15 dias'
      : 'Continuar monitoreo mensual habitual',
    telefono: '—',
    direccion: `${data.zona || ''} · ${data.comuna || ''}`,
    mnaPuntaje: data.puntaje_elcsa || 8,
    mnaEstado: nivelRiesgo,
    mnaEstadoLabel: nivelRiesgo === 'alto' ? 'Desnutricion' : nivelRiesgo === 'medio' ? 'Riesgo' : 'Normal',
    factoresRiesgo: factores,
    comorbilidades: [
      { nombre: 'Diabetes mellitus', valor: data.tiene_diabetes ? 'Sí' : 'No', nivel: data.tiene_diabetes ? 'alto' : null },
      { nombre: 'Hipertension arterial', valor: data.tiene_hipertension ? 'Sí' : 'No', nivel: data.tiene_hipertension ? 'medio' : null },
      { nombre: 'Depresion', valor: data.tiene_depresion ? 'Sí' : 'No', nivel: data.tiene_depresion ? 'alto' : null },
      { nombre: 'Vive solo/a', valor: data.vive_solo ? 'Sí' : 'No', nivel: data.vive_solo ? 'medio' : null },
    ],
    laboratorio: [],
    socioeconomico: {
      tramo: data.quintil_ingreso ? `Quintil ${data.quintil_ingreso}` : '—',
      ingreso: data.ingreso_total ? `$${Number(data.ingreso_total).toLocaleString('es-CL')}` : '—',
      pobreza: data.quintil_ingreso <= 2 ? 'Pobreza por ingresos' : '—',
      pobrezaMulti: '—',
      hogar: '—',
      estadoCivil: data.estado_civil || '—',
      vivienda: '—',
      pension: '—',
      carencias: [],
    },
    pacamEstado: data.acceso_pacam ? 'medio' : 'bajo',
    pacamEstadoLabel: data.acceso_pacam ? 'Inscrito PACAM' : 'No inscrito PACAM',
    pacamMotivoDeclarado: '—',
    pacamHistorial: [],
    imc: data.imc ? `${data.imc} (${imcLabel})` : '—',
    imcNivel,
    pantorrilla: data.circunferencia_pantorrilla ? `${data.circunferencia_pantorrilla} cm` : '—',
    inseguridad: data.nivel_inseguridad || '—',
  }
}

export default function PatientDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [p, setP] = useState(null)
  const [loading, setLoading] = useState(true)
  const [isMock, setIsMock] = useState(false)
  const [contacto, setContacto] = useState('exitoso')
  const [seguimiento, setSeguimiento] = useState('15')
  const [nota, setNota] = useState('')

  useEffect(() => {
    if (id && !isNaN(Number(id))) {
      getBeneficiario(Number(id)).then(({ data, error }) => {
        if (error || !data) {
          setP(buildProfile(null))
          setIsMock(true)
        } else {
          setP(buildProfile(data))
          setIsMock(false)
        }
        setLoading(false)
      })
    } else {
      setP(buildProfile(null))
      setIsMock(true)
      setLoading(false)
    }
  }, [id])

  if (loading) {
    return (
      <div className="page-detail">
        <TopBar subtitle="Vista detalle · Operador JUNAEB" showBack />
        <div style={{ padding: 60, textAlign: 'center', color: 'var(--ink-soft)', fontFamily: 'var(--mono)' }}>
          Cargando perfil…
        </div>
      </div>
    )
  }

  return (
    <div className="page-detail">
      <TopBar subtitle="Vista detalle · Operador JUNAEB" showBack />

      <div className="profile-layout">
        <aside className="profile-sidebar">
          <div className="profile-avatar">{p.iniciales}</div>
          <div className="profile-name">{p.nombre}</div>
          <div className="profile-meta">
            RUT: <span className="light">{p.rut}</span><br/>
            Edad: <span className="light">{p.edad} años</span> · {p.sexo}<br/>
            Comuna: <span className="light">{p.comuna}</span><br/>
            Zona: <span className="light">{p.zona}</span><br/>
            Tramo RSH: <span className="light bold">{p.tramoRSH}</span>
            {isMock && <><br/><span style={{ fontSize: 10, color: 'var(--ink-mute)' }}>datos de muestra</span></>}
          </div>

          <div className="profile-risk-card">
            <div className="risk-card-label">Score de riesgo predicho · Modelo ML v1.0</div>
            <div className="risk-big">{p.scoreRiesgo}<sup>/ 1.0</sup></div>
            <div style={{ marginTop: 10 }}>
              <span className={`pill ${p.nivelRiesgo}`}>● Riesgo {p.nivelRiesgo}</span>
            </div>
            <div className="risk-gauge">
              <div className="gauge-track">
                <div className="gauge-fill" style={{ width: `${parseFloat(p.scoreRiesgo) * 100}%` }} />
              </div>
              <div className="gauge-markers">
                {['0', '.25', '.45', '.70', '1.0'].map(m => <span key={m}>{m}</span>)}
              </div>
            </div>
            <div className="risk-recomendacion">
              <div className="recom-label">Recomendacion automatica</div>
              <div className="recom-text">⚠ {p.recomendacion}</div>
            </div>
          </div>

          <div className="sidebar-section">
            <h4>Contacto</h4>
            <div className="contact-row">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/>
              </svg>
              <span>{p.direccion}</span>
            </div>
          </div>

          <div className="sidebar-actions">
            <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}
              onClick={() => document.getElementById('visit-form').scrollIntoView({ behavior: 'smooth' })}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 5v14M5 12h14"/>
              </svg>
              Registrar visita domiciliaria
            </button>
            <button className="btn" style={{ width: '100%', justifyContent: 'center', background: 'transparent', color: '#B5AC97', borderColor: 'rgba(255,255,255,.15)' }}
              onClick={() => navigate('/beneficiarios')}>
              ← Volver a lista
            </button>
          </div>
        </aside>

        <main className="profile-content">
          <div className="profile-breadcrumb">
            <span className="bc-link" onClick={() => navigate('/beneficiarios')}>Lista beneficiarios</span>
            <span className="bc-sep">›</span>
            <span className="bc-link">{p.comuna}</span>
            <span className="bc-sep">›</span>
            <span>{p.nombre}</span>
          </div>

          <div className="content-grid">

            {/* Estado nutricional */}
            <div className="card">
              <div className="card-head">
                <div className="card-title">Estado nutricional <small>indicadores clinicos</small></div>
              </div>
              <div className="card-body">
                <div className="mna-antropo">
                  <div className="stat-row">
                    <span className="k">IMC</span>
                    <span className="v">{p.imc}</span>
                  </div>
                  <div className="stat-row">
                    <span className="k">Circ. pantorrilla</span>
                    <span className="v">{p.pantorrilla}</span>
                  </div>
                  <div className="stat-row">
                    <span className="k">Inseg. alimentaria</span>
                    <span className="v" style={{ textTransform: 'capitalize' }}>{p.inseguridad}</span>
                  </div>
                  <div className="stat-row">
                    <span className="k">Estado nutricional</span>
                    <span className="v">
                      <span className={`pill ${p.mnaEstado}`}>{p.mnaEstadoLabel}</span>
                    </span>
                  </div>
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
                  Factores que contribuyeron al score de <strong style={{ color: 'var(--ink)' }}>{p.scoreRiesgo}</strong>:
                </p>
                {p.factoresRiesgo.map(f => (
                  <div key={f.nombre} className="factor-row">
                    <span className="fname">{f.nombre}</span>
                    <div className="fbar">
                      <div className="fbar-fill" style={{ width: `${f.pct}%`, background: colorVar(f.nivel) }} />
                    </div>
                    <span className="fval">{f.pct}%</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Perfil clinico */}
            <div className="card">
              <div className="card-head">
                <div className="card-title">Perfil clinico <small>comorbilidades</small></div>
              </div>
              <div className="card-body">
                {p.comorbilidades.map(c => (
                  <div key={c.nombre} className="stat-row">
                    <span className="k">{c.nombre}</span>
                    <span className="v" style={{ color: c.nivel ? colorVar(c.nivel) : 'inherit' }}>
                      {c.valor}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Perfil socioeconomico */}
            <div className="card">
              <div className="card-head">
                <div className="card-title">Perfil socioeconómico <small>RSH · CASEN</small></div>
              </div>
              <div className="card-body">
                <div className="stat-row"><span className="k">Tramo RSH</span><span className="v">{p.socioeconomico.tramo}</span></div>
                <div className="stat-row"><span className="k">Ingreso total hogar</span><span className="v">{p.socioeconomico.ingreso}</span></div>
                <div className="stat-row"><span className="k">Clasificacion pobreza</span><span className="v">{p.socioeconomico.pobreza}</span></div>
                <div className="stat-row"><span className="k">Estado civil</span><span className="v">{p.socioeconomico.estadoCivil}</span></div>
                <div className="stat-row">
                  <span className="k">Acceso PACAM</span>
                  <span className="v">
                    <span className={`pill ${p.pacamEstado}`}>{p.pacamEstadoLabel}</span>
                  </span>
                </div>
              </div>
            </div>

            {/* Formulario visita */}
            <div className="card" id="visit-form" style={{ gridColumn: 'span 2' }}>
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
                      { val: 'rechazo', label: '⊘ Rechazo atencion' },
                    ].map(opt => (
                      <span key={opt.val}
                        className={`r-pill ${contacto === opt.val ? 'active' : ''}`}
                        onClick={() => setContacto(opt.val)}>
                        {opt.label}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="form-group">
                  <label>Nota de observacion (max 300 caracteres)</label>
                  <textarea className="form-textarea" maxLength={300}
                    placeholder="Describa brevemente el resultado de la visita..."
                    value={nota} onChange={e => setNota(e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Programar seguimiento</label>
                  <div className="radio-pills">
                    {[
                      { val: '7', label: 'En 7 dias' },
                      { val: '15', label: 'En 15 dias' },
                      { val: '30', label: 'En 30 dias' },
                      { val: 'none', label: 'Sin seguimiento' },
                    ].map(opt => (
                      <span key={opt.val}
                        className={`r-pill ${seguimiento === opt.val ? 'active' : ''}`}
                        onClick={() => setSeguimiento(opt.val)}>
                        {opt.label}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="form-footer">
                  <div className="form-meta">
                    <span>Beneficiario ID: {id} · Zona: {p.zona}</span>
                  </div>
                  <button className="btn btn-primary">Guardar registro</button>
                </div>
              </div>
            </div>

          </div>
        </main>
      </div>
    </div>
  )
}
