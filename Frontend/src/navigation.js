export const sidebarModules = [
  {
    id: 'operacion',
    label: 'Operación',
    items: [
      { id: 'overview', label: 'Panel operativo' },
      { id: 'incidents-evidence', label: 'Incidentes y evidencias' },
    ],
  },
  {
    id: 'datos-deteccion',
    label: 'Datos y detección',
    items: [
      { id: 'data-ingestion', label: 'Ingesta de datos' },
      { id: 'ml-pipeline', label: 'Modelo y predicción' },
    ],
  },
  {
    id: 'automatizacion',
    label: 'Automatización',
    items: [{ id: 'response-engine', label: 'Respuesta automática' }],
  },
  {
    id: 'administracion',
    label: 'Administración',
    items: [
      { id: 'auth-users', label: 'Usuarios y accesos' },
      { id: 'dashboard-reports', label: 'Reportes y exportación' },
    ],
  },
]
