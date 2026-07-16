// 금액을 원화 형식으로 표시합니다. 예: 12000 -> "12,000원"
export function won(value) {
  const number = Number(value) || 0
  return `${number.toLocaleString('ko-KR')}원`
}
