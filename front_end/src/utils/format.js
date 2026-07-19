/** 숫자를 천 단위 구분 문자열로 만듭니다. 예: 12000 -> "12,000" */
export function krw(value) {
  return Number(value || 0).toLocaleString('ko-KR')
}

/** 금액을 원화 표시로 만듭니다. 예: 12000 -> "12,000원" */
export function won(value) {
  return `${krw(value)}원`
}
