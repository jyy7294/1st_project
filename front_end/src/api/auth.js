// 목업 로그인. 백엔드에 인증 API가 없어서 프론트에서 검증합니다.
// 실제 인증 API가 생기면 verifyLogin() 안쪽만 교체하면 됩니다.

const DEMO_ID = 'KDA4'
const DEMO_PW = '1234'

/** 소셜 로그인 버튼이 새 탭으로 여는 주소. */
export const SOCIAL_URL = {
  kakao: 'https://accounts.kakao.com/login/?continue=https%3A%2F%2Fwww.kakao.com',
  naver: 'https://nid.naver.com/nidlogin.login',
}

/**
 * 아이디·비밀번호를 검증합니다.
 * @returns {{ok: true} | {ok: false, message: string}}
 */
export function verifyLogin(id, pw) {
  if (id.trim() === DEMO_ID && pw === DEMO_PW) return { ok: true }
  return { ok: false, message: '아이디 또는 비밀번호가 올바르지 않아요.' }
}
