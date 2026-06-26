export default function SupportPanel({ panel }) {
  return (
    <article className="panel support-panel" id={`summary-${panel.id}`}>
      <div className="panel-head compact">
        <div>
          <span className="label">{panel.eyebrow}</span>
          <h3>{panel.title}</h3>
        </div>
        {panel.pill ? <span className={`pill ${panel.pillTone ?? 'success'}`}>{panel.pill}</span> : null}
      </div>

      <p className="muted">{panel.description}</p>

      <ul className="support-list">
        {panel.items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </article>
  )
}
