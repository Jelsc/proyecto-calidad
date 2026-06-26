export default function OverviewPage({ dashboardBusy, kpis, onRefresh, sessionNote }) {
  return (
    <section className="overview-section" data-nav-section id="overview">
      <header className="topbar">
        <div>
          <p className="eyebrow">Resumen operativo</p>
          <h2>Postura de amenaza y contención automática</h2>
        </div>

        <div className="topbar-actions">
          <button className="primary-button" disabled={dashboardBusy} onClick={onRefresh} type="button">
            {dashboardBusy ? 'Sincronizando panel…' : 'Actualizar panel'}
          </button>
        </div>
      </header>

      {sessionNote ? <div className="hint inline-hint">{sessionNote}</div> : null}

      <section className="kpi-grid" aria-label="métricas de seguridad">
        {kpis.map((item) => (
          <article className="metric-card" key={item.label}>
            <span className="label">{item.label}</span>
            <strong>{item.value}</strong>
            <small>{item.delta}</small>
          </article>
        ))}
      </section>
    </section>
  )
}
