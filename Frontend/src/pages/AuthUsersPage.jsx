function SectionCard({ eyebrow, title, copy, children }) {
  return (
    <article className="panel auth-section">
      <div className="panel-head compact">
        <div>
          <span className="label">{eyebrow}</span>
          <h3>{title}</h3>
        </div>
        {copy ? <span className="auth-section-copy">{copy}</span> : null}
      </div>

      {children}
    </article>
  )
}

function RoleCard({ role, title, copy, badge }) {
  return (
    <article className="auth-role-card">
      <div className="auth-role-head">
        <div>
          <span className="label">{role}</span>
          <strong className="auth-role-title">{title}</strong>
        </div>
        {badge ? <span className="chip subtle">{badge}</span> : null}
      </div>
      <p>{copy}</p>
    </article>
  )
}

export default function AuthUsersPage({ health, identityTags = [], user }) {
  const displayName = user?.displayName ?? user?.fullName ?? user?.username ?? 'Usuario autenticado'
  const primaryRole = identityTags[0] ?? user?.role ?? (user?.is_superuser ? 'admin' : 'viewer')
  const authTone = /sin conexión|error|desconocido/i.test(String(health ?? '')) ? 'danger' : 'success'

  const users = [
    {
      username: displayName,
      email: user?.email ?? 'Sin correo',
      role: primaryRole,
      status: health ?? 'Desconocido',
      tone: authTone,
    },
    {
      username: 'demo.operator',
      email: 'operator@cybershield.local',
      role: 'operator',
      status: 'Activo',
      tone: 'success',
    },
    {
      username: 'demo.viewer',
      email: 'viewer@cybershield.local',
      role: 'viewer',
      status: 'Activo',
      tone: 'success',
    },
  ]

  const roles = [
    {
      role: 'analyst',
      title: 'Análisis y revisión',
      copy: 'Consulta datos y señales sin capacidad de cambios operativos.',
      badge: 'Lectura',
    },
    {
      role: 'operator',
      title: 'Operación diaria',
      copy: 'Gestiona el flujo de trabajo y ejecuta acciones permitidas.',
      badge: 'Acción',
    },
    {
      role: 'viewer',
      title: 'Solo lectura',
      copy: 'Acceso mínimo para seguimiento y validación visual.',
      badge: 'Base',
    },
    {
      role: 'admin',
      title: 'Control total',
      copy: 'Administra usuarios, permisos y configuración del módulo.',
      badge: 'Total',
    },
  ]

  return (
    <section className="panel workbench-card auth-users-page" id="auth-users" data-nav-section>
      <div className="panel-head auth-page-head">
        <div>
          <span className="label">Módulo de acceso</span>
          <h2>Usuarios y roles</h2>
          <p className="muted compact-copy">Vista compacta de usuarios activos y roles disponibles.</p>
        </div>

        <div className="auth-head-meta">
          <span className={`pill ${authTone}`}>{health}</span>
          <span className="chip subtle">{users.length} usuarios</span>
        </div>
      </div>

      <div className="auth-users-layout">
        <SectionCard eyebrow="Usuarios" title="Listado" copy="Compacto y directo">
          <div className="auth-table-shell" role="table" aria-label="tabla de usuarios">
            <div className="auth-table-head" role="row">
              <span>Usuario</span>
              <span>Correo</span>
              <span>Rol principal</span>
              <span>Estado</span>
            </div>

            <div className="auth-table-list">
              {users.map((item) => (
                <div className="auth-table-row" role="row" key={`${item.username}-${item.email}`}>
                  <div className="auth-user-main">
                    <strong>{item.username}</strong>
                    <span className="auth-user-sub">{item.role}</span>
                  </div>
                  <span className="auth-cell">{item.email}</span>
                  <span className="auth-cell">{item.role}</span>
                  <span className={`pill ${item.tone}`}>{item.status}</span>
                </div>
              ))}
            </div>
          </div>
        </SectionCard>

        <SectionCard eyebrow="Roles" title="Tarjetas" copy="Resumen corto">
          <div className="auth-role-grid" aria-label="tarjetas de roles">
            {roles.map((role) => (
              <RoleCard key={role.role} {...role} />
            ))}
          </div>
        </SectionCard>
      </div>
    </section>
  )
}
