import { useState } from 'react'
import AiSupportPanel from '../components/AiSupportPanel'
import { downloadJson, formatCount, formatDurationSeconds, safeNumber } from '../utils/helpers'

function formatTimestamp(value) {
  if (!value) return '—'

  return new Intl.DateTimeFormat('es-ES', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function MetricCard({ label, value, note }) {
  return (
    <div className="summary-block workflow-metric">
      <strong>{value}</strong>
      <p className="muted compact-copy">{label}</p>
      {note ? <p className="workflow-note muted compact-copy">{note}</p> : null}
    </div>
  )
}

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

  const workflow = dashboardSummary?.workflow ?? {}
  const analysis = workflow.analysis ?? {}
  const response = workflow.response ?? {}
  const history = workflow.history ?? {}
  const model = workflow.model ?? dashboardSummary?.model_quality ?? {}
  const incidentHistory = history.incident_history ?? dashboardSummary?.incident_history ?? recentIncidents.slice(0, 6)
  const suspiciousHosts = analysis.suspicious_hosts ?? dashboardSummary?.suspicious_hosts ?? []
  const isolatedHosts = response.isolated_hosts ?? dashboardSummary?.isolated_hosts ?? []
  const actionCounts = response.action_counts_by_type ?? dashboardSummary?.action_counts_by_type ?? []

  async function handleExport() {
    setBusy(true)
    setNote('')

    try {
      const report = {
        generatedAt: new Date().toISOString(),
        summary: dashboardSummary,
        workflow,
        trafficEvents: trafficEvents.slice(0, 10),
        incidents: incidentHistory.slice(0, 10),
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
          Métricas del flujo completo: análisis, alertas, contención, historial e indicadores del modelo.
        </p>

        <div className="workflow-section">
          <div className="workflow-section-head">
            <strong>Flujo operativo</strong>
            <span className="muted">Resumen derivado del backend</span>
          </div>

          <div className="workflow-grid">
            <MetricCard label="Eventos analizados" value={formatCount(dashboardSummary?.events_analyzed_total ?? dashboardSummary?.events_total)} note="Datos ingestados y puntuados" />
            <MetricCard label="Alertas activas" value={formatCount(dashboardSummary?.active_alerts_total)} note="Incidentes abiertos o en análisis" />
            <MetricCard label="Hosts sospechosos" value={formatCount(dashboardSummary?.suspicious_hosts_total)} note="Origen de detecciones de alto riesgo" />
            <MetricCard label="Hosts aislados" value={formatCount(dashboardSummary?.isolated_hosts_total)} note="Acciones de contención aplicadas" />
          </div>
        </div>

        <div className="workflow-section workflow-columns">
          <div className="workflow-panel">
            <div className="workflow-section-head">
              <strong>Tiempo de detección</strong>
              <span className="muted">Promedio y última señal registrada</span>
            </div>
            <div className="workflow-grid compact">
              <MetricCard
                label="Promedio"
                value={formatDurationSeconds(analysis.detection_latency_seconds?.average_seconds)}
                note={`${formatCount(analysis.detection_latency_seconds?.samples)} muestras`}
              />
              <MetricCard
                label="Último evento"
                value={formatDurationSeconds(analysis.detection_latency_seconds?.latest_seconds)}
                note={`${formatCount(analysis.detection_latency_seconds?.samples)} eventos analizados`}
              />
            </div>
          </div>

          <div className="workflow-panel">
            <div className="workflow-section-head">
              <strong>Tiempo de respuesta</strong>
              <span className="muted">Latencia hasta la primera acción</span>
            </div>
            <div className="workflow-grid compact">
              <MetricCard
                label="Promedio"
                value={formatDurationSeconds(response.response_latency_seconds?.average_seconds)}
                note={`${formatCount(response.response_latency_seconds?.samples)} incidentes`}
              />
              <MetricCard
                label="Último incidente"
                value={formatDurationSeconds(response.response_latency_seconds?.latest_seconds)}
                note="Acción controlada registrada"
              />
            </div>
          </div>
        </div>

        <div className="workflow-section workflow-columns">
          <div className="workflow-panel">
            <div className="workflow-section-head">
              <strong>Acciones por tipo</strong>
              <span className="muted">Distribución de contención</span>
            </div>
            <div className="workflow-list">
              {actionCounts.length > 0 ? (
                actionCounts.map((item) => (
                  <div className="workflow-list-row" key={item.action_type}>
                    <span>{item.action_type}</span>
                    <strong>{formatCount(item.count)}</strong>
                  </div>
                ))
              ) : (
                <p className="muted compact-copy">Sin acciones registradas.</p>
              )}
            </div>
          </div>

          <div className="workflow-panel">
            <div className="workflow-section-head">
              <strong>Calidad del modelo</strong>
              <span className="muted">Versión y estado de entrenamiento</span>
            </div>
            <div className="workflow-list">
              <div className="workflow-list-row">
                <span>Engine</span>
                <strong>{model.engine_version ?? '—'}</strong>
              </div>
              <div className="workflow-list-row">
                <span>Estado</span>
                <strong>{model.training_status ?? '—'}</strong>
              </div>
              <div className="workflow-list-row">
                <span>Entrenamiento</span>
                <strong>{formatCount(model.training_rows)}</strong>
              </div>
              <div className="workflow-list-row">
                <span>Ratio alto riesgo</span>
                <strong>{Math.round(safeNumber(model.high_risk_detection_rate) * 100)}%</strong>
              </div>
            </div>
          </div>
        </div>

        <div className="workflow-section">
          <div className="workflow-section-head">
            <strong>Historial de incidentes</strong>
            <span className="muted">{incidentHistory.length} registros más recientes</span>
          </div>

          <div className="workflow-history-grid">
            {incidentHistory.length > 0 ? (
              incidentHistory.map((item) => (
                <article className="workflow-history-card" key={item.id}>
                  <div className="workflow-history-head">
                    <strong>{item.title}</strong>
                    <span>{formatTimestamp(item.created_at)}</span>
                  </div>
                  <p className="muted compact-copy">Severidad {item.severity} · Estado {item.status}</p>
                  <div className="workflow-history-meta">
                    <span>{formatCount(item.evidence_total)} evidencias</span>
                    <span>{formatCount(item.response_actions_total)} acciones</span>
                    <span>{formatCount(item.timeline_total)} eventos</span>
                  </div>
                  <div className="workflow-history-meta compact">
                    <span>Detección: {formatDurationSeconds(item.detection_latency_seconds)}</span>
                    <span>Respuesta: {formatDurationSeconds(item.response_latency_seconds)}</span>
                  </div>
                </article>
              ))
            ) : (
              <p className="muted compact-copy">Todavía no hay incidentes registrados.</p>
            )}
          </div>
        </div>

        <div className="workflow-section workflow-columns">
          <div className="workflow-panel">
            <div className="workflow-section-head">
              <strong>Hosts sospechosos</strong>
              <span className="muted">Origen de detecciones de alto riesgo</span>
            </div>
            <div className="workflow-list">
              {suspiciousHosts.length > 0 ? (
                suspiciousHosts.map((item) => (
                  <div className="workflow-list-row" key={item.host}>
                    <span>{item.host}</span>
                    <strong>{formatCount(item.detection_count)}</strong>
                  </div>
                ))
              ) : (
                <p className="muted compact-copy">Sin hosts sospechosos registrados.</p>
              )}
            </div>
          </div>

          <div className="workflow-panel">
            <div className="workflow-section-head">
              <strong>Hosts aislados</strong>
              <span className="muted">Acciones de contención persistidas</span>
            </div>
            <div className="workflow-list">
              {isolatedHosts.length > 0 ? (
                isolatedHosts.map((item) => (
                  <div className="workflow-list-row" key={item.host}>
                    <span>{item.host}</span>
                    <strong>{formatCount(item.action_count)}</strong>
                  </div>
                ))
              ) : (
                <p className="muted compact-copy">Sin hosts aislados registrados.</p>
              )}
            </div>
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

        <AiSupportPanel
          title="Análisis IA para reportes"
          records={incidentHistory}
          getRecordLabel={(item) => `#${item.id} · ${item.title}`}
          getRecordText={(item) => item.summary || item.title || ''}
          defaultText={incidentHistory[0]?.summary || incidentHistory[0]?.title || ''}
        />

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
