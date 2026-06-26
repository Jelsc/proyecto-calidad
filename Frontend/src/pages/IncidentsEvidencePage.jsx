import { useState } from 'react'
import { requestJson } from '../api'
import {
  initialIncidentForm,
  severityOptions,
  incidentStatusOptions,
  safeNumber,
  formatCount,
} from '../utils/helpers'

export default function IncidentsEvidencePage({
  dashboardSummary,
  trafficEvents,
  recentIncidents,
  onDataRefresh,
}) {
  const [form, setForm] = useState(initialIncidentForm)
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState('')

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

        <form className="module-form" onSubmit={handleSubmit}>
          <label>
            <span>Título</span>
            <input
              required
              value={form.title}
              onChange={(event) => setForm({ ...form, title: event.target.value })}
              placeholder="Exfiltración detectada"
            />
          </label>

          <label>
            <span>Resumen</span>
            <textarea
              rows="3"
              required
              value={form.summary}
              onChange={(event) => setForm({ ...form, summary: event.target.value })}
              placeholder="Descripción breve del incidente"
            />
          </label>

          <div className="form-grid">
            <label>
              <span>Severidad</span>
              <select
                value={form.severity}
                onChange={(event) => setForm({ ...form, severity: event.target.value })}
              >
                {severityOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Estado</span>
              <select
                value={form.status}
                onChange={(event) => setForm({ ...form, status: event.target.value })}
              >
                {incidentStatusOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="form-grid">
            <label>
              <span>Evento origen</span>
              <select
                value={form.sourceEvent}
                onChange={(event) => setForm({ ...form, sourceEvent: event.target.value })}
              >
                <option value="">Opcional</option>
                {trafficEvents.map((item) => (
                  <option key={item.id} value={item.id}>
                    Evento #{item.id}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Detección</span>
              <input
                value={form.detection}
                onChange={(event) => setForm({ ...form, detection: event.target.value })}
                placeholder="ID de detección"
              />
            </label>
          </div>

          <label>
            <span>Asignado a</span>
            <input
              value={form.assignedTo}
              onChange={(event) => setForm({ ...form, assignedTo: event.target.value })}
              placeholder="analista-01"
            />
          </label>

          {note ? <div className="hint">{note}</div> : null}

          <button className="primary-button" disabled={busy} type="submit">
            {busy ? 'Registrando incidente…' : 'Registrar incidente'}
          </button>
        </form>

        <div className="table-shell">
          <div className="table-head">
            <strong>Incidentes recientes</strong>
            <span className="muted">{recentIncidents.length} registros</span>
          </div>
          <div className="table-list">
            {recentIncidents.slice(0, 5).map((item) => (
              <div className="table-row" key={item.id}>
                <span>#{item.id}</span>
                <span>{item.title}</span>
                <span>{item.severity}</span>
                <span>{item.status}</span>
              </div>
            ))}
            {recentIncidents.length === 0 ? <p className="muted compact-copy">No hay incidentes registrados.</p> : null}
          </div>
        </div>
      </section>

      <section className="footer-note">
        <p>Diseñado para detección controlada, trazabilidad y respuesta en entornos de red reales.</p>
      </section>
    </>
  )
}
