import { useState, useCallback } from 'react'
import TopBar from '../../components/TopBar/TopBar'
import FilterSidebar from '../../components/FilterSidebar/FilterSidebar'
import KPIStrip from '../../components/KPIStrip/KPIStrip'
import MapPanel from '../../components/MapPanel/MapPanel'
import StatsPanel from '../../components/StatsPanel/StatsPanel'
import './Dashboard.css'

export default function Dashboard() {
  // Estado de filtros compartido: FilterSidebar lo produce, los hijos lo consumen
  const [filters, setFilters] = useState({
    region: '07',
    nivelRiesgo: undefined,
    sexos: ['F', 'M'],
    grupos: ['65–74', '75–84', '85+'],
  })

  const handleFiltersChange = useCallback((newFilters) => {
    setFilters(newFilters)
  }, [])

  return (
    <div className="page-dashboard">
      <TopBar />

      {/* Hero */}
      <section className="hero">
        <div className="breadcrumb">
          <a href="#">Inicio</a>
          <span className="sep">/</span>
          <a href="#">Vigilancia nutricional</a>
          <span className="sep">/</span>
          <span>Mapa de riesgo regional</span>
        </div>
        <div className="hero-title">
          <h1>Riesgo de <em>desnutrición</em> en adultos mayores</h1>
          <div className="hero-meta">
            <div className="meta-item">Región: <strong>Maule</strong></div>
            <div className="meta-item">
              Personas: <strong>1.200</strong>
            </div>
            <div className="meta-item">Comunas: <strong>30</strong></div>
            <div className="meta-item">Período: <strong>2025-Q1</strong></div>
          </div>
        </div>
      </section>

      {/* Layout */}
      <div className="dash-layout">
        <FilterSidebar onFiltersChange={handleFiltersChange} />

        <main className="dash-main">
          <KPIStrip filters={filters} />
          <MapPanel filters={filters} />
          <StatsPanel />

          <div className="footnote">
            <strong>Fuente de datos:</strong> dataset sintético piloto basado
            en distribuciones de ESSALCAVI 2024 (INTa Universidad de Chile),
            CASEN 2022 (Ministerio de Desarrollo Social), ENS 2017 (MINSAL),
            RSH y JUNAEB. Las visualizaciones incorporan datos del backend
            cuando está disponible; en caso contrario muestran la muestra
            sintética calibrada.
            <br/><br/>
            <strong>Modelo predictivo:</strong> Árbol de decisión
            (scikit-learn 1.5) entrenado sobre 71 variables. Variable
            objetivo: categoria_mna (3 clases). Etapa: dataset sintético.
          </div>
        </main>
      </div>
    </div>
  )
}
