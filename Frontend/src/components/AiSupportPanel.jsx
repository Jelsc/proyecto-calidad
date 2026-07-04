import { useEffect, useMemo, useState } from 'react'
import { requestJson } from '../api'

const MODES = {
  explain: {
    label: 'Explicar alerta',
    endpoint: '/api/ai/explain/',
    payloadKey: 'alert_text',
    responseKey: 'explanation',
    defaultPrompt: '¿Qué causó esta alerta?',
  },
  summarize: {
    label: 'Resumir incidente',
    endpoint: '/api/ai/summarize/',
    payloadKey: 'incident_text',
    responseKey: 'summary',
    defaultPrompt: 'Resume este incidente en lenguaje simple.',
  },
  report: {
    label: 'Generar reporte',
    endpoint: '/api/ai/report/',
    payloadKey: 'incident_text',
    responseKey: 'report',
    defaultPrompt: 'Redacta un reporte técnico breve.',
  },
}

const SUGGESTIONS = [
  '¿Qué causó esta alerta?',
  'Resume este incidente en lenguaje simple.',
  'Redacta un reporte técnico breve.',
  '¿Qué acción defensiva recomendarías?',
]

function buildActionPrompt(modeName, customPrompt) {
  const mode = MODES[modeName]
  const basePrompt = mode?.defaultPrompt ?? ''
  const cleanCustomPrompt = customPrompt.trim()

  if (!cleanCustomPrompt || cleanCustomPrompt === basePrompt) {
    return basePrompt
  }

  return `${basePrompt}\nInstrucción adicional: ${cleanCustomPrompt}`
}

export default function AiSupportPanel({
  title,
  defaultText = '',
  emptyText = 'Sin texto disponible.',
  records = [],
  getRecordLabel = (item) => item?.title ?? `Registro #${item?.id ?? ''}`,
  getRecordText = (item) => item?.summary ?? item?.title ?? '',
}) {
  const [prompt, setPrompt] = useState('')
  const [selectedRecordId, setSelectedRecordId] = useState('')
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState('')
  const [result, setResult] = useState('')

  const selectedRecord = useMemo(
    () => records.find((item) => String(item.id) === String(selectedRecordId)),
    [records, selectedRecordId],
  )

  const incidentContext = useMemo(() => {
    if (selectedRecord) {
      return getRecordText(selectedRecord) || defaultText
    }

    return defaultText
  }, [defaultText, getRecordText, selectedRecord])

  const canSubmit = Boolean(incidentContext.trim() || prompt.trim())

  useEffect(() => {
    if (records.length === 0) {
      setSelectedRecordId('')
      return
    }

    const selectedStillExists = records.some((item) => String(item.id) === String(selectedRecordId))
    if (!selectedStillExists) {
      setSelectedRecordId(String(records[0].id))
    }
  }, [records, selectedRecordId])

  function applySuggestion(suggestion) {
    setPrompt((currentPrompt) => {
      const trimmedCurrent = currentPrompt.trim()
      if (!trimmedCurrent) {
        return suggestion
      }

      return `${trimmedCurrent}\n${suggestion}`
    })
  }

  function buildRequestPayload(modeName) {
    const mode = MODES[modeName]
    const cleanIncidentContext = incidentContext.trim()
    const requestPrompt = buildActionPrompt(modeName, prompt)

    return {
      mode: modeName,
      [mode.payloadKey]: cleanIncidentContext,
      incident_context: cleanIncidentContext,
      prompt: requestPrompt,
      text: [cleanIncidentContext, requestPrompt].filter(Boolean).join('\n\n'),
    }
  }

  async function run(modeName) {
    const mode = MODES[modeName]
    if (!mode) return

    if (!canSubmit) {
      setNote(emptyText)
      return
    }

    setBusy(true)
    setNote('')
    setResult('')

    try {
      const payload = await requestJson(mode.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildRequestPayload(modeName)),
      })

      setResult(payload?.[mode.responseKey] ?? '')
    } catch (error) {
      setNote(error.message || 'No fue posible consultar la IA.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="ai-support-panel">
      <div className="workflow-section-head">
        <strong>{title}</strong>
      </div>

      {records.length > 0 ? (
        <label className="ai-record-select">
          <span>Incidente a analizar</span>
          <select value={selectedRecordId} onChange={(event) => setSelectedRecordId(event.target.value)}>
            {records.map((item) => (
              <option key={item.id} value={item.id}>
                {getRecordLabel(item)}
              </option>
            ))}
          </select>
        </label>
      ) : null}

      <div className="ai-support-field">
        <label htmlFor="ai-support-context">
          <span>Contexto del incidente</span>
        </label>
        <textarea
          className="ai-support-textarea ai-support-context"
          id="ai-support-context"
          readOnly
          rows="5"
          value={incidentContext}
          placeholder="Selecciona un incidente para cargar su contexto."
        />
      </div>

      <div className="ai-support-field">
        <label htmlFor="ai-support-prompt">
          <span>Instrucción adicional opcional</span>
        </label>
        <textarea
          className="ai-support-textarea ai-support-prompt"
          id="ai-support-prompt"
          rows="4"
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="Agrega detalles extra; se combinarán con la acción elegida."
        />
        <p className="small-print compact-copy">Opcional: se añadirá como instrucción extra al botón que elijas.</p>
      </div>

      <div className="ai-support-actions">
        <button className="secondary-button" disabled={busy} type="button" onClick={() => run('explain')}>
          {busy ? 'Procesando…' : MODES.explain.label}
        </button>
        <button className="secondary-button" disabled={busy} type="button" onClick={() => run('summarize')}>
          {MODES.summarize.label}
        </button>
        <button className="secondary-button" disabled={busy} type="button" onClick={() => run('report')}>
          {MODES.report.label}
        </button>
      </div>

      <div className="ai-suggestions">
        <span className="muted compact-copy">Sugerencias:</span>
        <div className="chip-row compact-chip-row">
          {SUGGESTIONS.map((item) => (
            <button className="chip subtle chip-button" key={item} type="button" onClick={() => applySuggestion(item)}>
              {item}
            </button>
          ))}
        </div>
      </div>

      {note ? <div className="hint">{note}</div> : null}
      {result ? <pre className="ai-support-output">{result}</pre> : null}
    </section>
  )
}
