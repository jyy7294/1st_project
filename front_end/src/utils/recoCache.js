// 소비패턴 기반 신규 카드 추천의 '오늘자' 로컬 캐시.
//
// 백엔드는 KST 자정마다 하루 1회만 추천을 실제 계산해 스냅샷으로 캐시합니다.
// 프론트도 같은 KST 날짜를 키로 결과를 저장해 두면, 로그아웃 후 다시 들어와도
// 로딩·재요청 없이 그날 추천 화면을 그대로 보여줄 수 있습니다.
// (날짜가 바뀌면 캐시가 자동 무효화돼 그날 최초 진입에서만 다시 받아옵니다.)

// 캐시 스키마/백엔드 계산 로직이 바뀌면 버전을 올려 이전 캐시를 즉시 무효화합니다.
// v2: 백엔드가 적립·캐시백(포인트 적립)을 연간 혜택에 합산하도록 수정됨(체크카드 0원 해결).
// v3: 프론트에서 total 내림차순 재정렬 + 0원 카드 제외(백엔드 정렬 버그 임시 보정).
// v4: 백엔드가 정렬·0원 제외를 정식 수정해 프론트 임시보정 제거. 백엔드 순서를 그대로 신뢰.
// v5: 결제 후 업종 재정렬을 위해 후보를 넉넉히(12장) 캐시. 이전 3장 캐시 무효화.
// v6: 후보 풀을 20장으로 확대(업종 카드가 더 많이 잡히도록). 이전 12장 캐시 무효화.
// v7: 백엔드 대표혜택 선정 개선(니치 초고할인 업종 배제·소비비중 반영) 반영. 이전 캐시 무효화.
const KEY_PREFIX = 'picka:reco:v7'

/**
 * KST(Asia/Seoul) 기준 오늘 날짜 'YYYY-MM-DD'.
 * 백엔드 스냅샷 경계(KST 00:00)와 맞춰 하루 단위 캐시 키로 씁니다.
 */
export function kstToday() {
  return new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Seoul' })
}

function keyFor(userId, type) {
  return `${KEY_PREFIX}:${userId}:${type}`
}

/**
 * 오늘자 추천 캐시를 읽습니다. 저장된 날짜가 오늘(KST)과 다르면 무효로 보고 null.
 *
 * @param {number|string} userId
 * @param {'credit'|'check'} type
 * @returns {{cards: Array, meta: object}|null}
 */
export function readRecoCache(userId, type) {
  if (!userId) return null
  try {
    const raw = localStorage.getItem(keyFor(userId, type))
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (!parsed || parsed.date !== kstToday()) return null
    return parsed.data || null
  } catch {
    return null
  }
}

/**
 * 오늘자 추천을 캐시에 저장합니다.
 *
 * @param {number|string} userId
 * @param {'credit'|'check'} type
 * @param {{cards: Array, meta: object}} data
 */
export function writeRecoCache(userId, type, data) {
  if (!userId) return
  try {
    localStorage.setItem(
      keyFor(userId, type),
      JSON.stringify({ date: kstToday(), data }),
    )
  } catch {
    // 용량 초과 등 저장 실패는 무시합니다 — 캐시는 없으면 다시 받으면 됩니다.
  }
}
