// PICKA 백엔드(FastAPI) 호출 공통부.
//
// 주소는 .env 의 VITE_API_BASE 로 바꿀 수 있습니다. 기본값은 로컬 백엔드입니다.
// 백엔드 CORS 가 http://localhost:5173 만 허용하므로 프론트 포트는 5173 고정입니다.

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

/** 응답이 너무 늦으면 화면이 멈추므로 여기서 끊습니다. */
const TIMEOUT_MS = 8000

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/**
 * 백엔드 호출. 실패는 모두 ApiError 로 통일합니다.
 *
 * @param {string} path `/api/v1/...`
 * @param {{method?: string, body?: object, timeout?: number}} [options]
 */
export async function request(path, options = {}) {
  const { method = 'GET', body, timeout = TIMEOUT_MS } = options

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)

  let response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
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
