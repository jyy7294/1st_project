/** 숫자를 천 단위 구분 문자열로 만듭니다. 예: 12000 -> "12,000" */
export function krw(value) {
  return Number(value || 0).toLocaleString('ko-KR')
}

/** '318,000' 처럼 포맷된 금액 문자열을 숫자로 되돌립니다. 예: "318,000" -> 318000 */
export function parseKrw(value) {
  if (typeof value === 'number') return value
  return Number(String(value || '').replace(/[^0-9]/g, '')) || 0
}
