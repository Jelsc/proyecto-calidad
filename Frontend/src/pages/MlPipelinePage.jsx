import { useState } from 'react'
import { requestJson } from '../api'
import {
  initialDetectionForm,
  protocolOptions,
  safeNumber,
  parseJsonInput,
} from '../utils/helpers'

export default function MlPipelinePage({ detectionResult, trafficEvents = [], trainingResult, onDetectionResult, onDataRefresh }) {
  const [form, setForm] = useState(initialDetectionForm)
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState('')

  async function handleTrain() {
    setBusy(true)
    setNote('')

    try {
      const result = await requestJson('/api/detection/train/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })

      onDetectionResult('train', result)
      setNote('Modelo entrenado correctamente.')
      await onDataRefresh()
    } catch (error) {
      setNote(error.message || 'No fue posible entrenar el modelo.')
    } finally {
      setBusy(false)
    }
  }

  async function handleSimulate(event) {
    event.preventDefault()
    setBusy(true)
    setNote('')

    try {
      const payload = form.eventId
        ? {
            event_id: safeNumber(form.eventId),
            payload: parseJsonInput(form.payload, 'raw'),
          }
        : {
            source_ip: form.sourceIp,
            destination_ip: form.destinationIp,
            protocol: form.protocol,
            destination_port: safeNumber(form.destinationPort),
            payload: parseJsonInput(form.payload, 'raw'),
            metadata: parseJsonInput(form.metadata, 'note'),
          }

      const result = await requestJson('/api/detection/simulate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      onDetectionResult('simulate', result)
      setNote('Detección simulada correctamente.')
      await onDataRefresh()
    } catch (error) {
      setNote(error.message || 'No fue posible simular la detección.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <section className="overview-section" data-nav-section id="ml-pipeline">
        <header className="topbar">
          <div>
            <p className="eyebrow">Módulo 3</p>
            <h2>Preprocesamiento y detección ML</h2>
          </div>
          <span className="pill success">{trainingResult?.engine_version ?? 'Modelo listo'}</span>
        </header>

        <p className="muted">
          Entrena el modelo y simula detecciones con eventos reales o payloads manuales.
        </p>

        <div className="workflow-panel compact-panel">
          <div className="workflow-section-head">
            <strong>Elegir evento a analizar</strong>
            <span className="muted">Usa un registro cargado o un payload manual</span>
          </div>

          <div className="form-grid">
            <label>
              <span>Evento base</span>
              <select
                value={form.eventId}
                onChange={(event) => setForm({ ...form, eventId: event.target.value })}
              >
                <option value="">Usar payload manual</option>
                {trafficEvents.map((item) => (
                  <option key={item.id} value={item.id}>
                    Evento #{item.id} · {item.source_ip} → {item.destination_ip}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        <div className="action-row">
          <button className="secondary-button" disabled={busy} onClick={handleTrain} type="button">
            {busy ? 'Entrenando…' : 'Entrenar modelo'}
          </button>
        </div>

        <form className="module-form" onSubmit={handleSimulate}>
          <div className="form-grid">
            <label>
              <span>IP origen</span>
              <input
                value={form.sourceIp}
                onChange={(event) => setForm({ ...form, sourceIp: event.target.value })}
                placeholder="10.0.0.10"
              />
            </label>
            <label>
              <span>IP destino</span>
              <input
                value={form.destinationIp}
                onChange={(event) => setForm({ ...form, destinationIp: event.target.value })}
                placeholder="10.0.0.20"
              />
            </label>
            <label>
              <span>Protocolo</span>
              <select
                value={form.protocol}
                onChange={(event) => setForm({ ...form, protocol: event.target.value })}
              >
                {protocolOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Puerto destino</span>
              <input
                type="number"
                min="1"
                max="65535"
                value={form.destinationPort}
                onChange={(event) => setForm({ ...form, destinationPort: event.target.value })}
                placeholder="443"
              />
            </label>
          </div>

          <label>
            <span>Payload</span>
            <textarea
              rows="3"
              value={form.payload}
              onChange={(event) => setForm({ ...form, payload: event.target.value })}
              placeholder="Payload manual para la simulación"
            />
          </label>

          <label>
            <span>Metadata</span>
            <textarea
              rows="2"
              value={form.metadata}
              onChange={(event) => setForm({ ...form, metadata: event.target.value })}
              placeholder="Contexto adicional en JSON"
            />
          </label>

          <button className="primary-button" disabled={busy} type="submit">
            {busy ? 'Simulando…' : 'Simular detección'}
          </button>
        </form>

        {note ? <div className="hint">{note}</div> : null}

        {detectionResult ? (
          <div className="summary-block">
            <strong>{detectionResult.label}</strong>
            <p className="muted compact-copy">Score: {detectionResult.score}</p>
            <p className="muted compact-copy">{detectionResult.reason}</p>
          </div>
        ) : null}

        {trainingResult ? (
          <div className="mini-summary-grid">
            <div className="summary-block">
              <strong>{trainingResult.training_rows}</strong>
              <p className="muted compact-copy">Filas usadas para entrenamiento.</p>
            </div>
            <div className="summary-block">
              <strong>{trainingResult.score_threshold}</strong>
              <p className="muted compact-copy">Umbral del modelo entrenado.</p>
            </div>
          </div>
        ) : null}
      </section>

      <section className="footer-note">
        <p>Diseñado para detección controlada, trazabilidad y respuesta en entornos de red reales.</p>
      </section>
    </>
  )
}
