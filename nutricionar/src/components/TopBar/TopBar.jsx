import { Link, useLocation } from 'react-router-dom'
import './TopBar.css'

export default function TopBar({ subtitle, actions, showBack, onBack }) {
  const location = useLocation()

  return (
    <header className="topbar">
      <div className="brand">
        <div className="brand-mark">N</div>
        <div className="brand-text">
          <div className="b1">Nutricionar</div>
          <div className="b2">{subtitle || 'MINSAL · JUNAEB · Plataforma Predictiva'}</div>
        </div>
      </div>

      <div className="topbar-center hide-mobile">
        <span className="pill-tag">v0.3 · MOCKUP</span>
        Última actualización: 28 mar 2026 · Datos: piloto sintético Maule
      </div>

      <div className="topbar-right">
        {showBack && (
          <Link to="/beneficiarios" className="top-action">
            ← Volver a la lista
          </Link>
        )}
        {!showBack && (
          <>
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
          </>
        )}
        <button className="top-action">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
          </svg>
          <span className="hide-mobile">Exportar PDF</span>
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
