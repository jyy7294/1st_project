// 혜택 원본 데이터(data/benefits.js)를 화면에 쓸 문자열·아이콘으로 바꿉니다.
// 카드 상세와 전체 혜택 화면이 같은 표기를 쓰도록 이 파일 하나만 씁니다.

import { krw, normalizeBenefitRate } from './format.js'

// 배경 틴트 — 아이콘 색감에 맞춰 몇 가지만 돌려 씁니다.
const BLUE = '#e6f0ff'
const MINT = '#e6faf7'
const PEACH = '#fdeee2'
const CREAM = '#fef3e2'
const LILAC = '#eef0ff'
const PINK = '#fdeaf1'
const GRAY = '#f4f6fa'

/*
 * 카테고리별 아이콘과 배경 틴트.
 *
 * 카드 DB 의 카테고리 43종을 모두 덮어 두어, 서로 다른 업종이 같은 아이콘으로
 * 보이지 않게 했습니다. (예전에는 표에 없는 업종이 전부 ✦ 로 떨어졌습니다.)
 * 포인트·마일리지 계열만 의도적으로 보석 아이콘을 함께 씁니다.
 */
const STYLE_BY_CATEGORY = {
  // 생활 · 쇼핑
  '마트/쇼핑': { icon: '🛒', tint: CREAM },
  온라인쇼핑: { icon: '📦', tint: CREAM },
  편의점: { icon: '🏪', tint: CREAM },
  생활: { icon: '🏠', tint: MINT },
  '공과금/생활요금': { icon: '🧾', tint: BLUE },
  통신: { icon: '📱', tint: BLUE },
  '반려동물': { icon: '🐾', tint: MINT },

  // 먹거리
  '푸드/외식': { icon: '🍽️', tint: PEACH },
  '카페/디저트': { icon: '☕', tint: PEACH },
  배달앱: { icon: '🛵', tint: PEACH },
  베이커리: { icon: '🥐', tint: PEACH },

  // 이동
  교통: { icon: '🚇', tint: BLUE },
  주유: { icon: '⛽', tint: CREAM },
  '자동차/정비': { icon: '🚗', tint: BLUE },

  // 여가 · 문화
  '영화/문화': { icon: '🎬', tint: LILAC },
  '테마파크/레저': { icon: '🎢', tint: PINK },
  '구독/멤버십': { icon: '📺', tint: LILAC },
  '여행/숙박': { icon: '🏨', tint: BLUE },
  '항공/마일리지': { icon: '✈️', tint: BLUE },
  공항서비스: { icon: '🛫', tint: BLUE },
  공항라운지: { icon: '🛋️', tint: LILAC },
  PP: { icon: '🎫', tint: LILAC },
  면세점: { icon: '🛍️', tint: PINK },
  해외: { icon: '🌏', tint: MINT },

  // 건강 · 뷰티 · 교육
  '뷰티/피트니스': { icon: '💄', tint: PINK },
  '병원/약국': { icon: '🏥', tint: MINT },
  '교육/육아': { icon: '🎓', tint: LILAC },

  // 금융 · 결제
  모든가맹점: { icon: '💳', tint: GRAY },
  금융서비스: { icon: '🏦', tint: BLUE },
  간편결제: { icon: '📲', tint: BLUE },
  캐시백: { icon: '💰', tint: CREAM },
  '멤버십/포인트': { icon: '💎', tint: LILAC },
  멤버십포인트: { icon: '💎', tint: LILAC },
  '바우처/기프트': { icon: '🎁', tint: PINK },
  할인: { icon: '🏷️', tint: CREAM },

  // 기타 표기용
  프리미엄서비스: { icon: '🛎️', tint: LILAC },
  '우대 서비스': { icon: '🎖️', tint: CREAM },
  '기본 혜택': { icon: '✅', tint: MINT },
  '추가 혜택': { icon: '➕', tint: MINT },
  선택형: { icon: '🔀', tint: GRAY },
  국민행복: { icon: '🤝', tint: PINK },
  유의사항: { icon: 'ℹ️', tint: GRAY },
  기타: { icon: '✦', tint: GRAY },
}

const DEFAULT_STYLE = { icon: '✦', tint: GRAY }

/** 만원 단위가 딱 떨어지면 '30만원', 아니면 '350,000원'으로 씁니다. */
function moneyShort(won) {
  if (won >= 10000 && won % 10000 === 0) return `${won / 10000}만원`
  return `${krw(won)}원`
}

/**
 * 혜택 한 건을 화면 표기로 변환합니다.
 *
 * @param {object} benefit data/benefits.js 의 원소
 * @returns {{
 *   id: string, icon: string, tint: string, title: string, rate: string,
 *   desc: string, limitText: string, conditionText: string, notes: string[]
 * }}
 */
export function benefitView(benefit) {
  const style = STYLE_BY_CATEGORY[benefit.category] || DEFAULT_STYLE
  const where = benefit.detail || benefit.category

  /*
   * '해외 수수료 면제'처럼 숫자가 없는 혜택은 value 가 비어 옵니다.
   * 그대로 이어붙이면 '금융서비스 null 면제/우대' 가 되므로 숫자 부분을 통째로 뺍니다.
   */
  const hasValue = benefit.value !== null && benefit.value !== undefined && benefit.value !== ''
  // 정률(%)에 100 초과 값이 오면 정액(원)으로 정상화해 '1000%' 표기를 막습니다.
  const { value: rateValue, unit: rateUnit } = normalizeBenefitRate(benefit.value, benefit.unit)
  const rate = hasValue ? `${rateValue}${rateUnit}` : ''

  // 제목은 있는 조각만 이어 붙입니다. 카테고리와 유형이 같으면(기타/기타) 한 번만 씁니다.
  const title = [where, rate, benefit.type !== where ? benefit.type : '']
    .filter(Boolean)
    .join(' ')

  const notes = []
  if (benefit.desc) notes.push(benefit.desc)
  notes.push(
    benefit.brands
      ? `적용처 · ${benefit.brands.split('|').join(', ')}`
      : '해당 카테고리 가맹점 전체 적용',
  )
  if (benefit.limitPerUse) notes.push(`건당 최대 ${krw(benefit.limitPerUse)}원까지 적용`)

  return {
    id: benefit.id,
    icon: style.icon,
    tint: style.tint,
    title,
    rate,
    desc: benefit.desc || title,
    limitText: benefit.limitMonth
      ? `월 ${krw(benefit.limitMonth)}원`
      : benefit.limitPerUse
        ? `건당 ${krw(benefit.limitPerUse)}원`
        : '한도 없음',
    conditionText: benefit.condition ? `전월 ${moneyShort(benefit.condition)}` : '실적 무관',
    notes,
  }
}
