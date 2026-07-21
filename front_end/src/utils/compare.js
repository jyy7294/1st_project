// 백엔드 comparison[] 을 화면 표시 순서로 다룹니다.
//
// 백엔드(recommend_cards)가 이미 최종 순위를 정해서 내려줍니다.
// rank 1(is_recommended=true) 카드가 배열 맨 앞이고,
// recommendation_basis 가 performance_tiebreak / performance_only 인 경우
// 추천 카드는 "혜택 최대"가 아니라 "전월 실적 달성에 유리한" 카드입니다.
// 그래서 프론트에서 다시 정렬하면 백엔드의 판단을 버리게 됩니다.

/** 백엔드가 정한 순서 그대로의 비교 목록을 돌려줍니다. (방어적 복사) */
export function orderedComparison(comparison) {
  if (!Array.isArray(comparison)) return []
  return [...comparison]
}

/**
 * 기본 선택 카드의 index. 백엔드가 is_recommended 로 표시한 카드를 씁니다.
 * 표시된 카드가 없으면 0 (목록 첫 카드).
 */
export function recommendedIndex(comparison) {
  if (!Array.isArray(comparison)) return 0
  const found = comparison.findIndex((card) => card?.is_recommended === true)
  return found >= 0 ? found : 0
}

/** 모든 카드가 혜택 대상이 아닌지 — 200 응답이지만 실질적으로 "혜택 카드 없음". */
export function hasNoEligibleCard(comparison) {
  if (!Array.isArray(comparison) || comparison.length === 0) return false
  return comparison.every((card) => card?.eligible === false)
}
