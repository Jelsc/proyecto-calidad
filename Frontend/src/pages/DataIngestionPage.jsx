import { useEffect, useMemo, useRef, useState } from 'react'
import { requestJson } from '../api'
import {
  parseTrafficIngestionPayload,
  prettyJson,
  protocolOptions,
  trafficIngestionExamples,
} from '../utils/helpers'

const PAGE_SIZES = [10, 20, 50]

function normalizeText(value) {
  return String(value ?? '').toLowerCase()
}

function stringifyValue(value) {
  if (value == null) return ''
  if (typeof value === 'string') return value

  try {
    return JSON.stringify(value)
  } catch {
    return String(value)
  }
}

function formatEventDetail(item) {
  const payload = stringifyValue(item.payload)
  const metadata = stringifyValue(item.metadata)

  if (payload && metadata) {
    return `${payload} · ${metadata}`
  }

  return payload || metadata || 'Sin detalle'
}

export default function DataIngestionPage({ onDataRefresh, trafficEvents = [], eventsLoading = false }) {
  const [payloadText, setPayloadText] = useState(() => prettyJson(trafficIngestionExamples[0].payload))
  const [payloadSource, setPayloadSource] = useState(trafficIngestionExamples[0].label)
  const [payloadFileName, setPayloadFileName] = useState('')
  const [ingestionBusy, setIngestionBusy] = useState(false)
  const [ingestionNote, setIngestionNote] = useState('')
  const [ingestionTone, setIngestionTone] = useState('info')
  const [filters, setFilters] = useState({ sourceIp: '', destinationIp: '', protocol: '', search: '' })
  const [pageSize, setPageSize] = useState(10)
  const [page, setPage] = useState(1)
  const fileInputRef = useRef(null)

  const filteredEvents = useMemo(() => {
    const sourceIp = normalizeText(filters.sourceIp.trim())
    const destinationIp = normalizeText(filters.destinationIp.trim())
    const protocol = filters.protocol.trim().toLowerCase()
    const search = normalizeText(filters.search.trim())

    return trafficEvents.filter((item) => {
      const sourceMatch = !sourceIp || normalizeText(item.source_ip).includes(sourceIp)
      const destinationMatch = !destinationIp || normalizeText(item.destination_ip).includes(destinationIp)
      const protocolMatch = !protocol || normalizeText(item.protocol) === protocol
      const searchableText = [
        item.id,
        item.source_ip,
        item.destination_ip,
        item.protocol,
        item.destination_port,
        stringifyValue(item.payload),
        stringifyValue(item.metadata),
      ]
        .join(' ')
        .toLowerCase()

      return sourceMatch && destinationMatch && protocolMatch && (!search || searchableText.includes(search))
    })
  }, [filters, trafficEvents])

  const totalPages = Math.max(1, Math.ceil(filteredEvents.length / pageSize))
  const currentPage = Math.min(page, totalPages)
  const visibleEvents = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize
    return filteredEvents.slice(startIndex, startIndex + pageSize)
  }, [currentPage, filteredEvents, pageSize])

  useEffect(() => {
    setPage(1)
  }, [filters, pageSize])

  useEffect(() => {
    setPage((currentPageValue) => Math.min(currentPageValue, totalPages))
  }, [totalPages])

  const pageStart = filteredEvents.length === 0 ? 0 : (currentPage - 1) * pageSize + 1
  const pageEnd = Math.min(currentPage * pageSize, filteredEvents.length)
  const protocolFilterOptions = protocolOptions

  function updateFilter(field, value) {
    setFilters((currentFilters) => ({ ...currentFilters, [field]: value }))
  }

  function clearFilters() {
    setFilters({ sourceIp: '', destinationIp: '', protocol: '', search: '' })
  }

  function loadExample(example) {
    setPayloadText(prettyJson(example.payload))
    setPayloadSource(example.label)
    setPayloadFileName('')
    setIngestionNote(`Ejemplo cargado: ${example.label}.`)
    setIngestionTone('info')
  }

  function openFileDialog() {
    fileInputRef.current?.click()
  }

  async function handleFileChange(event) {
    const file = event.target.files?.[0]

    if (!file) return

    try {
      const text = await file.text()
      const parsed = parseTrafficIngestionPayload(text)

      setPayloadText(prettyJson(parsed))
      setPayloadSource('Archivo .json')
      setPayloadFileName(file.name)
      setIngestionNote(`Archivo cargado: ${file.name}.`)
      setIngestionTone('info')
    } catch (error) {
      setIngestionNote(error.message || 'No fue posible leer el archivo JSON.')
      setIngestionTone('error')
    } finally {
      event.target.value = ''
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setIngestionBusy(true)
    setIngestionNote('')
    setIngestionTone('info')

    try {
      const parsedPayload = parseTrafficIngestionPayload(payloadText)
      const result = await requestJson('/api/events/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parsedPayload),
      })

      const summary = `Ingestados ${result.ingested_count} eventos; ${result.detections_created_count} detecciones; ${result.incidents_triggered_count} incidentes.`
      setIngestionNote(result.detection_status === 'pending' ? `${summary} Detección pendiente.` : summary)
      setIngestionTone(result.detection_status === 'pending' ? 'warning' : 'success')
      await onDataRefresh()
    } catch (error) {
      setIngestionNote(error.message || 'No fue posible registrar el evento.')
      setIngestionTone('error')
    } finally {
      setIngestionBusy(false)
    }
  }

  return (
    <section className="panel workbench-card" id="data-ingestion" data-nav-section>
      <div className="panel-head compact">
        <div>
          <span className="label">Módulo 2</span>
          <h3>Ingesta y gestión de datos</h3>
        </div>
        <span className="pill success">{trafficEvents.length} eventos</span>
      </div>

      <p className="muted">Simula tráfico real pegando un JSON completo o cargando un archivo .json; el sistema lo enviará tal como está a <code>/api/events/</code>.</p>

      <form className="module-form" onSubmit={handleSubmit}>
        <div className="ingestion-simulator">
          <div className="ingestion-editor">
            <label>
              <span>JSON del tráfico</span>
              <textarea
                rows="14"
                value={payloadText}
                onChange={(event) => setPayloadText(event.target.value)}
                placeholder='Pega un objeto JSON o un array de objetos con source_ip, destination_ip, protocol, destination_port y payload.'
              />
            </label>

            <input
              ref={fileInputRef}
              accept=".json,application/json"
              className="sr-only-input"
              onChange={handleFileChange}
              type="file"
            />

            <div className="ingestion-actions">
              <button className="secondary-button" onClick={openFileDialog} type="button">
                Cargar archivo .json
              </button>
              {trafficIngestionExamples.map((example) => (
                <button
                  className={`secondary-button ingestion-example-button${payloadSource === example.label ? ' active' : ''}`}
                  key={example.id}
                  onClick={() => loadExample(example)}
                  type="button"
                >
                  {example.label}
                </button>
              ))}
            </div>

            <div className="ingestion-metadata-row">
              {payloadFileName ? <span className="chip subtle">Archivo: {payloadFileName}</span> : null}
              <span className="chip">Origen: {payloadSource}</span>
              <span className="chip subtle">Compatibilidad: objeto o array</span>
            </div>

            {ingestionNote ? <div className={`ingestion-status-note ${ingestionTone}`}>{ingestionNote}</div> : null}

            <button className="primary-button wide" disabled={ingestionBusy || !payloadText.trim()} type="submit">
              {ingestionBusy ? 'Enviando JSON…' : 'Enviar a /api/events/'}
            </button>
          </div>

          <aside className="ingestion-helper">
            <div className="hint">
              <strong>Formato mínimo esperado</strong>
              <ul>
                <li>Un objeto JSON o un array de objetos.</li>
                <li>Campos clave: <code>source_ip</code>, <code>destination_ip</code>, <code>protocol</code>, <code>destination_port</code> y <code>payload</code>.</li>
                <li><code>metadata</code> es opcional y puede ser un objeto libre.</li>
              </ul>
            </div>

            <div className="hint">
              <strong>Ejemplos listos para probar</strong>
              <p>El botón benigno carga un objeto; el sospechoso carga una ráfaga en array para forzar más de un evento.</p>
              <ul className="example-list">
                {trafficIngestionExamples.map((example) => (
                  <li key={example.id}>
                    <button className="text-button" onClick={() => loadExample(example)} type="button">
                      {example.label}
                    </button>
                    <span>{example.description}</span>
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      </form>

      <div className="table-shell">
        <div className="table-head compact-table-head">
          <div>
            <strong>Eventos operativos</strong>
            <p className="muted compact-copy">Tabla completa para revisar tráfico cargado, filtrar por origen/destino y navegar por páginas.</p>
          </div>
          <span className="pill success">{filteredEvents.length} eventos</span>
        </div>

        <div className="table-toolbar">
          <div className="table-filters">
            <label>
              <span>IP origen</span>
              <input
                value={filters.sourceIp}
                onChange={(event) => updateFilter('sourceIp', event.target.value)}
                placeholder="10.0.0.10"
              />
            </label>
            <label>
              <span>IP destino</span>
              <input
                value={filters.destinationIp}
                onChange={(event) => updateFilter('destinationIp', event.target.value)}
                placeholder="10.0.0.20"
              />
            </label>
            <label>
              <span>Protocolo</span>
              <select value={filters.protocol} onChange={(event) => updateFilter('protocol', event.target.value)}>
                <option value="">Todos</option>
                {protocolFilterOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
            <label className="search-filter">
              <span>Búsqueda</span>
              <input
                value={filters.search}
                onChange={(event) => updateFilter('search', event.target.value)}
                placeholder="Payload o metadata"
              />
            </label>
          </div>

          <div className="table-toolbar-actions">
            <label className="page-size-control">
              <span>Filas por página</span>
              <select value={pageSize} onChange={(event) => setPageSize(Number(event.target.value))}>
                {PAGE_SIZES.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </label>
            <button className="secondary-button secondary-button-tight" onClick={clearFilters} type="button">
              Limpiar filtros
            </button>
          </div>
        </div>

        {eventsLoading ? <div className="table-empty">Cargando eventos cargados…</div> : null}

        {!eventsLoading && trafficEvents.length === 0 ? (
          <div className="table-empty">No hay eventos cargados todavía.</div>
        ) : null}

        {!eventsLoading && trafficEvents.length > 0 && filteredEvents.length === 0 ? (
          <div className="table-empty">No hay eventos que coincidan con los filtros activos.</div>
        ) : null}

        {!eventsLoading && filteredEvents.length > 0 ? (
          <>
            <div className="event-table-head">
              <span>ID</span>
              <span>IP origen</span>
              <span>IP destino</span>
              <span>Protocolo</span>
              <span>Puerto</span>
              <span>Payload / metadata</span>
            </div>

            <div className="table-list event-table-list">
              {visibleEvents.map((item) => (
                <article className="event-table-row" key={item.id}>
                  <span className="event-cell event-id">#{item.id}</span>
                  <span className="event-cell">{item.source_ip}</span>
                  <span className="event-cell">{item.destination_ip}</span>
                  <span className="event-cell">{item.protocol}</span>
                  <span className="event-cell">{item.destination_port}</span>
                  <span className="event-cell event-detail">{formatEventDetail(item)}</span>
                </article>
              ))}
            </div>

            <div className="pagination-row">
              <div className="muted compact-copy">
                Mostrando {pageStart}-{pageEnd} de {filteredEvents.length} eventos
              </div>

              <div className="pagination-controls">
                <button
                  className="secondary-button secondary-button-tight"
                  disabled={currentPage === 1}
                  onClick={() => setPage((currentPageValue) => Math.max(1, currentPageValue - 1))}
                  type="button"
                >
                  Anterior
                </button>
                <span className="pagination-status">
                  Página {currentPage} de {totalPages}
                </span>
                <button
                  className="secondary-button secondary-button-tight"
                  disabled={currentPage === totalPages}
                  onClick={() => setPage((currentPageValue) => Math.min(totalPages, currentPageValue + 1))}
                  type="button"
                >
                  Siguiente
                </button>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </section>
  )
}
