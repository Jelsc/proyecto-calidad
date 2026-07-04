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

export const trafficIngestionExamples = [
  {
    id: 'benign-check',
    label: 'Ejemplo benigno',
    description: 'Un solo objeto JSON con una verificación normal de servicio.',
    payload: {
      source_ip: '10.0.0.21',
      destination_ip: '10.0.1.15',
      protocol: 'HTTPS',
      destination_port: 443,
      payload: {
        method: 'GET',
        path: '/health',
        status: 200,
        latency_ms: 18,
      },
      metadata: {
        scenario: 'health-check',
        service: 'api-gateway',
        tag: 'benign',
      },
    },
  },
  {
    id: 'suspicious-burst',
    label: 'Ejemplo sospechoso',
    description: 'Un array de eventos para simular actividad lateral y un intento de credenciales.',
    payload: [
      {
        source_ip: '203.0.113.44',
        destination_ip: '10.0.1.25',
        protocol: 'TCP',
        destination_port: 445,
        payload: 'SMB negotiation attempt from external host',
        metadata: {
          scenario: 'lateral-movement',
          severity_hint: 'high',
          tag: 'suspicious',
        },
      },
      {
        source_ip: '203.0.113.44',
        destination_ip: '10.0.1.26',
        protocol: 'HTTP',
        destination_port: 80,
        payload: {
          method: 'POST',
          path: '/admin/login',
          user_agent: 'curl/8.0.1',
          body: 'username=admin&password=admin',
        },
        metadata: {
          scenario: 'credential-stuffing',
          suspicious: true,
          tag: 'suspicious',
        },
      },
    ],
  },
]

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

export function prettyJson(value) {
  return JSON.stringify(value, null, 2)
}

export function parseTrafficIngestionPayload(value) {
  const trimmed = String(value ?? '').trim()

  if (!trimmed) {
    throw new Error('Pegá o cargá un JSON antes de enviar.')
  }

  let parsed

  try {
    parsed = JSON.parse(trimmed)
  } catch {
    throw new Error('El contenido no es un JSON válido.')
  }

  if (Array.isArray(parsed)) {
    if (parsed.length === 0) {
      throw new Error('El array JSON no puede estar vacío.')
    }

    if (parsed.some((item) => !item || typeof item !== 'object' || Array.isArray(item))) {
      throw new Error('Cada elemento del array debe ser un objeto JSON.')
    }

    return parsed
  }

  if (parsed && typeof parsed === 'object') {
    return parsed
  }

  throw new Error('El JSON debe ser un objeto o un array de objetos.')
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

export function formatDurationSeconds(value) {
  const numeric = Number(value)

  if (!Number.isFinite(numeric)) {
    return '—'
  }

  return `${numeric.toFixed(2)} s`
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
      value: formatCount(summary?.events_analyzed_total ?? summary?.events_total),
      delta: 'Scoring completado',
    },
    {
      label: 'Alertas activas',
      value: formatCount(summary?.active_alerts_total ?? summary?.open_incidents),
      delta: 'Incidentes en curso',
    },
    {
      label: 'Hosts sospechosos',
      value: formatCount(summary?.suspicious_hosts_total),
      delta: 'Detección de riesgo',
    },
    {
      label: 'Hosts aislados',
      value: formatCount(summary?.isolated_hosts_total),
      delta: 'Respuesta controlada',
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
