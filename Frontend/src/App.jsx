import { useEffect, useMemo, useRef, useState } from 'react'
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { clearStoredAuth, getStoredAuth, loginWithCredentials, requestJson } from './api'
import Sidebar from './components/Sidebar'
import {
  authSummary,
  buildIncidents,
  buildKpis,
  buildSignals,
  formatHealthStatus,
  getIdentityTags,
  normalizeUser,
  supportPanels,
  supportTables,
} from './utils/helpers'
import OverviewPage from './pages/OverviewPage'
import AuthUsersPage from './pages/AuthUsersPage'
import DataIngestionPage from './pages/DataIngestionPage'
import MlPipelinePage from './pages/MlPipelinePage'
import ResponseEnginePage from './pages/ResponseEnginePage'
import IncidentsEvidencePage from './pages/IncidentsEvidencePage'
import DashboardReportsPage from './pages/DashboardReportsPage'
import SupportTablesPage from './pages/SupportTablesPage'
import LoginPage from './pages/LoginPage'

const sectionFromPath = {
  '/': 'overview',
  '/resumen': 'overview',
  '/auth-users': 'auth-users',
  '/data-ingestion': 'data-ingestion',
  '/ml-pipeline': 'ml-pipeline',
  '/response-engine': 'response-engine',
  '/incidents-evidence': 'incidents-evidence',
  '/dashboard-reports': 'dashboard-reports',
  '/support-tables': 'support-tables',
}

const pathFromSection = {
  overview: '/resumen',
  'auth-users': '/auth-users',
  'data-ingestion': '/data-ingestion',
  'ml-pipeline': '/ml-pipeline',
  'response-engine': '/response-engine',
  'incidents-evidence': '/incidents-evidence',
  'dashboard-reports': '/dashboard-reports',
  'support-tables': '/support-tables',
}

const loginSeed = { username: '', password: '' }

export default function App() {
  const navigate = useNavigate()
  const location = useLocation()
  const [health, setHealth] = useState('cargando')
  const [authState, setAuthState] = useState({ status: 'checking', user: null })
  const [loginForm, setLoginForm] = useState(loginSeed)
  const [loginBusy, setLoginBusy] = useState(false)
  const [authError, setAuthError] = useState('')
  const [sessionNote, setSessionNote] = useState('')
  const [dashboardSummary, setDashboardSummary] = useState(null)
  const [recentIncidents, setRecentIncidents] = useState([])
  const [trafficEvents, setTrafficEvents] = useState([])
  const [responseActions, setResponseActions] = useState([])
  const [detectionResult, setDetectionResult] = useState(null)
  const [trainingResult, setTrainingResult] = useState(null)
  const [dashboardBusy, setDashboardBusy] = useState(false)
  const contentRef = useRef(null)
  const activeSection = sectionFromPath[location.pathname] || 'overview'

  useEffect(() => {
    requestJson('/api/health/', { auth: false })
      .then((data) => setHealth(formatHealthStatus(data.status ?? data.detail ?? 'operativo')))
      .catch(() => setHealth('sin conexión'))
  }, [])

  useEffect(() => {
    const storedAuth = getStoredAuth()

    if (!storedAuth?.accessToken) {
      setAuthState({ status: 'unauthenticated', user: null })
      return
    }

    let active = true

    requestJson('/api/auth/me/')
      .then((profile) => {
        if (!active) return

        setAuthState({ status: 'authenticated', user: normalizeUser(profile) })
        setSessionNote('Sesión restaurada desde los tokens JWT guardados.')
      })
      .catch((error) => {
        if (!active) return

        clearStoredAuth()
        setAuthState({ status: 'unauthenticated', user: null })
        setSessionNote('La sesión expiró. Inicia sesión nuevamente.')
        setAuthError(error.message)
        navigate('/login', { replace: true })
      })

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (authState.status !== 'authenticated') return undefined
    refreshWorkspaceData()
  }, [authState.status])

  const authenticated = authState.status === 'authenticated'
  const user = authState.user
  const identityTags = useMemo(() => getIdentityTags(user), [user])
  const kpis = useMemo(() => buildKpis(dashboardSummary), [dashboardSummary])
  const incidents = useMemo(() => buildIncidents(recentIncidents), [recentIncidents])
  const signals = useMemo(() => buildSignals(dashboardSummary), [dashboardSummary])

  async function refreshWorkspaceData() {
    setDashboardBusy(true)

    try {
      const [summary, eventsData, incidentsData, responsesData] = await Promise.all([
        requestJson('/api/dashboard/summary/'),
        requestJson('/api/events/'),
        requestJson('/api/incidents/'),
        requestJson('/api/responses/'),
      ])

      setDashboardSummary(summary)
      setTrafficEvents(Array.isArray(eventsData) ? eventsData : [])
      setRecentIncidents(Array.isArray(incidentsData) ? incidentsData : [])
      setResponseActions(Array.isArray(responsesData) ? responsesData : [])
      setSessionNote('Resumen operativo sincronizado con el backend.')
    } catch (error) {
      setDashboardSummary(null)
      setTrafficEvents([])
      setRecentIncidents([])
      setResponseActions([])
      setSessionNote(error.message || 'No fue posible sincronizar el dashboard.')
    } finally {
      setDashboardBusy(false)
    }
  }

  function handleNavigate(sectionId) {
    navigate(pathFromSection[sectionId] || '/resumen')
  }

  useEffect(() => {
    contentRef.current?.scrollTo({ top: 0, behavior: 'smooth' })
  }, [activeSection])

  if (authState.status === 'checking') {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <div className="panel-head compact">
            <div>
              <p className="eyebrow">CyberShield AI</p>
              <h2>Verificando autenticación</h2>
            </div>
            <span className="pill success">en línea</span>
          </div>

          <div className="hint">Cargando el perfil protegido desde /api/auth/me/…</div>
        </section>
      </main>
    )
  }

  async function handleLogin(event) {
    event.preventDefault()
    setLoginBusy(true)
    setAuthError('')
    setSessionNote('')

    try {
      await loginWithCredentials(loginForm.username, loginForm.password)
      const profile = await requestJson('/api/auth/me/')
      setAuthState({ status: 'authenticated', user: normalizeUser(profile) })
      setLoginForm(loginSeed)
      setSessionNote('Inicio de sesión exitoso.')
      navigate('/resumen', { replace: true })
    } catch (error) {
      clearStoredAuth()
      setAuthState({ status: 'unauthenticated', user: null })
      setAuthError(error.message || 'No fue posible iniciar sesión.')
      navigate('/login', { replace: true })
    } finally {
      setLoginBusy(false)
    }
  }

  function handleLogout() {
    clearStoredAuth()
    setAuthState({ status: 'unauthenticated', user: null })
    setLoginForm(loginSeed)
    setSessionNote('Sesión cerrada.')
    setDashboardSummary(null)
    setRecentIncidents([])
    setTrafficEvents([])
    setResponseActions([])
    setDetectionResult(null)
    setTrainingResult(null)
    setDashboardBusy(false)
    navigate('/login', { replace: true })
  }

  function handleDetectionResult(type, result) {
    if (type === 'train') {
      setTrainingResult(result)
    } else {
      setDetectionResult(result)
    }
  }

  const sharedPageProps = {
    onDataRefresh: refreshWorkspaceData,
  }

  if (!authenticated) {
    return (
      <Routes>
        <Route
          path="/login"
          element={
            <LoginPage
              authError={authError}
              health={health}
              loginBusy={loginBusy}
              loginForm={loginForm}
              onLogin={handleLogin}
              onLoginFormChange={setLoginForm}
              sessionNote={sessionNote}
            />
          }
        />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }

  return (
    <main className="app-shell">
      <Sidebar
        activeSection={activeSection}
        authSummary={authSummary}
        health={health}
        identityTags={identityTags}
        supportTables={supportTables}
        onLogout={handleLogout}
        onNavigate={handleNavigate}
        user={user}
      />

      <section ref={contentRef} className="content">
        <Routes>
          <Route path="/" element={<Navigate to="/resumen" replace />} />
          <Route path="/login" element={<Navigate to="/resumen" replace />} />
          <Route
            path="/resumen"
            element={
              <OverviewPage
                authSummary={authSummary}
                dashboardBusy={dashboardBusy}
                dashboardSummary={dashboardSummary}
                health={health}
                incidents={incidents}
                kpis={kpis}
                sessionNote={sessionNote}
                signals={signals}
                supportPanels={supportPanels}
                supportTables={supportTables}
                user={user}
                onRefresh={refreshWorkspaceData}
              />
            }
          />
          <Route path="/auth-users" element={<AuthUsersPage authSummary={authSummary} health={health} user={user} />} />
          <Route path="/data-ingestion" element={<DataIngestionPage trafficEvents={trafficEvents} {...sharedPageProps} />} />
          <Route
            path="/ml-pipeline"
            element={
              <MlPipelinePage
                detectionResult={detectionResult}
                trafficEvents={trafficEvents}
                trainingResult={trainingResult}
                onDetectionResult={handleDetectionResult}
                {...sharedPageProps}
              />
            }
          />
          <Route
            path="/response-engine"
            element={<ResponseEnginePage recentIncidents={recentIncidents} responseActions={responseActions} {...sharedPageProps} />}
          />
          <Route
            path="/incidents-evidence"
            element={
              <IncidentsEvidencePage
                dashboardSummary={dashboardSummary}
                trafficEvents={trafficEvents}
                recentIncidents={recentIncidents}
                {...sharedPageProps}
              />
            }
          />
          <Route
            path="/dashboard-reports"
            element={
              <DashboardReportsPage
                dashboardSummary={dashboardSummary}
                detectionResult={detectionResult}
                responseActions={responseActions}
                recentIncidents={recentIncidents}
                trainingResult={trainingResult}
                trafficEvents={trafficEvents}
              />
            }
          />
          <Route path="/support-tables" element={<SupportTablesPage />} />
          <Route path="*" element={<Navigate to="/resumen" replace />} />
        </Routes>
      </section>
    </main>
  )
}
