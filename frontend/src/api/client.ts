export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown
  ) {
    super(typeof body === 'string' ? body : `HTTP ${status}`)
    this.name = 'ApiError'
  }
}

function getBaseUrl(): string {
  const env = import.meta.env.VITE_API_BASE_URL
  if (env && env.length > 0) {
    return env.replace(/\/$/, '')
  }
  return ''
}

let refreshPromise: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const refresh = localStorage.getItem('refresh')
      if (!refresh) return null

      const res = await fetch(`${getBaseUrl()}/api/auth/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      })

      if (!res.ok) {
        localStorage.removeItem('access')
        localStorage.removeItem('refresh')
        return null
      }

      const data = (await res.json()) as { access: string; refresh?: string }
      localStorage.setItem('access', data.access)
      if (data.refresh) {
        localStorage.setItem('refresh', data.refresh)
      }
      return data.access
    })().finally(() => {
      refreshPromise = null
    })
  }

  return refreshPromise
}

type JsonOptions = {
  method?: string
  body?: unknown
  skipAuth?: boolean
}

export async function apiJson<T>(path: string, options: JsonOptions = {}): Promise<T> {
  const { method = 'GET', body, skipAuth = false } = options
  const bodyStr = body !== undefined ? JSON.stringify(body) : undefined

  const send = async (token: string | null) => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (token && !skipAuth) {
      headers.Authorization = `Bearer ${token}`
    }
    return fetch(`${getBaseUrl()}${path}`, {
      method,
      headers,
      body: bodyStr,
    })
  }

  let token: string | null = skipAuth ? null : localStorage.getItem('access')
  let res = await send(token)

  if (res.status === 401 && !skipAuth) {
    const newAccess = await refreshAccessToken()
    if (newAccess) {
      res = await send(newAccess)
    }
  }

  if (!res.ok) {
    const text = await res.text()
    let parsed: unknown = text
    try {
      parsed = text ? JSON.parse(text) : text
    } catch {
      /* raw text */
    }
    throw new ApiError(res.status, parsed)
  }

  if (res.status === 204) {
    return undefined as T
  }

  const ct = res.headers.get('content-type')
  if (!ct?.includes('application/json')) {
    return undefined as T
  }

  return (await res.json()) as T
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem('access', access)
  localStorage.setItem('refresh', refresh)
}

export function clearTokens() {
  localStorage.removeItem('access')
  localStorage.removeItem('refresh')
}

export function getStoredAccess(): string | null {
  return localStorage.getItem('access')
}
