// 로그인 / 세션 복구 / 로그아웃.
//
// 백엔드가 JWT 인증을 요구합니다. 로그인 응답의 access_token·refresh_token 을 저장해
// 두고(client.js 가 sessionStorage 에 보관), 이후 모든 보호 API 요청에 Authorization:
// Bearer 헤더로 실어 보냅니다. 사용자 식별용 user_id 는 지금도 URL 경로에 함께 실립니다.

import {
  API_BASE,
  request,
  setTokens,
  clearTokens,
  refreshTokens,
  getAccessToken,
  getRefreshToken,
} from './client.js'

export { API_BASE }

/** 백엔드 user(_id 표기)를 프론트 표기(userId)로 맞춥니다. */
function adaptUser(raw, fallbackEmail = '') {
  const userId = raw?.user_id
  if (!userId) return null
  return {
    userId,
    email: raw?.email || fallbackEmail,
    name: raw?.name || '',
  }
}

/**
 * 아이디(이메일)·비밀번호로 로그인합니다.
 *
 * @returns {Promise<{ok: true, user: {userId: number, email: string, name: string},
 *                    accessToken: string|null, refreshToken: string|null}
 *                  | {ok: false, message: string}>}
 */
export async function login(id, pw) {
  const email = id.trim()

  try {
    const data = await request('/api/v1/auth/login', {
      method: 'POST',
      body: { email, password: pw },
    })

    const user = adaptUser(data?.user, email)
    if (!user) {
      return { ok: false, message: '로그인 응답에 사용자 정보가 없어요.' }
    }

    // 토큰을 저장해야 이후 인증이 필요한 요청이 통과합니다.
    const accessToken = data?.access_token || null
    const refreshToken = data?.refresh_token || null
    setTokens(accessToken, refreshToken)

    return { ok: true, user, accessToken, refreshToken }
  } catch (err) {
    return { ok: false, message: err?.message || '로그인에 실패했어요.' }
  }
}

/**
 * 새로고침 복구 — sessionStorage 에 남은 refresh_token 으로 세션을 되살립니다.
 * 성공하면 새 토큰이 저장되고 사용자 정보를 돌려줍니다. 실패하면 토큰을 비웁니다.
 *
 * @returns {Promise<{ok: true, user: object, accessToken: string|null, refreshToken: string|null}
 *                  | {ok: false}>}
 */
export async function restoreSession() {
  const result = await refreshTokens()
  if (!result?.ok) {
    clearTokens()
    return { ok: false }
  }
  const user = adaptUser(result.user)
  if (!user) {
    clearTokens()
    return { ok: false }
  }
  return {
    ok: true,
    user,
    accessToken: getAccessToken(),
    refreshToken: getRefreshToken(),
  }
}

/**
 * 로그아웃 — 백엔드에 refresh_token 폐기를 요청합니다.
 * 성공·실패와 무관하게 프론트의 토큰은 반드시 지웁니다.
 */
export async function logout() {
  const refreshToken = getRefreshToken()
  try {
    if (refreshToken) {
      await request('/api/v1/auth/logout', {
        method: 'POST',
        body: { refresh_token: refreshToken },
      })
    }
  } catch {
    // 서버 로그아웃 실패해도 아래에서 로컬 토큰을 정리합니다.
  } finally {
    clearTokens()
  }
}
