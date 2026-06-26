import { useState } from 'react'
import { downloadJson, formatCount, safeNumber } from '../utils/helpers'

export default function DashboardReportsPage({
  dashboardSummary,
  detectionResult,
  responseActions,
  recentIncidents,
  trainingResult,
  trafficEvents,
}) {
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState('')

  async function handleExport() {
    setBusy(true)
    setNote('')

    try {
      const report = {
        generatedAt: new Date().toISOString(),
        summary: dashboardSummary,
        trafficEvents: trafficEvents.slice(0, 10),
        incidents: recentIncidents.slice(0, 10),
        responseActions: responseActions.slice(0, 10),
        detectionResult,
        trainingResult,
      }

      downloadJson('cybershield-report.json', report)
      setNote('Reporte exportado correctamente.')
    } catch (error) {
      setNote(error.message || 'No fue posible exportar el reporte.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <section className="overview-section" data-nav-section id="dashboard-reports">
        <header className="topbar">
          <div>
            <p className="eyebrow">Módulo 6</p>
            <h2>Dashboard y reportes</h2>
          </div>
          <span className="pill success">{busy ? 'Exportando…' : 'Reporte listo'}</span>
        </header>

        <p className="muted">
          Métricas clave, resumen ejecutivo y exportación local del reporte en JSON.
        </p>

        <div className="mini-summary-grid">
          <div className="summary-block">
            <strong>{formatCount(dashboardSummary?.events_total)}</strong>
            <p className="muted compact-copy">Eventos analizados.</p>
          </div>
          <div className="summary-block">
            <strong>{formatCount(dashboardSummary?.high_risk_detections)}</strong>
            <p className="muted compact-copy">Detecciones de alto riesgo.</p>
          </div>
          <div className="summary-block">
            <strong>{formatCount(dashboardSummary?.open_incidents)}</strong>
            <p className="muted compact-copy">Incidentes abiertos.</p>
          </div>
          <div className="summary-block">
            <strong>{formatCount(dashboardSummary?.response_actions_total)}</strong>
            <p className="muted compact-copy">Acciones de respuesta.</p>
          </div>
        </div>

        <div className="report-chart">
          <div>
            <span>Detecciones de alto riesgo</span>
            <strong>{formatCount(dashboardSummary?.high_risk_detections)}</strong>
          </div>
          <div className="bar">
            <span style={{ width: `${Math.min(100, safeNumber(dashboardSummary?.high_risk_detection_rate) * 100)}%` }} />
          </div>
        </div>

        {note ? <div className="hint">{note}</div> : null}

        <button className="primary-button" disabled={busy} onClick={handleExport} type="button">
          {busy ? 'Exportando reporte…' : 'Exportar reporte'}
        </button>
      </section>

      <section className="footer-note">
        <p>Diseñado para detección controlada, trazabilidad y respuesta en entornos de red reales.</p>
      </section>
    </>
  )
}
