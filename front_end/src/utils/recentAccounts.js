// 최근 로그인 계정 목록 — 로그인 화면의 '계정 선택(자동완성)' 편의 기능.
//
// 저장 항목은 userId·email·name·lastLoginAt 뿐입니다.
// 비밀번호와 토큰은 설계상 이 모듈에 들어올 수 없습니다(인자로도 받지 않음).
// 민감정보가 아니므로 브라우저를 닫아도 유지되도록 localStorage 에 둡니다.
// (인증 토큰은 별도로 sessionStorage 에만 보관 — api/client.js 참고.)

const KEY = 'picka_recent_accounts'
const MAX = 4

export function getRecentAccounts() {
  try {
    const raw = localStorage.getItem(KEY)
    const list = raw ? JSON.parse(raw) : []
    return Array.isArray(list) ? list : []
  } catch {
    return []
  }
}

function save(list) {
  try {
    localStorage.setItem(KEY, JSON.stringify(list.slice(0, MAX)))
  } catch {
    // localStorage 를 못 쓰는 환경이면 조용히 무시합니다.
  }
}

/**
 * 로그인 성공 시 호출. 같은 계정은 최신으로 끌어올리고 최대 3개만 유지합니다.
 * @param {{userId: number, email: string, name?: string}} account
 * @returns {Array} 갱신된 목록
 */
export function recordLogin({ userId, email, name } = {}) {
  if (!userId || !email) return getRecentAccounts()
  const entry = {
    userId,
    email,
    name: name || '',
    lastLoginAt: new Date().toISOString(),
  }
  const next = [entry, ...getRecentAccounts().filter((a) => a.userId !== userId)]
  save(next)
  return next.slice(0, MAX)
}

/** 목록에서 계정 하나를 지웁니다. @returns {Array} 갱신된 목록 */
export function removeRecentAccount(userId) {
  const next = getRecentAccounts().filter((a) => a.userId !== userId)
  save(next)
  return next
}

/** 'N일 전' 같은 상대 시각. 목록 표시용. */
export function formatLastLogin(iso) {
  if (!iso) return ''
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return ''
  const diff = Date.now() - then
  const min = Math.floor(diff / 60000)
  if (min < 1) return '방금 전'
  if (min < 60) return `${min}분 전`
  const hour = Math.floor(min / 60)
  if (hour < 24) return `${hour}시간 전`
  const day = Math.floor(hour / 24)
  if (day < 30) return `${day}일 전`
  return new Date(iso).toLocaleDateString('ko-KR')
}
