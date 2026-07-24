// 로그인.
//
// 백엔드 POST /api/v1/auth/login 응답이 성공한 경우에만 로그인 처리합니다.
// 백엔드에 인증 미들웨어가 없어 access_token 은 검증되지 않으므로,
// 응답으로 받은 user.user_id 를 이후 모든 API 호출에 실어 보냅니다.

import { API_BASE, request } from './client.js'

export { API_BASE }

/**
 * 아이디(이메일)·비밀번호로 로그인합니다.
 *
 * @returns {Promise<{ok: true, user: {userId: number, email: string, name: string}, token: string|null}
 *                  | {ok: false, message: string}>}
 */
export async function login(id, pw) {
  const email = id.trim()

  try {
    const data = await request('/api/v1/auth/login', {
      method: 'POST',
      body: { email, password: pw },
    })

    const userId = data?.user?.user_id
    if (!userId) {
      return { ok: false, message: '로그인 응답에 사용자 정보가 없어요.' }
    }

    return {
      ok: true,
      token: data?.access_token || null,
      user: {
        userId,
        email: data?.user?.email || email,
        name: data?.user?.name || '',
      },
    }
  } catch (err) {
    return { ok: false, message: err?.message || '로그인에 실패했어요.' }
  }
}
