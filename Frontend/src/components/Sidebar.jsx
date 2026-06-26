import { useEffect, useMemo, useState } from 'react'
import { sidebarModules } from '../navigation'

function getModuleIdForSection(sectionId) {
  return sidebarModules.find((module) => module.items.some((item) => item.id === sectionId))?.id ?? sidebarModules[0]?.id
}

function SidebarModule({ activeSection, isOpen, module, onNavigate, onToggle }) {
  const isModuleActive = module.items.some((item) => item.id === activeSection)

  return (
    <section className={`nav-module${isModuleActive ? ' active' : ''}${isOpen ? ' open' : ''}`}>
      <button
        aria-controls={`nav-module-${module.id}`}
        aria-expanded={isOpen}
        className="nav-module-toggle"
        onClick={() => onToggle(module.id)}
        type="button"
      >
        <span className="nav-module-toggle-label">{module.label}</span>
        <span className="nav-module-toggle-meta">
          <span className="nav-module-badge">{module.items.length}</span>
          <span className="nav-module-caret" aria-hidden="true">
            ▾
          </span>
        </span>
      </button>

      {isOpen ? (
        <div className="nav-module-items" id={`nav-module-${module.id}`}>
          {module.items.map((item) => {
            const isActive = activeSection === item.id

            return (
              <button
                aria-current={isActive ? 'page' : undefined}
                className={`nav-item${isActive ? ' active' : ''}`}
                key={item.id}
                onClick={() => onNavigate(item.id)}
                type="button"
              >
                <span className="nav-item-label">{item.label}</span>
              </button>
            )
          })}
        </div>
      ) : null}
    </section>
  )
}

export default function Sidebar({
  activeSection,
  authSummary,
  health,
  identityTags,
  onLogout,
  onNavigate,
  user,
}) {
  const [openModuleId, setOpenModuleId] = useState(() => getModuleIdForSection(activeSection))

  useEffect(() => {
    setOpenModuleId(getModuleIdForSection(activeSection))
  }, [activeSection])

  const compactTags = useMemo(() => identityTags.slice(0, 3), [identityTags])

  function handleToggle(moduleId) {
    setOpenModuleId((current) => (current === moduleId ? '' : moduleId))
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <p className="sidebar-brand-kicker">CyberShield AI</p>
        <h1 className="sidebar-brand-title">Consola de seguridad</h1>
        <p className="sidebar-brand-copy">Monitoreo y respuesta para operaciones críticas.</p>
      </div>

      <nav className="nav-card nav-stack" aria-label="Navegación principal">
        {sidebarModules.map((module) => (
          <SidebarModule
            activeSection={activeSection}
            isOpen={openModuleId === module.id}
            key={module.id}
            module={module}
            onNavigate={onNavigate}
            onToggle={handleToggle}
          />
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-footer-card">
          <div className="sidebar-footer-grid">
            <div>
              <span className="label">Sesión iniciada</span>
              <strong className="sidebar-user-name">{user?.displayName ?? user?.username ?? 'Usuario autenticado'}</strong>
              <p className="muted compact-copy">{user?.username ?? 'Sesión JWT activa'}</p>
              <p className="muted compact-copy">{authSummary(user)}</p>
            </div>
          </div>

          <div className="chip-row compact-chip-row">
            {compactTags.length > 0 ? (
              compactTags.map((tag) => (
                <span className="chip" key={tag}>
                  {tag}
                </span>
              ))
            ) : (
              <span className="chip">JWT</span>
            )}

          </div>

          <button className="secondary-button secondary-button-tight" onClick={onLogout} type="button">
            Cerrar sesión
          </button>
        </div>
      </div>
    </aside>
  )
}
