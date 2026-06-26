const storageKey = 'cybershield.auth'

const errorTranslations = {
  'No active account found with the given credentials.':
    'No se encontró una cuenta activa con esas credenciales.',
  'No active account found with the given credentials':
    'No se encontró una cuenta activa con esas credenciales.',
  'Incorrect authentication credentials.': 'Las credenciales de autenticación no son correctas.',
  'Authentication credentials were not provided.': 'Faltan credenciales de autenticación.',
  'Token is invalid or expired.': 'El token no es válido o expiró.',
  'Token is invalid or expired': 'El token no es válido o expiró.',
  'The token is invalid or expired.': 'El token no es válido o expiró.',
  'Login response did not include an access token.':
    'La respuesta de inicio de sesión no incluyó un token de acceso.',
  'Refresh response did not include an access token.':
    'La respuesta de renovación no incluyó un token de acceso.',
  'Unable to sign in.': 'No fue posible iniciar sesión.',
  'Session expired. Please sign in again.': 'La sesión expiró. Inicia sesión nuevamente.',
  'Refresh response did not include an access token':
    'La respuesta de renovación no incluyó un token de acceso.',
  'Login response did not include an access token':
    'La respuesta de inicio de sesión no incluyó un token de acceso.',
  'Request failed.': 'La solicitud falló.',
}

function readStoredAuth() {
  if (typeof window === 'undefined') return null

  try {
    const raw = window.localStorage.getItem(storageKey)
    if (!raw) return null

    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? parsed : null
  } catch {
    return null
  }
}

function writeStoredAuth(auth) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(storageKey, JSON.stringify(auth))
}

function extractTokens(payload) {
  const accessToken = payload?.access ?? payload?.accessToken ?? payload?.token ?? ''
  const refreshToken = payload?.refresh ?? payload?.refreshToken ?? ''

  if (!accessToken) {
    throw new Error('La respuesta de inicio de sesión no incluyó un token de acceso.')
  }

  return { accessToken, refreshToken }
}

function extractMessage(payload, fallback) {
  if (!payload) return fallback

  if (typeof payload.detail === 'string') return errorTranslations[payload.detail] ?? payload.detail
  if (typeof payload.message === 'string') return errorTranslations[payload.message] ?? payload.message

  const firstValue = Object.values(payload).find((value) => {
    if (typeof value === 'string') return value.length > 0
    if (Array.isArray(value)) return value.length > 0
    return false
  })

  if (typeof firstValue === 'string') return errorTranslations[firstValue] ?? firstValue
  if (Array.isArray(firstValue) && typeof firstValue[0] === 'string') {
    return errorTranslations[firstValue[0]] ?? firstValue[0]
  }

  return errorTranslations[fallback] ?? fallback
}

async function parseJson(response) {
  const body = await response.text()

  if (!body) return {}

  try {
    return JSON.parse(body)
  } catch {
    return { detail: body }
  }
}

export function getStoredAuth() {
  return readStoredAuth()
}

export function clearStoredAuth() {
  if (typeof window === 'undefined') return
  window.localStorage.removeItem(storageKey)
}

export async function loginWithCredentials(username, password) {
  const response = await fetch('/api/auth/login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({ username, password }),
  })

  const payload = await parseJson(response)

  if (!response.ok) {
    throw new Error(extractMessage(payload, 'No fue posible iniciar sesión.'))
  }

  const auth = extractTokens(payload)
  writeStoredAuth(auth)
  return { auth, payload }
}

let refreshInFlight = null

async function refreshAuthToken() {
  const storedAuth = getStoredAuth()

  if (!storedAuth?.refreshToken) {
    throw new Error('La sesión expiró. Inicia sesión nuevamente.')
  }

  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      const response = await fetch('/api/auth/refresh/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({ refresh: storedAuth.refreshToken }),
      })

      const payload = await parseJson(response)

      if (!response.ok) {
        throw new Error(extractMessage(payload, 'La sesión expiró. Inicia sesión nuevamente.'))
      }

      const nextAuth = {
        accessToken: payload?.access ?? payload?.accessToken ?? payload?.token ?? '',
        refreshToken: payload?.refresh ?? storedAuth.refreshToken,
      }

      if (!nextAuth.accessToken) {
        throw new Error('La respuesta de renovación no incluyó un token de acceso.')
      }

      writeStoredAuth(nextAuth)
      return nextAuth
    })().finally(() => {
      refreshInFlight = null
    })
  }

  return refreshInFlight
}

export async function apiRequest(path, options = {}) {
  const { auth = true, retry = true, ...init } = options
  const headers = new Headers(init.headers || {})

  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json')
  }

  if (auth) {
    const storedAuth = getStoredAuth()
    if (storedAuth?.accessToken) {
      headers.set('Authorization', `Bearer ${storedAuth.accessToken}`)
    }
  }

  const response = await fetch(path, { ...init, headers })

  if (response.status !== 401 || !auth || !retry) {
    return response
  }

  try {
    const refreshedAuth = await refreshAuthToken()
    headers.set('Authorization', `Bearer ${refreshedAuth.accessToken}`)
    return fetch(path, { ...init, headers })
  } catch {
    clearStoredAuth()
    return response
  }
}

export async function requestJson(path, options = {}) {
  const response = await apiRequest(path, options)
  const payload = await parseJson(response)

  if (!response.ok) {
    if (response.status === 401) {
      clearStoredAuth()
    }

    throw new Error(extractMessage(payload, 'La solicitud falló.'))
  }

  return payload
}
