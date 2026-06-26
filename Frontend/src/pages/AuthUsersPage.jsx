function StatTile({ label, value, note }) {
  return (
    <article className="auth-metric">
      <span className="auth-metric-label">{label}</span>
      <strong>{value}</strong>
      <span className="auth-metric-note">{note}</span>
    </article>
  )
}

function DetailRow({ label, value }) {
  return (
    <div className="auth-detail-row">
      <span className="auth-detail-label">{label}</span>
      <span className="auth-detail-value">{value}</span>
    </div>
  )
}

function SectionCard({ eyebrow, title, copy, children }) {
  return (
    <article className="panel auth-card-section">
      <div className="panel-head compact">
        <div>
          <span className="label">{eyebrow}</span>
          <h3>{title}</h3>
        </div>
        {copy ? <span className="auth-card-copy">{copy}</span> : null}
      </div>

      {children}
    </article>
  )
}

export default function AuthUsersPage({ authSummary, health, identityTags = [], user }) {
  const displayName = user?.displayName ?? user?.fullName ?? user?.username ?? 'Usuario autenticado'
  const primaryRole = identityTags[0] ?? user?.role ?? 'Sin rol expuesto'
  const accessScope = identityTags.length > 0 ? identityTags.join(' · ') : 'JWT'
  const authTone = /sin conexión|error|desconocido/i.test(String(health ?? '')) ? 'danger' : 'success'

  const summaryTiles = [
    {
      label: 'Sesión',
      value: health,
      note: 'Estado operativo del canal autenticado.',
    },
    {
      label: 'Usuario activo',
      value: displayName,
      note: user?.email ?? 'Perfil visible desde /api/auth/me/.',
    },
    {
      label: 'Rol principal',
      value: primaryRole,
      note: authSummary(user),
    },
    {
      label: 'Huella de acceso',
      value: identityTags.length > 0 ? `${identityTags.length} etiquetas` : 'JWT',
      note: accessScope,
    },
  ]

  const accessPolicy = [
    ['Autenticación', 'Obligatoria para el perfil activo'],
    ['Autorización', 'Por roles y grupos expuestos'],
    ['Trazabilidad', 'Sesión legible desde la UI'],
  ]

  const protectedSurfaces = [
    ['Perfil protegido', '/api/auth/me/ — identidad, grupos y claims visibles'],
    ['Consola del módulo', '/auth-users — acceso operativo de solo lectura'],
    ['Sesión', 'JWT activo con contexto de permisos'],
  ]

  const auditNotes = [
    'Mantener este módulo como control operativo, no como formulario.',
    'Reutilizar identityTags para reflejar cambios de rol sin duplicar lógica.',
    'Si la salud cae, el módulo debe seguir mostrando la última identidad válida.',
  ]

  return (
    <section className="panel workbench-card auth-users-page" id="auth-users" data-nav-section>
      <div className="panel-head auth-page-head">
        <div>
          <span className="label">Módulo de acceso</span>
          <h2>Gestión de usuarios y acceso</h2>
          <p className="muted compact-copy">Sesión activa, roles, permisos y superficie protegida.</p>
        </div>

        <div className="auth-head-meta">
          <span className={`pill ${authTone}`}>{health}</span>
          <span className="chip subtle">JWT</span>
        </div>
      </div>

      <div className="auth-summary-strip" aria-label="resumen de sesión y acceso">
        {summaryTiles.map((tile) => (
          <StatTile key={tile.label} {...tile} />
        ))}
      </div>

      <div className="auth-grid">
        <SectionCard eyebrow="Sesión activa" title="Identidad y contexto" copy="Perfil actual">
          <div className="auth-list">
            <DetailRow label="Usuario" value={displayName} />
            <DetailRow label="Estado" value={health} />
            <DetailRow label="Resumen" value={authSummary(user)} />
            <DetailRow label="Correo" value={user?.email ?? 'No expuesto'} />
          </div>
        </SectionCard>

        <SectionCard eyebrow="Roles y permisos" title="Acceso efectivo" copy="Claims visibles">
          <div className="auth-list">
            <DetailRow label="Rol base" value={primaryRole} />
            <DetailRow label="Cobertura" value={identityTags.length > 0 ? `${identityTags.length} etiquetas activas` : 'JWT estándar'} />
            <DetailRow label="Ámbito" value={user?.is_superuser ? 'Superusuario' : user?.is_staff ? 'Equipo interno' : 'Acceso estándar'} />
          </div>

          <div className="auth-tag-row" aria-label="etiquetas de identidad">
            {identityTags.length > 0 ? (
              identityTags.map((tag) => (
                <span className="chip subtle" key={tag}>
                  {tag}
                </span>
              ))
            ) : (
              <span className="chip subtle">JWT</span>
            )}
          </div>
        </SectionCard>

        <SectionCard eyebrow="Política de acceso" title="Permisos y control" copy="Reglas operativas">
          <div className="auth-note-box">
            <ul className="auth-note-list">
              {accessPolicy.map(([label, value]) => (
                <li key={label}>
                  <strong>{label}:</strong> {value}
                </li>
              ))}
            </ul>
          </div>
        </SectionCard>

        <SectionCard eyebrow="Superficie protegida" title="Rutas y postura" copy="Lectura segura">
          <div className="auth-endpoint-list">
            {protectedSurfaces.map(([label, value]) => (
              <div className="auth-endpoint-row" key={label}>
                <strong>{label}</strong>
                <p>{value}</p>
              </div>
            ))}
          </div>

          <div className="auth-note-box auth-audit-box">
            <p className="label">Notas de auditoría</p>
            <ul className="auth-note-list compact-copy">
              {auditNotes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          </div>
        </SectionCard>
      </div>
    </section>
  )
}
