import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard/Dashboard'
import NonRetirers from './pages/NonRetirers/NonRetirers'
import PatientDetail from './pages/PatientDetail/PatientDetail'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"                   element={<Dashboard />} />
        <Route path="/beneficiarios"      element={<NonRetirers />} />
        <Route path="/beneficiario/:id"   element={<PatientDetail />} />
        <Route path="*"                   element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
