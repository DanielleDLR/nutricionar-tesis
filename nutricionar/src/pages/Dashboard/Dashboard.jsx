import TopBar from '../../components/TopBar/TopBar'
import FilterSidebar from '../../components/FilterSidebar/FilterSidebar'
import KPIStrip from '../../components/KPIStrip/KPIStrip'
import MapPanel from '../../components/MapPanel/MapPanel'
import StatsPanel from '../../components/StatsPanel/StatsPanel'
import './Dashboard.css'

export default function Dashboard() {
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
            <div className="meta-item">Personas: <strong>1.200</strong></div>
            <div className="meta-item">Comunas: <strong>30</strong></div>
            <div className="meta-item">Período: <strong>2025-Q1</strong></div>
          </div>
        </div>
      </section>

      {/* Layout */}
      <div className="dash-layout">
        <FilterSidebar />

        <main className="dash-main">
          <KPIStrip />
          <MapPanel />
          <StatsPanel />

          <div className="footnote">
            <strong>Fuente de datos:</strong> dataset sintético piloto basado en distribuciones de
            ESSALCAVI 2024 (INTa Universidad de Chile), CASEN 2022 (Ministerio de Desarrollo Social),
            ENS 2017 (MINSAL), RSH y JUNAEB. Las visualizaciones son un mockup S3;
            los valores reales se incorporarán con la base definitiva del MIDESO/MINSAL.
            <br/><br/>
            <strong>Modelo predictivo:</strong> Árbol de decisión (scikit-learn 1.5) entrenado sobre 71 variables.
            Variable objetivo: categoria_mna (3 clases). Etapa actual: dataset sintético calibrado.
          </div>
        </main>
      </div>

      <div className="mockup-banner">Mockup S3 · Sin datos reales</div>
    </div>
  )
}
