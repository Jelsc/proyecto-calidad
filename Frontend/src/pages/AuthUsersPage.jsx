export default function AuthUsersPage({ authSummary, health, identityTags, user }) {
  return (
    <section className="panel workbench-card" id="auth-users" data-nav-section>
      <div className="panel-head compact">
        <div>
          <span className="label">Módulo 1</span>
          <h3>Autenticación y usuarios</h3>
        </div>
        <span className="pill success">{health}</span>
      </div>

      <p className="muted">Login JWT, roles, permisos y trazabilidad de la sesión actual.</p>

      <div className="mini-summary-grid">
        <div className="summary-block">
          <strong>{user?.displayName ?? user?.username ?? 'Usuario autenticado'}</strong>
          <p className="muted compact-copy">Usuario activo en la sesión actual.</p>
        </div>

        <div className="summary-block">
          <strong>{authSummary(user)}</strong>
          <p className="muted compact-copy">Roles y grupos visibles desde `/api/auth/me/`.</p>
        </div>
      </div>

      <div className="chip-row">
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
    </section>
  )
}
