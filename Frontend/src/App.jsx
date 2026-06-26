import { useEffect, useMemo, useRef, useState } from 'react'
import { clearStoredAuth, getStoredAuth, loginWithCredentials, requestJson } from './api'
import Sidebar from './components/Sidebar'
import { sidebarModules } from './navigation'
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

const loginSeed = { username: '', password: '' }

export default function App() {
  const [health, setHealth] = useState('cargando')
  const [authState, setAuthState] = useState({ status: 'checking', user: null })
  const [loginForm, setLoginForm] = useState(loginSeed)
  const [loginBusy, setLoginBusy] = useState(false)
  const [authError, setAuthError] = useState('')
  const [sessionNote, setSessionNote] = useState('')
  const [activeSection, setActiveSection] = useState(sidebarModules[0].items[0].id)
  const [dashboardSummary, setDashboardSummary] = useState(null)
  const [recentIncidents, setRecentIncidents] = useState([])
  const [trafficEvents, setTrafficEvents] = useState([])
  const [responseActions, setResponseActions] = useState([])
  const [detectionResult, setDetectionResult] = useState(null)
  const [trainingResult, setTrainingResult] = useState(null)
  const [dashboardBusy, setDashboardBusy] = useState(false)
  const contentRef = useRef(null)

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
    setActiveSection(sectionId)
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
    } catch (error) {
      clearStoredAuth()
      setAuthState({ status: 'unauthenticated', user: null })
      setAuthError(error.message || 'No fue posible iniciar sesión.')
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
    setActiveSection(sidebarModules[0].items[0].id)
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

  function renderPage() {
    switch (activeSection) {
      case 'overview':
        return (
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
        )
      case 'auth-users':
        return <AuthUsersPage authSummary={authSummary} health={health} user={user} />
      case 'data-ingestion':
        return <DataIngestionPage trafficEvents={trafficEvents} {...sharedPageProps} />
      case 'ml-pipeline':
        return (
          <MlPipelinePage
            detectionResult={detectionResult}
            trafficEvents={trafficEvents}
            trainingResult={trainingResult}
            onDetectionResult={handleDetectionResult}
            {...sharedPageProps}
          />
        )
      case 'response-engine':
        return <ResponseEnginePage recentIncidents={recentIncidents} responseActions={responseActions} {...sharedPageProps} />
      case 'incidents-evidence':
        return (
          <IncidentsEvidencePage
            dashboardSummary={dashboardSummary}
            trafficEvents={trafficEvents}
            recentIncidents={recentIncidents}
            {...sharedPageProps}
          />
        )
      case 'dashboard-reports':
        return (
          <DashboardReportsPage
            dashboardSummary={dashboardSummary}
            detectionResult={detectionResult}
            responseActions={responseActions}
            recentIncidents={recentIncidents}
            trainingResult={trainingResult}
            trafficEvents={trafficEvents}
          />
        )
      case 'support-tables':
        return <SupportTablesPage />
      default:
        return (
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
        )
    }
  }

  if (!authenticated) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <div className="panel-head compact">
            <div>
              <p className="eyebrow">CyberShield AI</p>
              <h2>Acceso</h2>
            </div>
            <span className={`pill ${health === 'sin conexión' ? 'danger' : 'success'}`}>{health}</span>
          </div>

          <form className="auth-form" onSubmit={handleLogin}>
            <label>
              <span>Usuario</span>
              <input
                autoComplete="username"
                autoFocus
                value={loginForm.username}
                onChange={(event) => setLoginForm({ ...loginForm, username: event.target.value })}
                placeholder="demo"
                required
              />
            </label>

            <label>
              <span>Contraseña</span>
              <input
                autoComplete="current-password"
                type="password"
                value={loginForm.password}
                onChange={(event) => setLoginForm({ ...loginForm, password: event.target.value })}
                placeholder="••••••••"
                required
              />
            </label>

            {authError ? <div className="alert">{authError}</div> : null}
            {sessionNote ? <div className="hint">{sessionNote}</div> : null}

            <button className="primary-button wide" disabled={loginBusy} type="submit">
              {loginBusy ? 'Iniciando sesión…' : 'Entrar'}
            </button>
          </form>
        </section>
      </main>
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
        {renderPage()}
      </section>
    </main>
  )
}
