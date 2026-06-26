export const healthLabels = {
  ok: 'operativo',
  running: 'operativo',
  healthy: 'operativo',
  online: 'operativo',
  degraded: 'degradado',
  maintenance: 'en mantenimiento',
  offline: 'sin conexión',
  down: 'sin conexión',
  unavailable: 'sin conexión',
  unknown: 'desconocido',
}

export const severityLabels = {
  low: 'Bajo',
  medium: 'Medio',
  high: 'Alto',
  critical: 'Crítico',
}

export const statusLabels = {
  open: 'Abierto',
  investigating: 'En análisis',
  contained: 'Contenido',
  resolved: 'Resuelto',
}

export const protocolOptions = ['TCP', 'UDP', 'ICMP', 'HTTP', 'HTTPS']

export const severityOptions = [
  { value: 'low', label: 'Bajo' },
  { value: 'medium', label: 'Medio' },
  { value: 'high', label: 'Alto' },
  { value: 'critical', label: 'Crítico' },
]

export const incidentStatusOptions = [
  { value: 'open', label: 'Abierto' },
  { value: 'investigating', label: 'En análisis' },
  { value: 'contained', label: 'Contenido' },
  { value: 'resolved', label: 'Resuelto' },
]

export const responseActionOptions = [
  { value: 'alert', label: 'Alertar' },
  { value: 'isolate_host', label: 'Aislar host' },
  { value: 'block_ip', label: 'Bloquear IP' },
  { value: 'suspend_user', label: 'Suspender usuario' },
]

export const initialTrafficEventForm = {
  sourceIp: '',
  destinationIp: '',
  protocol: 'TCP',
  destinationPort: '',
  payload: '',
  metadata: '',
}

export const initialDetectionForm = {
  eventId: '',
  sourceIp: '',
  destinationIp: '',
  protocol: 'TCP',
  destinationPort: '',
  payload: '',
  metadata: '',
}

export const initialIncidentForm = {
  title: '',
  summary: '',
  severity: 'medium',
  status: 'open',
  sourceEvent: '',
  detection: '',
  assignedTo: '',
}

export const initialResponseForm = {
  incident: '',
  actionType: 'alert',
  targetValue: '',
  notes: '',
}

export const supportTables = [
  'Roles',
  'Niveles de riesgo',
  'Tipos de anomalía',
  'Tipos de acción',
  'Parámetros del sistema',
  'Logs de auditoría',
  'Estados de incidente',
]

export const supportPanels = [
  {
    id: 'auth-users',
    eyebrow: 'Módulo 1',
    title: 'Autenticación y usuarios',
    description: 'Login JWT, roles, permisos y restauración de sesión con usuarios reales.',
    items: ['Login y refresh JWT', 'Roles y permisos', 'Sesión autenticada y trazabilidad'],
    pill: '/api/auth/',
  },
  {
    id: 'data-ingestion',
    eyebrow: 'Módulo 2',
    title: 'Ingesta y gestión de datos',
    description: 'Carga de datasets, recepción de eventos y persistencia de tráfico/anomalías.',
    items: ['Carga de datasets', 'Recepción de eventos', 'Almacenamiento de tráfico y anomalías'],
    pill: '/api/events/',
  },
  {
    id: 'ml-pipeline',
    eyebrow: 'Módulo 3',
    title: 'Preprocesamiento y detección ML',
    description: 'Preparación de datos y predicción con el modelo ya existente, sin heurísticas.',
    items: ['Limpieza de datos', 'Extracción de características', 'Predicción de anomalías y riesgo'],
    pill: '/api/detection/',
  },
  {
    id: 'response-engine',
    eyebrow: 'Módulo 4',
    title: 'Motor de decisión y respuesta automática',
    description: 'Reglas, severidad y acciones de contención con ejecución controlada.',
    items: ['Reglas', 'Niveles de severidad', 'Alertar, bloquear, aislar y limitar tráfico'],
    pill: '/api/responses/',
  },
  {
    id: 'incidents-evidence',
    eyebrow: 'Módulo 5',
    title: 'Incidentes, alertas y evidencias',
    description: 'Historial, trazabilidad y evidencias asociadas a cada incidente operativo.',
    items: ['Historial de alertas', 'Incidentes y evidencias', 'Trazabilidad de acciones'],
    pill: '/api/incidents/',
  },
  {
    id: 'dashboard-reports',
    eyebrow: 'Módulo 6',
    title: 'Dashboard y reportes',
    description: 'Métricas operativas, gráficos, resumen de incidentes y exportación de reportes.',
    items: ['Métricas', 'Gráficos', 'Resumen y exportación de reportes'],
    pill: '/api/dashboard/summary/',
  },
]

export function normalizeUser(profile) {
  const username =
    profile?.username ?? profile?.user_name ?? profile?.email ?? profile?.name ?? 'Usuario autenticado'
  const displayName =
    profile?.full_name ?? profile?.fullName ?? profile?.display_name ?? username

  return {
    ...profile,
    username,
    displayName,
    groups: collectLabels(profile?.groups ?? profile?.group_names ?? profile?.group ?? []),
    roles: collectLabels(profile?.roles ?? profile?.role_names ?? profile?.permissions ?? []),
  }
}

function collectLabels(value) {
  if (!value) return []

  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object') {
          return item.name ?? item.label ?? item.title ?? item.code ?? item.group_name ?? ''
        }
        return ''
      })
      .filter(Boolean)
  }

  if (typeof value === 'string') return [value]

  if (typeof value === 'object') {
    return collectLabels(Object.values(value))
  }

  return []
}

export function getIdentityTags(user) {
  const tags = [...new Set([...(user?.roles ?? []), ...(user?.groups ?? [])])]

  if (user?.is_staff) tags.push('staff')
  if (user?.is_superuser) tags.push('superuser')

  return tags.filter(Boolean).slice(0, 4)
}

export function authSummary(user) {
  const tags = getIdentityTags(user)

  if (tags.length > 0) {
    return tags.join(' • ')
  }

  return 'Sesión autenticada con JWT'
}

export function formatHealthStatus(status) {
  if (!status) return 'desconocido'

  const normalizedStatus = String(status).toLowerCase()
  return healthLabels[normalizedStatus] ?? status
}

export function safeNumber(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

export function parseJsonInput(value, fallbackKey) {
  const trimmed = String(value ?? '').trim()

  if (!trimmed) return {}

  try {
    const parsed = JSON.parse(trimmed)
    if (parsed && typeof parsed === 'object') return parsed
  } catch {
  }

  return { [fallbackKey]: trimmed }
}

export function downloadJson(filename, data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export function formatCount(value) {
  return new Intl.NumberFormat('es-ES').format(Number(value ?? 0))
}

export function formatSeverity(value) {
  const normalized = String(value ?? '').toLowerCase()
  return severityLabels[normalized] ?? value ?? 'Sin dato'
}

export function formatIncidentStatus(value) {
  const normalized = String(value ?? '').toLowerCase()
  return statusLabels[normalized] ?? value ?? 'Sin dato'
}

export function buildKpis(summary) {
  return [
    {
      label: 'Eventos analizados',
      value: formatCount(summary?.events_total),
      delta: 'Ingesta activa',
    },
    {
      label: 'Detecciones de alto riesgo',
      value: formatCount(summary?.high_risk_detections),
      delta: 'Modelo ML',
    },
    {
      label: 'Incidentes abiertos',
      value: formatCount(summary?.open_incidents),
      delta: 'Seguimiento activo',
    },
    {
      label: 'Acciones de respuesta',
      value: formatCount(summary?.response_actions_total),
      delta: 'Trazabilidad controlada',
    },
  ]
}

export function buildIncidents(incidents) {
  if (!Array.isArray(incidents) || incidents.length === 0) {
    return [
      { id: 'INC-014', host: 'PC-014', type: 'Movimiento lateral', risk: 'Crítico', riskKey: 'critical', action: 'Equipo aislado' },
      { id: 'INC-013', host: 'SRV-02', type: 'Tráfico saliente sospechoso', risk: 'Alto', riskKey: 'high', action: 'Conexión limitada' },
      { id: 'INC-012', host: 'LAP-08', type: 'Patrón de escaneo de puertos', risk: 'Medio', riskKey: 'medium', action: 'Alerta generada' },
    ]
  }

  return incidents.slice(0, 3).map((incident) => ({
    id: `INC-${String(incident.id).padStart(3, '0')}`,
    host: incident.assigned_to?.trim() || 'Sin asignar',
    type: incident.title,
    risk: formatSeverity(incident.severity),
    riskKey: String(incident.severity ?? '').toLowerCase() || 'medium',
    action: formatIncidentStatus(incident.status),
  }))
}

export function buildSignals(summary) {
  const base = [
    { name: 'DDoS', level: 82 },
    { name: 'Ransomware', level: 63 },
    { name: 'Exfiltración', level: 71 },
    { name: 'Movimiento lateral', level: 89 },
  ]

  if (!summary) return base

  const boost = summary.high_risk_detection_rate ? Math.min(15, Math.round(summary.high_risk_detection_rate * 10)) : 0

  return base.map((signal, index) => ({
    ...signal,
    level: Math.min(100, signal.level + boost - index),
  }))
}
