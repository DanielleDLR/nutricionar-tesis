import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import TopBar from '../../components/TopBar/TopBar'
import { getBeneficiario, predictRiesgo, registrarVisita } from '../../services/api'
import { PATIENT_DETAIL } from '../../data/mockData'
import './PatientDetail.css'

function colorVar(nivel) {
  return `var(--${nivel})`
}

// Etiquetas legibles para los nombres de feature del modelo IPRN (RF v1.0).
// Nota: puntaje_mna NO es una feature del modelo (no disponible en ENS/CASEN).
// Las 17 features del modelo estan definidas en backend/ml/features.py.
const FACTOR_LABELS = {
  // Features IPRN — antropometria
  circ_pantorrilla:        'Circ. pantorrilla',
  circ_pantorrilla_baja:   'Circ. pantorrilla baja (<31 cm)',
  imc:                     'IMC',
  imc_bajo_peso:           'IMC bajo peso (<18.5)',
  imc_limite_am:           'IMC limite adulto mayor (<22)',
  perdio_peso:             'Perdida de peso (3 meses)',
  // Features IPRN — inseguridad alimentaria
  inseg_alimentaria:       'Inseg. alimentaria',
  inseg_alimentaria_severa:   'Inseg. alimentaria severa',
  inseg_alimentaria_moderada: 'Inseg. alimentaria moderada',
  // Features IPRN — salud
  depresion:               'Depresion',
  limitacion_fisica:       'Limitacion fisica',
  movilidad_reducida:      'Movilidad reducida',
  diabetes:                'Diabetes',
  hta:                     'Hipertension arterial',
  // Features IPRN — contexto social
  vive_solo:               'Vive solo/a',
  edad_avanzada:           'Edad avanzada (>85)',
  num_carencias:           'Carencias RSH',
  hacinamiento:            'Hacinamiento',
  // Features IPRN — otras
  ingreso_per_capita:      'Ingreso per capita',
  acceso_pacam:            'Acceso PACAM',
  movilidad_num:           'Movilidad',
  sexo_num:                'Sexo',
  zona_num:                'Zona',
}

function _prettyFactor(nombre) {
  return FACTOR_LABELS[nombre] ||
    String(nombre).replace(/_/g, ' ').replace(/^\w/, c => c.toUpperCase())
}

/**
 * Convierte una lista ordenada de nombres de factor (de mayor a menor
 * importancia) en objetos para la barra, con porcentajes descendentes.
 * Nota: el endpoint expone los factores ya ordenados pero sin el score numérico
 * crudo, por lo que la contribución se estima por rango.
 */
function factoresDesdeNombres(nombres, nivel) {
  const lista = (nombres || []).filter(Boolean)
  const n = lista.length || 1
  return lista.map((nm, i) => ({
    nombre: _prettyFactor(nm),
    pct: Math.max(8, Math.round(45 - i * (33 / Math.max(n - 1, 1)))),
    nivel,
  }))
}

// Inseguridad alimentaria textual → código numérico que espera el modelo.
const INSEG_COD = { seguro: 0, leve: 1, moderado: 2, severo: 3 }

/** Construye el payload de predicción a partir del detalle del beneficiario. */
function payloadPrediccion(data) {
  const payload = {
    edad: data.edad,
    sexo: data.sexo,
    zona: data.zona || 'urbano',
    depresion: !!data.tiene_depresion,
    diabetes: !!data.tiene_diabetes,
    hta: !!data.tiene_hipertension,
    vive_solo: !!data.vive_solo,
    acceso_pacam: !!data.acceso_pacam,
    inseg_alimentaria: INSEG_COD[data.nivel_inseguridad] ?? 0,
  }
  if (data.imc != null && data.imc !== '') payload.imc = parseFloat(data.imc)
  if (data.circunferencia_pantorrilla != null) payload.circ_pantorrilla = parseFloat(data.circunferencia_pantorrilla)
  // puntaje_mna no se envia: no es una feature del modelo IPRN (ver ml/features.py)
  return payload
}

function buildProfile(data) {
  if (!data) {
    // Hace visible en desarrollo que se está usando el perfil de muestra
    // (María del Carmen) por falta de respuesta real de la API.
    console.warn(
      '[PatientDetail] Sin datos de la API para este beneficiario; ' +
      'se muestra el perfil de referencia (mock).'
    )
    return PATIENT_DETAIL
  }
  const imc = parseFloat(data.imc) || 0
  const imcLabel = imc < 18.5 ? 'bajo peso' : imc < 25 ? 'normal' : imc < 30 ? 'sobrepeso' : 'obesidad'
  const imcNivel = imc < 18.5 ? 'critico' : imc < 25 ? 'bajo' : 'medio'
  const nivelRiesgo = data.nivel_riesgo || 'medio'
  const prob = parseFloat(data.probabilidad_riesgo) || 0.5

  // Factores de respaldo (cuando la predicción ML no está disponible): se parte
  // de factor_1/2/3 de la BD y se complementa con factores clínicos presentes
  // en los datos, para no mostrar uno solo.
  // Factores de respaldo en orden de importancia del modelo RF (circ_pantorrilla > imc).
  // Se usa cuando la prediccion ML no esta disponible o no retorna factores.
  const nombresDb = [data.factor_1, data.factor_2, data.factor_3].filter(Boolean)
  const candidatos = [...nombresDb]
  if (data.circunferencia_pantorrilla != null) candidatos.push('circ_pantorrilla')
  if (data.imc != null) candidatos.push('imc')
  if (data.nivel_inseguridad && data.nivel_inseguridad !== 'seguro') {
    candidatos.push('inseg_alimentaria')
  }
  if (data.tiene_depresion) candidatos.push('depresion')
  if (data.vive_solo) candidatos.push('vive_solo')
  if (data.tiene_diabetes) candidatos.push('diabetes')
  const nombresUnicos = [...new Set(candidatos)].slice(0, 5)
  const factores = factoresDesdeNombres(
    nombresUnicos.length ? nombresUnicos : ['circ_pantorrilla', 'imc', 'inseg_alimentaria'],
    nivelRiesgo,
  )

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
    // iprnScore: proxy observable (0-1) calculado por el modelo RF.
    // Reemplaza al puntaje MNA clinico, no disponible en fuentes reales.
    iprnScore: prob.toFixed(3),
    estadoNutricional: nivelRiesgo,
    estadoNutricionalLabel: {
      critico: 'Riesgo critico (IPRN >= 0.62)',
      alto:    'Riesgo alto (IPRN >= 0.42)',
      medio:   'Riesgo medio (IPRN >= 0.22)',
      bajo:    'Sin riesgo significativo',
    }[nivelRiesgo] || 'Riesgo medio',
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
  const [guardando, setGuardando] = useState(false)
  const [msgVisita, setMsgVisita] = useState(null)   // { tipo: 'ok'|'error', texto }

  useEffect(() => {
    if (id && !isNaN(Number(id))) {
      getBeneficiario(Number(id)).then(({ data, error }) => {
        if (error || !data) {
          setP(buildProfile(null))
          setIsMock(true)
          setLoading(false)
          return
        }
        const perfil = buildProfile(data)
        setP(perfil)
        setIsMock(false)
        setLoading(false)
        // Segunda llamada: factores de riesgo con scores del modelo ML.
        predictRiesgo(payloadPrediccion(data)).then(({ data: pred, error: e }) => {
          if (!e && pred?.factores_principales?.length) {
            const factores = factoresDesdeNombres(
              pred.factores_principales, pred.riesgo || perfil.nivelRiesgo,
            )
            setP(prev => (prev ? { ...prev, factoresRiesgo: factores } : prev))
          }
        })
      })
    } else {
      setP(buildProfile(null))
      setIsMock(true)
      setLoading(false)
    }
  }, [id])

  async function handleGuardarVisita() {
    if (!nota.trim()) {
      setMsgVisita({ tipo: 'error', texto: 'Ingresa una observación antes de guardar' })
      return
    }
    setGuardando(true)
    setMsgVisita(null)
    const { data, error } = await registrarVisita(id, {
      contacto,
      nota: nota.trim(),
      seguimiento_dias: parseInt(seguimiento, 10) || null,
    })
    setGuardando(false)
    if (error || !data?.ok) {
      setMsgVisita({ tipo: 'error', texto: 'Error al guardar. Intenta nuevamente.' })
      return
    }
    setMsgVisita({ tipo: 'ok', texto: 'Registro guardado correctamente' })
    setNota('')
    setContacto('exitoso')
    setSeguimiento('15')
    setTimeout(() => setMsgVisita(null), 3000)
  }

  if (loading) {
    return (
      <div className="page-detail">
        <TopBar subtitle="Vista detalle · Equipo APS" />
        <div style={{ padding: 60, textAlign: 'center', color: 'var(--ink-soft)', fontFamily: 'var(--mono)' }}>
          Cargando perfil…
        </div>
      </div>
    )
  }

  return (
    <div className="page-detail">
      <TopBar subtitle="Vista detalle · Equipo APS" />

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
              <span className={`pill ${p.nivelRiesgo}`}>Riesgo {p.nivelRiesgo}</span>
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
              <div className="recom-text">{p.recomendacion}</div>
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
                      <span className={`pill ${p.estadoNutricional}`}>{p.estadoNutricionalLabel}</span>
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
                      { val: 'exitoso', label: 'Contacto exitoso' },
                      { val: 'no-encontrado', label: 'No encontrado/a' },
                      { val: 'rechazo', label: 'Rechazo atencion' },
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
                {msgVisita && (
                  <div className="form-group" style={{
                    color: msgVisita.tipo === 'ok' ? 'var(--bajo)' : 'var(--critico)',
                    fontSize: 13, fontWeight: 600,
                  }}>
                    {msgVisita.texto}
                  </div>
                )}
                <div className="form-footer">
                  <div className="form-meta">
                    <span>Beneficiario ID: {id} · Zona: {p.zona}</span>
                  </div>
                  <button className="btn btn-primary"
                    onClick={handleGuardarVisita} disabled={guardando}>
                    {guardando ? 'Guardando...' : 'Guardar registro'}
                  </button>
                </div>
              </div>
            </div>

          </div>
        </main>
      </div>
    </div>
  )
}
