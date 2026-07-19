// 백엔드 comparison[] 을 화면 표시 순서로 정렬합니다.
// 혜택 금액 내림차순, 같으면 혜택 적용 가능한 카드가 먼저.
export function sortByBenefit(comparison) {
  if (!Array.isArray(comparison)) return []

  return [...comparison].sort((a, b) => {
    const diff = (b.expected_benefit || 0) - (a.expected_benefit || 0)
    if (diff !== 0) return diff
    return Number(b.eligible) - Number(a.eligible)
  })
}
