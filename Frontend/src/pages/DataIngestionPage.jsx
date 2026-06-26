export default function DataIngestionPage({
  form,
  ingestionBusy,
  ingestionNote,
  onSubmit,
  setForm,
  trafficEvents,
}) {
  return (
    <section className="panel workbench-card" id="data-ingestion" data-nav-section>
      <div className="panel-head compact">
        <div>
          <span className="label">Módulo 2</span>
          <h3>Ingesta y gestión de datos</h3>
        </div>
        <span className="pill success">{trafficEvents.length} eventos</span>
      </div>

      <p className="muted">Carga datasets o eventos de red y persiste el tráfico para análisis posterior.</p>

      <form className="module-form" onSubmit={onSubmit}>
        <div className="form-grid">
          <label>
            <span>IP origen</span>
            <input required value={form.sourceIp} onChange={(event) => setForm({ ...form, sourceIp: event.target.value })} placeholder="10.0.0.10" />
          </label>
          <label>
            <span>IP destino</span>
            <input required value={form.destinationIp} onChange={(event) => setForm({ ...form, destinationIp: event.target.value })} placeholder="10.0.0.20" />
          </label>
          <label>
            <span>Protocolo</span>
            <select value={form.protocol} onChange={(event) => setForm({ ...form, protocol: event.target.value })}>
              {['TCP', 'UDP', 'ICMP', 'HTTP', 'HTTPS'].map((option) => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Puerto destino</span>
            <input required type="number" min="1" max="65535" value={form.destinationPort} onChange={(event) => setForm({ ...form, destinationPort: event.target.value })} placeholder="443" />
          </label>
        </div>

        <label>
          <span>Payload</span>
          <textarea required rows="3" value={form.payload} onChange={(event) => setForm({ ...form, payload: event.target.value })} placeholder="Contenido del evento o JSON" />
        </label>

        <label>
          <span>Metadata</span>
          <textarea rows="2" value={form.metadata} onChange={(event) => setForm({ ...form, metadata: event.target.value })} placeholder="JSON opcional de contexto" />
        </label>

        {ingestionNote ? <div className="hint">{ingestionNote}</div> : null}

        <button className="primary-button" disabled={ingestionBusy} type="submit">
          {ingestionBusy ? 'Registrando evento…' : 'Registrar evento'}
        </button>
      </form>

      <div className="table-shell">
        <div className="table-head">
          <strong>Eventos recientes</strong>
          <span className="muted">{trafficEvents.length} registros</span>
        </div>

        <div className="table-list">
          {trafficEvents.slice(0, 5).map((item) => (
            <div className="table-row" key={item.id}>
              <span>#{item.id}</span>
              <span>{item.source_ip} → {item.destination_ip}</span>
              <span>{item.protocol}</span>
              <span>{item.destination_port}</span>
            </div>
          ))}
          {trafficEvents.length === 0 ? <p className="muted compact-copy">No hay eventos cargados todavía.</p> : null}
        </div>
      </div>
    </section>
  )
}
