// PICKA 백엔드(FastAPI) 호출 공통부.
//
// 주소는 .env 의 VITE_API_BASE 로 바꿀 수 있습니다. 기본값은 로컬 백엔드입니다.
// 백엔드 CORS 가 http://localhost:5173 만 허용하므로 프론트 포트는 5173 고정입니다.

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

/** 응답이 너무 늦으면 화면이 멈추므로 여기서 끊습니다. */
const TIMEOUT_MS = 8000

// ── 인증 토큰 보관 ─────────────────────────────────────────────────────────
// 백엔드가 JWT 인증을 요구하므로 로그인 때 받은 토큰을 여기 보관하고, 모든 보호 API
// 요청에 Authorization 헤더로 실어 보냅니다. request() 는 React 상태에 접근할 수
// 없어 모듈 변수로 두고, 새로고침 복구를 위해 sessionStorage 에만 담습니다.
// (탭을 닫으면 사라지도록 localStorage 에는 장기 보관하지 않습니다.)
//
// 토큰은 이 계층(모듈 + sessionStorage)이 단일 원본입니다. 요청 시점에 여기서 읽고,
// 조용한 401 재발급도 여기서 갱신하므로 화면 상태와 어긋날 일이 없습니다.
const STORAGE_KEY = 'picka_auth'

let accessToken = null
let refreshToken = null

function persist() {
  try {
    if (accessToken || refreshToken) {
      sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ accessToken, refreshToken }),
      )
    } else {
      sessionStorage.removeItem(STORAGE_KEY)
    }
  } catch {
    // sessionStorage 를 못 쓰는 환경이면 메모리에만 둡니다.
  }
}

// 새로고침 직후 모듈이 처음 로드될 때 sessionStorage 에서 토큰을 되살립니다.
try {
  const raw = sessionStorage.getItem(STORAGE_KEY)
  if (raw) {
    const parsed = JSON.parse(raw)
    accessToken = parsed?.accessToken || null
    refreshToken = parsed?.refreshToken || null
  }
} catch {
  accessToken = null
  refreshToken = null
}

/** 로그인·재발급 성공 시 토큰을 저장합니다. */
export function setTokens(access, refresh) {
  accessToken = access || null
  refreshToken = refresh || null
  persist()
}

/** 로그아웃·세션 만료 시 토큰을 모두 지웁니다. */
export function clearTokens() {
  accessToken = null
  refreshToken = null
  persist()
}

export function getAccessToken() {
  return accessToken
}

export function getRefreshToken() {
  return refreshToken
}

/** 새로고침 복구를 시도할지 판단할 때 씁니다. */
export function hasRefreshToken() {
  return Boolean(refreshToken)
}

// refresh 까지 실패했을 때 화면을 로그인으로 되돌리기 위한 콜백. AppProvider 가 등록합니다.
// (API 계층은 React 를 모르므로 이 훅으로만 화면에 알립니다.)
let authFailureHandler = null

export function onAuthFailure(handler) {
  authFailureHandler = handler || null
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// 이 경로들은 401 자동 재발급 대상에서 제외합니다(무한 루프 방지).
const AUTH_PATHS = [
  '/api/v1/auth/login',
  '/api/v1/auth/refresh',
  '/api/v1/auth/logout',
]

function isAuthPath(path) {
  return AUTH_PATHS.some((p) => path.startsWith(p))
}

// ── Access Token 자동 재발급 ───────────────────────────────────────────────
// 동시에 여러 요청이 401 을 받아도 refresh 는 한 번만 호출되도록 refreshPromise
// 하나만 유지합니다. 첫 401 이 재발급을 돌리고, 나머지는 같은 Promise 를 기다립니다.
let refreshPromise = null

/**
 * refresh_token 으로 새 토큰을 받아옵니다.
 * 백엔드는 회전(rotation) 방식이라 응답의 새 refresh_token 으로 반드시 교체합니다.
 * @returns {Promise<{ok: boolean, user?: object}>}
 */
export function refreshTokens() {
  if (!refreshToken) return Promise.resolve({ ok: false })
  if (!refreshPromise) {
    refreshPromise = doRefresh(refreshToken).finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

async function doRefresh(currentRefresh) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: currentRefresh }),
    })
    if (!res.ok) return { ok: false }
    const data = await res.json().catch(() => null)
    if (!data?.access_token) return { ok: false }
    // 회전: 새 refresh_token 으로 즉시 교체(없으면 기존 것을 유지).
    setTokens(data.access_token, data.refresh_token || currentRefresh)
    return { ok: true, user: data.user || null }
  } catch {
    return { ok: false }
  }
}

/**
 * 백엔드 호출. 실패는 모두 ApiError 로 통일합니다.
 *
 * 보호 API 가 401 을 주면 refresh 후 원 요청을 딱 한 번 재시도합니다.
 *
 * @param {string} path `/api/v1/...`
 * @param {{method?: string, body?: object, timeout?: number, _retried?: boolean}} [options]
 */
export async function request(path, options = {}) {
  const { method = 'GET', body, timeout = TIMEOUT_MS, _retried = false } = options

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)

  const headers = {}
  if (body) headers['Content-Type'] = 'application/json'
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`

  let response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers: Object.keys(headers).length ? headers : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    })
  } catch (err) {
    if (err?.name === 'AbortError') {
      throw new ApiError('응답이 지연되고 있어요. 잠시 후 다시 시도해 주세요.', 408)
    }
    throw new ApiError('서버에 연결하지 못했습니다.', 0)
  } finally {
    clearTimeout(timer)
  }

  // Access Token 만료(401) → refresh 후 원 요청을 한 번만 재시도합니다.
  // 인증 엔드포인트 자체·이미 재시도한 요청·refresh_token 이 없는 경우는 제외합니다.
  if (
    response.status === 401 &&
    !_retried &&
    !isAuthPath(path) &&
    refreshToken
  ) {
    const result = await refreshTokens()
    if (result?.ok) {
      return request(path, { ...options, _retried: true })
    }
    // refresh 까지 실패 → 세션 폐기 후 로그인 화면으로 되돌립니다.
    clearTokens()
    if (authFailureHandler) authFailureHandler()
    throw new ApiError('세션이 만료되었습니다. 다시 로그인해 주세요.', 401)
  }

  if (response.status === 204) return null

  let data = null
  try {
    data = await response.json()
  } catch {
    data = null
  }

  if (!response.ok) {
    // FastAPI 는 오류 사유를 detail 에 담아 줍니다. 문자열이 아닌 경우(422)도 있습니다.
    const detail = data?.detail
    const message =
      typeof detail === 'string' ? detail : '요청을 처리하지 못했습니다.'
    throw new ApiError(message, response.status)
  }

  return data
}
