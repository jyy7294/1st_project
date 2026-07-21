// 혜택 원본 데이터(data/benefits.js)를 화면에 쓸 문자열·아이콘으로 바꿉니다.
// 카드 상세와 전체 혜택 화면이 같은 표기를 쓰도록 이 파일 하나만 씁니다.

import { krw } from './format.js'

// 카테고리별 아이콘과 배경 틴트. 없는 카테고리는 기본값을 씁니다.
const STYLE_BY_CATEGORY = {
  '공과금/생활요금': { icon: '🧾', tint: '#e6f0ff' },
  교통: { icon: '🚇', tint: '#e6f0ff' },
  '구독/멤버십': { icon: '🎬', tint: '#eef0ff' },
  '마트/쇼핑': { icon: '🛒', tint: '#fef3e2' },
  모든가맹점: { icon: '💳', tint: '#f4f6fa' },
  배달앱: { icon: '🛵', tint: '#fdeee2' },
  '병원/약국': { icon: '🏥', tint: '#e6faf7' },
  생활: { icon: '🏠', tint: '#e6faf7' },
  주유: { icon: '⛽', tint: '#fef3e2' },
  '카페/디저트': { icon: '☕', tint: '#fdeee2' },
  편의점: { icon: '🏪', tint: '#fef3e2' },
  '푸드/외식': { icon: '🍽️', tint: '#fdeee2' },
}

const DEFAULT_STYLE = { icon: '✦', tint: '#f4f6fa' }

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
  const rate = `${benefit.value}${benefit.unit || ''}`
  const where = benefit.detail || benefit.category

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
    title: `${where} ${rate} ${benefit.type}`,
    rate,
    desc: benefit.desc || `${where} ${benefit.type}`,
    limitText: benefit.limitMonth
      ? `월 ${krw(benefit.limitMonth)}원`
      : benefit.limitPerUse
        ? `건당 ${krw(benefit.limitPerUse)}원`
        : '한도 없음',
    conditionText: benefit.condition ? `전월 ${moneyShort(benefit.condition)}` : '실적 무관',
    notes,
  }
}
