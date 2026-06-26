import { useState } from 'react'
import { requestJson } from '../api'
import { initialResponseForm, responseActionOptions } from '../utils/helpers'

export default function ResponseEnginePage({ recentIncidents = [], responseActions = [], onDataRefresh }) {
  const [form, setForm] = useState(initialResponseForm)
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setNote('')

    try {
      await requestJson('/api/responses/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          incident: Number(form.incident) || 0,
          action_type: form.actionType,
          target_value: form.targetValue,
          notes: form.notes,
        }),
      })

      setForm(initialResponseForm)
      setNote('Acción de respuesta registrada.')
      await onDataRefresh()
    } catch (error) {
      setNote(error.message || 'No fue posible registrar la respuesta.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <section className="overview-section" data-nav-section id="response-engine">
        <header className="topbar">
          <div>
            <p className="eyebrow">Módulo 4</p>
            <h2>Motor de decisión y respuesta automática</h2>
          </div>
          <span className="pill success">{responseActions.length} acciones</span>
        </header>

        <p className="muted">
          Registra acciones automáticas sobre incidentes ya creados, con trazabilidad completa.
        </p>

        <form className="module-form" onSubmit={handleSubmit}>
          <div className="form-grid">
            <label>
              <span>Incidente</span>
              <select
                required
                value={form.incident}
                onChange={(event) => setForm({ ...form, incident: event.target.value })}
              >
                <option value="">Seleccionar incidente</option>
                {recentIncidents.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.id} - {item.title}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Acción</span>
              <select
                value={form.actionType}
                onChange={(event) => setForm({ ...form, actionType: event.target.value })}
              >
                {responseActionOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Valor objetivo</span>
              <input
                value={form.targetValue}
                onChange={(event) => setForm({ ...form, targetValue: event.target.value })}
                placeholder="10.0.0.20"
              />
            </label>
          </div>

          <label>
            <span>Notas</span>
            <textarea
              rows="3"
              value={form.notes}
              onChange={(event) => setForm({ ...form, notes: event.target.value })}
              placeholder="Contexto operativo de la respuesta"
            />
          </label>

          {note ? <div className="hint">{note}</div> : null}

          <button className="primary-button" disabled={busy} type="submit">
            {busy ? 'Registrando…' : 'Registrar acción'}
          </button>
        </form>

        <div className="table-shell">
          <div className="table-head">
            <strong>Acciones recientes</strong>
            <span className="muted">Trazabilidad operativa</span>
          </div>
          <div className="table-list">
            {responseActions.slice(0, 5).map((item) => (
              <div className="table-row" key={item.id}>
                <span>#{item.id}</span>
                <span>{item.action_type}</span>
                <span>{item.target_value || 'Sin valor'}</span>
                <span>{item.status}</span>
              </div>
            ))}
            {responseActions.length === 0 ? <p className="muted compact-copy">No hay acciones registradas.</p> : null}
          </div>
        </div>
      </section>

      <section className="footer-note">
        <p>Diseñado para detección controlada, trazabilidad y respuesta en entornos de red reales.</p>
      </section>
    </>
  )
}
