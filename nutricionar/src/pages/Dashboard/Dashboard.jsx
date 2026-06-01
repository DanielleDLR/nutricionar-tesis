import { useState, useCallback } from 'react'
import TopBar from '../../components/TopBar/TopBar'
import FilterSidebar from '../../components/FilterSidebar/FilterSidebar'
import KPIStrip from '../../components/KPIStrip/KPIStrip'
import MapPanel from '../../components/MapPanel/MapPanel'
import TendenciasChart from '../../components/TendenciasChart/TendenciasChart'
import StatsPanel from '../../components/StatsPanel/StatsPanel'
import PredictionPanel from '../../components/PredictionPanel/PredictionPanel'
import './Dashboard.css'

export default function Dashboard() {
  const [filters, setFilters] = useState({
    region: '07',
    nivelRiesgo: undefined,
    sexos: ['F', 'M'],
    grupos: ['65-74', '75-84', '85+'],
  })

  const handleFiltersChange = useCallback((newFilters) => {
    setFilters(newFilters)
  }, [])

  return (
    <div className="page-dashboard">
      <a href="#contenido-principal" className="skip-link">Saltar al contenido</a>
      <TopBar />

      <section className="hero">
        <div className="breadcrumb">
          <a href="#">Inicio</a>
          <span className="sep">/</span>
          <a href="#">Vigilancia nutricional</a>
          <span className="sep">/</span>
          <span>Mapa de riesgo regional</span>
        </div>
        <div className="hero-title">
          <h1>Riesgo de <em>desnutricion</em> en adultos mayores</h1>
          <div className="hero-meta">
            <div className="meta-item">Region: <strong>Maule</strong></div>
            <div className="meta-item">Personas: <strong>1.200</strong></div>
            <div className="meta-item">Comunas: <strong>30</strong></div>
            <div className="meta-item">Periodo: <strong>2025-Q1</strong></div>
          </div>
        </div>
      </section>

      <div className="dash-layout">
        <FilterSidebar onFiltersChange={handleFiltersChange} />

        <main id="contenido-principal" className="dash-main">
          <KPIStrip filters={filters} />
          <MapPanel filters={filters} />
          <TendenciasChart filters={filters} />
          <StatsPanel filters={filters} />
          <PredictionPanel />

          <div className="footnote">
            <strong>Fuente de datos:</strong> dataset sintetico piloto basado
            en distribuciones de ESSALCAVI 2024 (INTa Universidad de Chile),
            CASEN 2022 (Ministerio de Desarrollo Social), ENS 2017 (MINSAL),
            RSH y JUNAEB. Las visualizaciones incorporan datos del backend
            cuando esta disponible; en caso contrario muestran la muestra
            sintetica calibrada.
            <br/><br/>
            <strong>Modelo predictivo:</strong> RandomForestClassifier
            (scikit-learn) entrenado sobre 18 variables, 1.200 registros.
            F1-macro CV 5-fold: 0.813. Variable objetivo: nivel_riesgo (4 clases).
          </div>
        </main>
      </div>
    </div>
  )
}
