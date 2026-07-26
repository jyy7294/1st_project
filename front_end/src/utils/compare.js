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

/**
 * 화면에 보여줄 업종.
 *
 * 업종은 백엔드가 가맹점명으로 판정합니다(merchant_aliases). 그 결과가
 * 응답 transaction.category 로 오므로 이 값을 우선합니다. 아직 추천 결과가
 * 없거나(수신 화면) 호출이 실패했을 때만 QR 에 적힌 업종으로 대신합니다.
 *
 * @param {object} result 추천 API 응답
 * @param {object} transaction QR 로 받은 결제정보
 */
export function displayCategory(result, transaction) {
  return result?.transaction?.category || transaction?.payment_category || ''
}

/** 모든 카드가 혜택 대상이 아닌지 — 200 응답이지만 실질적으로 "혜택 카드 없음". */
export function hasNoEligibleCard(comparison) {
  if (!Array.isArray(comparison) || comparison.length === 0) return false
  return comparison.every((card) => card?.eligible === false)
}

/**
 * 사용자가 직접 카드를 골라야 하는 상황인지.
 *
 * 백엔드는 혜택이 하나도 없을 때 두 갈래로 답합니다.
 *  - performance_only: 즉시 혜택은 없지만 전월 실적에 유리한 카드를 추천 (recommended_card 있음)
 *  - user_selection : 혜택도 실적도 딱히 나을 게 없어 직접 고르라고 함 (selection_required=true)
 * 앞의 경우는 추천을 그대로 보여줘야 하고, 뒤의 경우에만 "직접 선택" 화면을 띄웁니다.
 *
 * @param {object} result 추천 API 응답
 * @param {boolean} noEligibleCard 404 (보유 카드 자체가 없음)
 */
export function needsManualSelection(result, noEligibleCard) {
  if (noEligibleCard) return true
  return result?.selection_required === true
}

/** 즉시 혜택 없이 전월 실적만 보고 추천한 경우인지. */
export function isPerformanceOnly(result) {
  return result?.recommendation_basis === 'performance_only'
}
