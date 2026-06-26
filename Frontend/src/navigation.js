export const sidebarModules = [
  {
    id: 'overview',
    label: 'Resumen',
    items: [{ id: 'overview', label: 'Panel operativo' }],
  },
  {
    id: 'auth-users',
    label: 'Gestión de usuarios',
    items: [{ id: 'auth-users', label: 'Acceso y roles' }],
  },
  {
    id: 'data-ingestion',
    label: 'Ingesta de datos',
    items: [{ id: 'data-ingestion', label: 'Eventos y datasets' }],
  },
  {
    id: 'ml-pipeline',
    label: 'Detección ML',
    items: [{ id: 'ml-pipeline', label: 'Modelo y predicción' }],
  },
  {
    id: 'response-engine',
    label: 'Respuesta automática',
    items: [{ id: 'response-engine', label: 'Acciones de contención' }],
  },
  {
    id: 'incidents-evidence',
    label: 'Incidentes',
    items: [{ id: 'incidents-evidence', label: 'Alertas y evidencias' }],
  },
  {
    id: 'dashboard-reports',
    label: 'Reportes',
    items: [{ id: 'dashboard-reports', label: 'Indicadores y exportación' }],
  },
]
