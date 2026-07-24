// 백엔드 응답을 화면이 쓰는 모양으로 옮깁니다.
// UI 컴포넌트는 그대로 두고, 필드 이름 차이는 전부 여기서 흡수합니다.

import { krw, normalizeBenefitRate } from '../utils/format.js'

/** 카테고리별 표시 아이콘. 없는 카테고리는 카드 모양으로 떨어집니다. */
const CATEGORY_ICON = {
  카페: '☕',
  '카페/디저트': '☕',
  교통: '🚇',
  대중교통: '🚇',
  주유: '⛽',
  편의점: '🏪',
  '마트/쇼핑': '🛒',
  온라인쇼핑: '🛒',
  쇼핑: '🛍️',
  '푸드/외식': '🍽️',
  음식점: '🍽️',
  배달앱: '🛵',
  '병원/약국': '🏥',
  '공과금/생활요금': '🧾',
  공과금: '🧾',
  통신: '📱',
  '구독/멤버십': '🎬',
  영화: '🎬',
  '여행/항공': '✈️',
  해외: '✈️',
  생활: '🏠',
  모든가맹점: '💳',
}

export function iconForCategory(category) {
  return CATEGORY_ICON[category] || '💳'
}

/**
 * 보유 카드 한 장 (GET /users/{id}/cards 의 cards[] 원소) → 지갑 화면 카드.
 * CardFace 가 쓰는 필드(card_id / card_company / card_name / last_four / spent / benefit)를 맞춥니다.
 */
export function adaptCard(card) {
  return {
    card_id: card.card_id,
    user_card_id: card.user_card_id,
    card_company: card.card_company || card.issuer || '',
    card_name: card.card_name || '',
    last_four: card.card_number_last4 || '',
    nickname: card.nickname || '',
    // 화면은 포맷된 문자열을 그대로 찍습니다.
    spent: krw(card.current_month_spending || 0),
    benefit: krw(card.card_monthly_benefit_used || 0),
    // 백엔드 카드 상태에는 유효기간이 없어 비워 둡니다 (CardFace 가 알아서 감춥니다).
    expiry: '',
    // 실적·한도 막대에 쓰는 원본 숫자 (위 spent/benefit 은 포맷된 문자열입니다)
    required_spending: card.required_spending || 0,
    previous_month_spending: card.previous_month_spending || 0,
    current_month_spending: card.current_month_spending || 0,
    // 카드 한 장에 걸린 월 통합 혜택 한도와 이번 달 사용분
    benefit_limit: card.monthly_total_limit || 0,
    benefit_used: card.card_monthly_benefit_used || 0,
    benefits: Array.isArray(card.benefits) ? card.benefits.map(adaptBenefit) : [],
  }
}

/**
 * 카드 혜택 한 건 → utils/benefit.js 의 benefitView() 가 읽는 모양.
 * 필드 이름만 바꾸고 값은 손대지 않습니다.
 */
export function adaptBenefit(benefit) {
  // 정률(%)·정액(원)이 한 필드에 섞여 오므로 여기서 단위를 정상화합니다.
  // (예: 단위 '%' + 값 1000 → '원'으로 되돌려 '1000% 할인' 표기 방지)
  const { value, unit } = normalizeBenefitRate(benefit.benefit_value, benefit.benefit_unit)
  return {
    id: String(benefit.card_benefit_id ?? benefit.source_benefit_id ?? benefit.benefit_name),
    category: benefit.category || '기타',
    detail: null,
    type: benefit.benefit_type || '혜택',
    value,
    unit,
    condition: benefit.required_spending || null,
    limitMonth: benefit.monthly_benefit_limit || null,
    limitPerUse: benefit.per_transaction_limit || null,
    brands: benefit.merchant_list || null,
    desc: benefit.benefit_name || benefit.source_summary || benefit.condition_text || '',
  }
}

/**
 * 결제 내역 한 건 → 카드 상세의 '최근 결제내역' 행.
 * @param {object} tx recent_transactions[] 또는 거래 목록 API 의 원소
 */
export function adaptTransaction(tx) {
  const category = tx.payment_category || '기타'
  return {
    id: String(tx.transaction_id),
    place: tx.merchant_name || '',
    category,
    icon: iconForCategory(category),
    date: formatDate(tx.approved_at),
    amount: tx.original_payment_amount || 0,
    saved: tx.saved_amount ? `할인 ${krw(tx.saved_amount)}원` : '혜택 없음',
  }
}

/**
 * 월별 소비 리포트 응답 → 화면 모양.
 *
 * 백엔드가 총지출·전월비교·일별 누적·카테고리·카드별 혜택까지 다 주므로
 * 여기서는 필드 이름만 화면 표기에 맞춥니다. (ratio 는 이미 퍼센트 단위)
 * @param {object} r spending-report 응답
 * @param {string} label 탭에 보여줄 달 이름 (예: '6월')
 */
export function adaptSpendingReport(r, label = '') {
  return {
    key: label || r.month,
    month: r.month,
    prevMonth: r.previousMonth || '',
    spent: r.totalSpending || 0,
    prevSpent: r.previousMonthSpending || 0,
    spentDiff: r.spendingDifference || 0,
    benefit: r.totalBenefit || 0,
    prevBenefit: r.previousMonthBenefit || 0,
    benefitDiff: r.benefitDifference || 0,
    // 전월 데이터가 조금이라도 있으면 비교를 보여줍니다.
    hasPrev: (r.previousMonthSpending || 0) > 0 || (r.previousDailyCumulative || []).length > 0,
    daily: r.dailyCumulative || [],
    prevDaily: r.previousDailyCumulative || [],
    // buildDonut 이 쓰는 {name, amount} 로 맞춥니다.
    // 도넛 중앙·범례가 큰 항목부터 나오도록 금액순 정렬하고, 0원 항목은 뺍니다.
    categories: (r.categories || [])
      .map((c) => ({ name: c.category, amount: c.amount || 0 }))
      .filter((c) => c.amount > 0)
      .sort((a, b) => b.amount - a.amount),
    cards: (r.cardBenefits || []).map((c) => ({
      cardId: c.cardId,
      company: c.issuer,
      name: c.cardName,
      imageUrl: c.imageUrl || null,
      benefit: c.benefit || 0,
    })),
  }
}

/** ISO8601 → `2026.07.20` */
function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}.${mm}.${dd}`
}
