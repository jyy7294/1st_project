// 백엔드 응답을 화면이 쓰는 모양으로 옮깁니다.
// UI 컴포넌트는 그대로 두고, 필드 이름 차이는 전부 여기서 흡수합니다.

import { krw } from '../utils/format.js'

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
    // 실적 표시에 쓰는 원본 값
    required_spending: card.required_spending || 0,
    previous_month_spending: card.previous_month_spending || 0,
    benefits: Array.isArray(card.benefits) ? card.benefits.map(adaptBenefit) : [],
  }
}

/**
 * 카드 혜택 한 건 → utils/benefit.js 의 benefitView() 가 읽는 모양.
 * 필드 이름만 바꾸고 값은 손대지 않습니다.
 */
export function adaptBenefit(benefit) {
  return {
    id: String(benefit.card_benefit_id ?? benefit.source_benefit_id ?? benefit.benefit_name),
    category: benefit.category || '기타',
    detail: null,
    type: benefit.benefit_type || '혜택',
    value: benefit.benefit_value,
    unit: benefit.benefit_unit || '',
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

/** ISO8601 → `2026.07.20` */
function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}.${mm}.${dd}`
}
