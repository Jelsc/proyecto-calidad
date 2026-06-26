export default function SupportTablesPage({ supportTables }) {
  return (
    <section className="panel support-tables-panel" data-nav-section id="support-tables">
      <div className="panel-head compact">
        <div>
          <span className="label">Tablas de apoyo</span>
          <h3>Catálogos y configuración auxiliar</h3>
        </div>
      </div>

      <div className="chip-row">
        {supportTables.map((item) => (
          <span className="chip subtle" key={item}>{item}</span>
        ))}
      </div>
    </section>
  )
}
