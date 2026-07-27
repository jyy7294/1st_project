// 백엔드 응답을 화면이 쓰는 모양으로 옮깁니다.
// UI 컴포넌트는 그대로 두고, 필드 이름 차이는 전부 여기서 흡수합니다.

import { krw, normalizeBenefitRate } from '../utils/format.js'
import { categoryStyle } from '../utils/benefit.js'

/** 카테고리별 표시 아이콘. 혜택 목록과 같은 촘촘한 맵(categoryStyle)을 씁니다. */
export function iconForCategory(category) {
  return categoryStyle(category).icon
}

/**
 * 같은 카테고리라도 가맹점 성격이 결이 다르면 아이콘만 따로 줍니다.
 * (예: 교보문고는 카드사 기준 '영화/문화'로 분류되지만 서점이라 책 아이콘이 자연스럽습니다.)
 * 배경색은 카테고리 색을 그대로 두어 업종 구분은 유지합니다.
 */
const MERCHANT_ICON_OVERRIDE = [
  { test: /문고|서점|북스|book/i, icon: '📚' },
]

function transactionStyle(merchantName, category) {
  const base = categoryStyle(category)
  const hit = MERCHANT_ICON_OVERRIDE.find((o) => o.test.test(merchantName || ''))
  return hit ? { ...base, icon: hit.icon } : base
}

/**
 * 보유 카드 한 장 (GET /users/{id}/cards 의 cards[] 원소) → 지갑 화면 카드.
 * CardFace 가 쓰는 필드(card_id / card_company / card_name / last_four / spent / benefit)를 맞춥니다.
 */
export function adaptCard(card) {
  return {
    card_id: card.card_id,
    user_card_id: card.user_card_id,
    // 카드고릴라 원본 카드 id. 상세 혜택 화면이 카드사 안내 링크를 만들 때 씁니다.
    source_card_id: card.source_card_id ?? null,
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
    limitYear: benefit.annual_limit || null,
    brands: benefit.merchant_list || null,
    desc: benefit.benefit_name || benefit.source_summary || benefit.condition_text || '',
    // 카드사 원문. benefitView 가 첫 줄은 부제로, 나머지는 유의사항으로 풀어 씁니다.
    summary: benefit.source_summary || null,
    detailText: benefit.source_detail || null,
  }
}

/**
 * 결제 내역 한 건 → 카드 상세의 '최근 결제내역' 행.
 * @param {object} tx recent_transactions[] 또는 거래 목록 API 의 원소
 */
export function adaptTransaction(tx) {
  const category = tx.payment_category || '기타'
  const style = transactionStyle(tx.merchant_name, category)
  return {
    id: String(tx.transaction_id),
    place: tx.merchant_name || '',
    category,
    icon: style.icon,
    // 카테고리별 파스텔 배경 — 결제내역 아이콘이 회색 하나로 뭉치지 않고 업종별로 구분됩니다.
    tint: style.tint,
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
