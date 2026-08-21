import { useState } from 'react'
import { predictRiesgo } from '../../services/api'
import './PredictionPanel.css'

const RIESGO_CONFIG = {
  bajo:    { label: 'Bajo',    color: 'var(--bajo)' },
  medio:   { label: 'Medio',   color: 'var(--medio)' },
  alto:    { label: 'Alto',    color: 'var(--alto)' },
  critico: { label: 'Crítico', color: 'var(--critico)' },
}

const FACTOR_LABELS = {
  imc:               'IMC',
  inseg_alimentaria: 'Inseguridad alimentaria',
  depresion:         'Depresión',
  limitacion_fisica: 'Limitación física',
  diabetes:          'Diabetes',
  vive_solo:         'Vive solo/a',
  perdio_peso:       'Pérdida de peso',
  edad:              'Edad',
  circ_pantorrilla:  'Circ. pantorrilla',
  num_carencias:     'Carencias RSH',
  hta:               'Hipertensión',
  acceso_pacam:      'Acceso PACAM',
}

const INITIAL_FORM = {
  edad: 72,
  sexo: 'F',
  zona: 'urbano',
  imc: '',
  circ_pantorrilla: '',
  perdio_peso: false,
  diabetes: false,
  hta: false,
  depresion: false,
  limitacion_fisica: false,
  inseg_alimentaria: 0,
  acceso_pacam: false,
  vive_solo: false,
  movilidad: 1,
}

export default function PredictionPanel() {
  const [form, setForm] = useState(INITIAL_FORM)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [open, setOpen] = useState(true)

  function handleChange(e) {
    const { name, value, type, checked } = e.target
    setForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked
            : type === 'number'   ? (value === '' ? '' : Number(value))
            : value,
    }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    const payload = { ...form }
    // Limpiar campos vacíos
    Object.keys(payload).forEach(k => {
      if (payload[k] === '') delete payload[k]
    })

    const { data, error: apiError } = await predictRiesgo(payload)
    setLoading(false)

    if (apiError || !data) {
      setError('No se pudo conectar con el backend. Verifica que el servidor esté corriendo.')
      return
    }
    setResult(data)
  }

  function handleReset() {
    setForm(INITIAL_FORM)
    setResult(null)
    setError(null)
  }

  const cfg = result ? (RIESGO_CONFIG[result.riesgo] || RIESGO_CONFIG.medio) : null

  return (
    <section className="prediction-panel">
      <div className="prediction-header" onClick={() => setOpen(o => !o)}>
        <div className="prediction-title">
          Evaluación de riesgo individual
          <small>modelo RandomForest · 17 variables</small>
        </div>
        <button className="prediction-toggle" aria-label="Expandir/Colapsar">
          {open ? '−' : '+'}
        </button>
      </div>

      {open && (
        <div className="prediction-body">
          <form className="pred-form" onSubmit={handleSubmit}>
            <div className="pred-grid">

              {/* Columna 1: Sociodemográfico */}
              <fieldset className="pred-fieldset">
                <legend>Datos del paciente</legend>

                <label>
                  Edad (años)
                  <input type="number" name="edad" min="60" max="120"
                    value={form.edad} onChange={handleChange} required />
                </label>

                <label>
                  Sexo
                  <select name="sexo" value={form.sexo} onChange={handleChange}>
                    <option value="F">Femenino</option>
                    <option value="M">Masculino</option>
                  </select>
                </label>

                <label>
                  Zona
                  <select name="zona" value={form.zona} onChange={handleChange}>
                    <option value="urbano">Urbano</option>
                    <option value="rural">Rural</option>
                  </select>
                </label>

                <label>
                  Movilidad
                  <select name="movilidad" value={form.movilidad} onChange={handleChange}>
                    <option value={0}>En cama / silla</option>
                    <option value={1}>Sale con ayuda</option>
                    <option value={2}>Sale sin ayuda</option>
                  </select>
                </label>

                <label>
                  Inseg. alimentaria
                  <select name="inseg_alimentaria" value={form.inseg_alimentaria} onChange={handleChange}>
                    <option value={0}>Seguro</option>
                    <option value={1}>Leve</option>
                    <option value={2}>Moderada</option>
                    <option value={3}>Severa</option>
                  </select>
                </label>
              </fieldset>

              {/* Columna 2: Antropometría */}
              <fieldset className="pred-fieldset">
                <legend>Medidas clínicas</legend>

                <label>
                  IMC
                  <input type="number" name="imc" min="10" max="50" step="0.1"
                    placeholder="ej. 22.5"
                    value={form.imc} onChange={handleChange} />
                </label>

                <label>
                  Circ. pantorrilla (cm)
                  <input type="number" name="circ_pantorrilla" min="10" max="60" step="0.5"
                    placeholder="ej. 33"
                    value={form.circ_pantorrilla} onChange={handleChange} />
                </label>
              </fieldset>

              {/* Columna 3: Comorbilidades + checkboxes */}
              <fieldset className="pred-fieldset">
                <legend>Antecedentes clínicos</legend>

                {[
                  { name: 'perdio_peso',      label: 'Perdió peso (últimos 3 meses)' },
                  { name: 'diabetes',         label: 'Diabetes mellitus' },
                  { name: 'hta',              label: 'Hipertensión arterial' },
                  { name: 'depresion',        label: 'Depresión diagnosticada' },
                  { name: 'limitacion_fisica',label: 'Limitación física' },
                  { name: 'acceso_pacam',     label: 'Beneficiario/a PACAM' },
                  { name: 'vive_solo',        label: 'Vive solo/a' },
                ].map(({ name, label }) => (
                  <label key={name} className="pred-check">
                    <input type="checkbox" name={name}
                      checked={form[name]} onChange={handleChange} />
                    {label}
                  </label>
                ))}
              </fieldset>
            </div>

            <div className="pred-actions">
              <button type="submit" className="btn-predict" disabled={loading}>
                {loading ? 'Calculando…' : 'Evaluar riesgo'}
              </button>
              <button type="button" className="btn-reset" onClick={handleReset}>
                Limpiar
              </button>
            </div>
          </form>

          {/* Resultado */}
          {error && (
            <div className="pred-error">
              <span>{error}</span>
            </div>
          )}

          {result && cfg && (
            <div className="pred-result" style={{ borderColor: cfg.color }}>
              <div className="result-badge" style={{ background: cfg.color }}>
                <span className="result-label">Riesgo {cfg.label}</span>
              </div>

              <div className="result-details">
                <div className="result-prob">
                  <span className="prob-label">Probabilidad</span>
                  <div className="prob-bar-wrap">
                    <div className="prob-bar"
                      style={{ width: `${Math.round(result.probabilidad * 100)}%`, background: cfg.color }} />
                  </div>
                  <span className="prob-value">{Math.round(result.probabilidad * 100)}%</span>
                </div>

                {result.factores_principales?.length > 0 && (
                  <div className="result-factors">
                    <div className="factors-title">Factores determinantes</div>
                    <div className="factors-list">
                      {result.factores_principales.map((f, i) => (
                        <span key={f} className="factor-chip" style={{ opacity: 1 - i * 0.15 }}>
                          {FACTOR_LABELS[f] || f}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {result.probabilidades?.length > 0 && (
                  <div className="result-probs-all">
                    {result.probabilidades.map(p => {
                      const c = RIESGO_CONFIG[p.nivel]
                      return (
                        <div key={p.nivel} className="prob-row">
                          <span className="prob-nivel" style={{ color: c?.color }}>{c?.label || p.nivel}</span>
                          <div className="prob-mini-bar">
                            <div style={{ width: `${Math.round(p.probabilidad * 100)}%`, background: c?.color || '#888' }} />
                          </div>
                          <span className="prob-mini-val">{Math.round(p.probabilidad * 100)}%</span>
                        </div>
                      )
                    })}
                  </div>
                )}

                {result.usa_fallback && (
                  <div className="fallback-notice">
                    Predicción calculada con heurística clínica (modelo ML no disponible)
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
