import { useEffect, useMemo, useState } from 'react'
import { requestJson } from '../api'
import AiSupportPanel from '../components/AiSupportPanel'
import {
  initialIncidentForm,
  severityOptions,
  incidentStatusOptions,
  safeNumber,
  formatCount,
} from '../utils/helpers'

export default function IncidentsEvidencePage({ dashboardSummary, trafficEvents = [], recentIncidents = [], onDataRefresh }) {
  const [form, setForm] = useState(initialIncidentForm)
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)

  const workflow = dashboardSummary?.workflow ?? {}
  const analysis = workflow.analysis ?? {}
  const response = workflow.response ?? {}
  const history = workflow.history ?? {}
  const incidentsPerPage = 5
  const incidentsTable = useMemo(() => recentIncidents, [recentIncidents])
  const totalPages = Math.max(1, Math.ceil(incidentsTable.length / incidentsPerPage))
  const visibleIncidents = incidentsTable.slice((currentPage - 1) * incidentsPerPage, currentPage * incidentsPerPage)

  useEffect(() => {
    setCurrentPage((value) => Math.min(value, totalPages))
  }, [totalPages])

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setNote('')

    try {
      await requestJson('/api/incidents/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: form.title,
          summary: form.summary,
          severity: form.severity,
          status: form.status,
          source_event: form.sourceEvent ? safeNumber(form.sourceEvent) : null,
          detection: form.detection ? safeNumber(form.detection) : null,
          assigned_to: form.assignedTo,
        }),
      })

      setForm(initialIncidentForm)
      setNote('Incidente registrado correctamente.')
      await onDataRefresh()
    } catch (error) {
      setNote(error.message || 'No fue posible registrar el incidente.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <section className="overview-section" data-nav-section id="incidents-evidence">
        <header className="topbar">
          <div>
            <p className="eyebrow">Módulo 5</p>
            <h2>Incidentes, alertas y evidencias</h2>
          </div>
          <span className="pill success">{formatCount(dashboardSummary?.evidence_total)} evidencias</span>
        </header>

        <p className="muted">
          Registra incidentes manuales y valida la trazabilidad con los contadores reales del backend.
        </p>

        <div className="mini-summary-grid workflow-summary-grid">
          <div className="summary-block">
            <strong>{formatCount(analysis.events_analyzed_total ?? dashboardSummary?.events_analyzed_total)}</strong>
            <p className="muted compact-copy">Eventos analizados.</p>
          </div>
          <div className="summary-block">
            <strong>{formatCount(response.active_alerts_total ?? dashboardSummary?.active_alerts_total)}</strong>
            <p className="muted compact-copy">Alertas activas.</p>
          </div>
          <div className="summary-block">
            <strong>{formatCount(dashboardSummary?.isolated_hosts_total)}</strong>
            <p className="muted compact-copy">Hosts aislados.</p>
          </div>
          <div className="summary-block">
            <strong>{formatCount(history.evidence_total ?? dashboardSummary?.evidence_total)}</strong>
            <p className="muted compact-copy">Evidencias registradas.</p>
          </div>
        </div>

      </section>

      <section className="overview-section" id="incidents-table">
        <header className="table-head compact-table-head">
          <div>
            <p className="eyebrow">Historial</p>
            <h3>Incidentes registrados</h3>
          </div>
          <button className="primary-button" type="button" onClick={() => setShowCreateModal(true)}>
            Nuevo incidente
          </button>
        </header>

        <div className="table-shell">
          <div className="table-head incidents-table-head">
            <span>ID</span>
            <span>Título</span>
            <span>Severidad</span>
            <span>Estado</span>
            <span>Evidencias</span>
            <span>Acciones</span>
          </div>

          <div className="table-list">
            {visibleIncidents.length > 0 ? (
              visibleIncidents.map((item) => (
                <div className="table-row incidents-table-row" key={item.id}>
                  <span>#{item.id}</span>
                  <span>{item.title}</span>
                  <span>{item.severity}</span>
                  <span>{item.status}</span>
                  <span>{formatCount(item.evidence_total ?? 0)}</span>
                  <span>{formatCount(item.response_actions_total ?? 0)}</span>
                </div>
              ))
            ) : (
              <p className="muted compact-copy">No hay incidentes registrados.</p>
            )}
          </div>

          <div className="pagination-row">
            <button
              className="secondary-button"
              disabled={currentPage === 1}
              type="button"
              onClick={() => setCurrentPage((value) => Math.max(1, value - 1))}
            >
              Anterior
            </button>
            <span className="muted compact-copy">
              Página {currentPage} de {totalPages}
            </span>
            <button
              className="secondary-button"
              disabled={currentPage === totalPages}
              type="button"
              onClick={() => setCurrentPage((value) => Math.min(totalPages, value + 1))}
            >
              Siguiente
            </button>
          </div>
        </div>
      </section>

      <AiSupportPanel
        title="Análisis IA contextual"
        records={visibleIncidents}
        getRecordLabel={(item) => `#${item.id} · ${item.title}`}
        getRecordText={(item) => item.summary || item.title || ''}
        defaultText={recentIncidents[0]?.summary || recentIncidents[0]?.title || ''}
      />

      {showCreateModal ? (
        <div className="modal-backdrop" role="presentation" onClick={() => setShowCreateModal(false)}>
          <section className="modal-card" role="dialog" aria-modal="true" aria-label="Nuevo incidente" onClick={(event) => event.stopPropagation()}>
            <header className="panel-head compact">
              <div>
                <p className="eyebrow">Incidente</p>
                <h3>Registrar incidente</h3>
              </div>
              <button className="secondary-button" type="button" onClick={() => setShowCreateModal(false)}>
                Cerrar
              </button>
            </header>

            <form className="module-form" onSubmit={handleSubmit}>
              <label>
                <span>Título</span>
                <input required value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="Exfiltración detectada" />
              </label>

              <label>
                <span>Resumen</span>
                <textarea rows="3" required value={form.summary} onChange={(event) => setForm({ ...form, summary: event.target.value })} placeholder="Descripción breve del incidente" />
              </label>

              <div className="form-grid">
                <label>
                  <span>Severidad</span>
                  <select value={form.severity} onChange={(event) => setForm({ ...form, severity: event.target.value })}>
                    {severityOptions.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Estado</span>
                  <select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}>
                    {incidentStatusOptions.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="form-grid">
                <label>
                  <span>Evento origen</span>
                  <select value={form.sourceEvent} onChange={(event) => setForm({ ...form, sourceEvent: event.target.value })}>
                    <option value="">Opcional</option>
                    {trafficEvents.map((item) => (
                      <option key={item.id} value={item.id}>Evento #{item.id}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Detección</span>
                  <input value={form.detection} onChange={(event) => setForm({ ...form, detection: event.target.value })} placeholder="ID de detección" />
                </label>
              </div>

              <label>
                <span>Asignado a</span>
                <input value={form.assignedTo} onChange={(event) => setForm({ ...form, assignedTo: event.target.value })} placeholder="analista-01" />
              </label>

              {note ? <div className="hint">{note}</div> : null}

              <div className="action-row">
                <button className="primary-button" disabled={busy} type="submit">
                  {busy ? 'Registrando incidente…' : 'Registrar incidente'}
                </button>
              </div>
            </form>
          </section>
        </div>
      ) : null}

      <section className="footer-note">
        <p>Diseñado para detección controlada, trazabilidad y respuesta en entornos de red reales.</p>
      </section>
    </>
  )
}
