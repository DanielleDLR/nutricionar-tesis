import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { jsPDF } from 'jspdf'
import { getResumen, getComunas, filtersToParams } from '../../services/api'
import './TopBar.css'

/** Descripción legible de los filtros activos para el encabezado del informe. */
function describirFiltros(filters) {
  if (!filters) return 'Ninguno (vista general)'
  const partes = []
  if (filters.region) partes.push(`Región ${filters.region}`)
  if (filters.comuna) partes.push(`Comuna ${filters.comuna}`)
  if (filters.nivelRiesgo) partes.push(`Riesgo ${filters.nivelRiesgo}`)
  if (filters.sexos?.length) partes.push(`Sexo: ${filters.sexos.join(', ')}`)
  if (filters.grupos?.length) partes.push(`Edad: ${filters.grupos.join(', ')}`)
  if (filters.pacam?.length) {
    partes.push(`PACAM: ${[].concat(filters.pacam).join(', ')}`)
  }
  return partes.length ? partes.join(' · ') : 'Ninguno (vista general)'
}

export default function TopBar({
  subtitle,
  showBack,
  backTo = '/',
  backLabel = 'Volver al dashboard',
  filters = null,
}) {
  const location = useLocation()
  const [exportando, setExportando] = useState(false)

  /**
   * Genera un informe nutricional estructurado en texto (no captura de imagen)
   * usando jsPDF. Lee datos frescos de la API en el momento de exportar.
   */
  async function exportarPDF() {
    setExportando(true)
    try {
      const fParams = filtersToParams(filters || {})
      const comunaParams = { ...fParams }
      if (filters?.region) comunaParams.region_cod = filters.region

      const [{ data: resumen }, { data: comunasResp }] = await Promise.all([
        getResumen(fParams),
        getComunas(comunaParams),
      ])

      const r = resumen || {}
      const fmt = (v) =>
        (v == null || isNaN(parseFloat(v))) ? '—' : `${parseFloat(v).toFixed(1)}%`
      const total = r.total_adultos_mayores
      const pctAlto = parseFloat(r.pct_riesgo_alto)
      const nAlto = (total != null && !isNaN(pctAlto))
        ? Math.round((total * pctAlto) / 100)
        : null

      const topComunas = (comunasResp?.comunas || [])
        .slice()
        .sort((a, b) => (b.pct_riesgo_alto_crit || 0) - (a.pct_riesgo_alto_crit || 0))
        .slice(0, 5)

      const pdf = new jsPDF('p', 'mm', 'a4')
      const M = 16
      const W = pdf.internal.pageSize.getWidth()
      let y = 20

      const escribir = (txt, { size = 11, bold = false, dy = 6 } = {}) => {
        pdf.setFont('helvetica', bold ? 'bold' : 'normal')
        pdf.setFontSize(size)
        pdf.text(String(txt), M, y)
        y += dy
      }

      escribir('INFORME NUTRICIONAL — REGIÓN DEL MAULE', { size: 15, bold: true, dy: 9 })
      escribir(`Fecha: ${new Date().toLocaleDateString('es-CL')}`)
      escribir(`Filtros aplicados: ${describirFiltros(filters)}`, { dy: 10 })

      escribir('INDICADORES CLAVE', { size: 12, bold: true, dy: 8 })
      escribir(
        `- Riesgo alto: ${fmt(r.pct_riesgo_alto)}` +
        (nAlto != null ? `  (${nAlto.toLocaleString('es-CL')} personas)` : '')
      )
      escribir(`- Riesgo medio: ${fmt(r.pct_riesgo_medio)}`)
      escribir(`- Inseguridad alimentaria: ${fmt(r.pct_inseguridad_alimentaria)}`)
      escribir(`- Beneficiarios PACAM: ${fmt(r.pct_beneficiarios_pacam)}`, { dy: 10 })

      escribir('COMUNAS CON MAYOR RIESGO', { size: 12, bold: true, dy: 8 })
      if (topComunas.length) {
        topComunas.forEach((c, i) => {
          escribir(
            `${i + 1}. ${c.comuna_nombre} — ${fmt(c.pct_riesgo_alto_crit)} ` +
            `riesgo alto/crítico (${(c.total_personas ?? 0).toLocaleString('es-CL')} personas)`
          )
        })
      } else {
        escribir('Sin datos de comunas disponibles.')
      }
      y += 4

      escribir('NOTAS METODOLÓGICAS', { size: 12, bold: true, dy: 8 })
      const nota =
        'Modelo: RandomForestClassifier · 18 variables · F1-macro 0.7537. ' +
        'Datos: dataset sintético piloto calibrado con ESSALCAVI 2024, ' +
        'CASEN 2022, ENS 2017. Los resultados son apoyo a la decisión y no ' +
        'reemplazan evaluación clínica profesional.'
      pdf.setFont('helvetica', 'normal')
      pdf.setFontSize(10)
      const lineas = pdf.splitTextToSize(nota, W - M * 2)
      pdf.text(lineas, M, y)

      pdf.save(`informe_nutricional_maule_${new Date().toISOString().slice(0, 10)}.pdf`)
    } finally {
      setExportando(false)
    }
  }

  return (
    <header className="topbar">
      <div className="brand">
        <div className="brand-mark">N</div>
        <div className="brand-text">
          <div className="b1">Nutricionar</div>
          <div className="b2">{subtitle || 'MINSAL · APS · Plataforma Predictiva'}</div>
        </div>
      </div>

      <div className="topbar-center hide-mobile">
        <span className="pill-tag">v0.3 · MOCKUP</span>
        Última actualización: 28 mar 2026 · Datos: piloto sintético Maule
      </div>

      <div className="topbar-right">
        {/* El botón de retorno (si aplica) coexiste con la navegación principal:
            no la reemplaza. */}
        {showBack && (
          <Link to={backTo} className="top-action">
            ← {backLabel}
          </Link>
        )}
        <Link
          to="/"
          className={`top-action ${location.pathname === '/' ? 'active' : ''}`}
        >
          Dashboard
        </Link>
        <Link
          to="/beneficiarios"
          className={`top-action ${location.pathname.startsWith('/beneficiarios') ? 'active' : ''}`}
        >
          Beneficiarios
        </Link>
        <button className="top-action" onClick={exportarPDF} disabled={exportando}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
          </svg>
          <span className="hide-mobile">{exportando ? 'Generando…' : 'Exportar PDF'}</span>
        </button>
        <div className="user-chip">
          <div className="avatar">AM</div>
          <div className="hide-mobile">
            <div className="name">A. Méndez</div>
            <div className="role">Analista MINSAL</div>
          </div>
        </div>
      </div>
    </header>
  )
}
