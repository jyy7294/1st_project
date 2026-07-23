/** 숫자를 천 단위 구분 문자열로 만듭니다. 예: 12000 -> "12,000" */
export function krw(value) {
  return Number(value || 0).toLocaleString('ko-KR')
}

/**
 * 차감 금액(연회비·할인 등) 표기.
 *
 * 0원이면 '-0' 처럼 어색하게 보이므로 부호를 붙이지 않습니다.
 * 예: 15000 -> "-15,000",  0 -> "0"
 */
export function krwMinus(value) {
  const won = Number(value || 0)
  return won > 0 ? `-${krw(won)}` : krw(won)
}

/**
 * 연회비 표기. 0원이면 '0원'보다 '없음'이 읽기 쉽습니다.
 * 예: 15000 -> "-15,000원",  0 -> "없음"
 */
export function feeText(fee) {
  const won = Number(fee || 0)
  return won > 0 ? `-${krw(won)}원` : '없음'
}

/** '318,000' 처럼 포맷된 금액 문자열을 숫자로 되돌립니다. 예: "318,000" -> 318000 */
export function parseKrw(value) {
  if (typeof value === 'number') return value
  return Number(String(value || '').replace(/[^0-9]/g, '')) || 0
}
