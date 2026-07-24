// 카드 추천 목록을 화면에 맞게 고르고 정렬합니다.

import { RECO_CARDS } from '../data/recommend.js'
import { CATEGORY_CARDS } from '../data/categoryRecommend.js'
import { cardImage } from '../data/cardImages.js'
import { krw, normalizeBenefitRate } from './format.js'

/**
 * 이미 보유한 카드는 추천에서 뺍니다.
 * 카드명이 서로 포함 관계면 같은 상품으로 봅니다 (원본 HTML과 같은 기준).
 */
function isOwned(card, myCards) {
  return myCards.some((mine) => {
    const name = mine.card_name || ''
    return name && (card.name.includes(name) || (card.short || '').includes(name))
  })
}

/** 카테고리 추천 카드에는 색·표기 정보가 없어 여기서 채워 줍니다. */
const CATEGORY_GRADIENTS = [
  'linear-gradient(150deg,#1a1a2e,#16213e)',
  'linear-gradient(150deg,#2F6BFF,#0a2a8f)',
  'linear-gradient(150deg,#19D3C5,#0DAFA8)',
]

/** DB 추천 카드를 화면이 쓰는 모양으로 맞춥니다. */
function adaptCategoryCard(card, i) {
  return {
    ...card,
    // 실물 카드 이미지 (없으면 그라데이션으로 대체)
    image: cardImage({ card_id: card.id }),
    // 카드 앞면에 크게 넣을 짧은 이름 (긴 상품명은 잘라 씁니다)
    short: card.name.length > 16 ? `${card.name.slice(0, 16)}…` : card.name,
    grad: CATEGORY_GRADIENTS[i % CATEGORY_GRADIENTS.length],
    // 카테고리 추천은 신규 발급 캐시백 정보가 없어 비워 둡니다.
    cashback: null,
  }
}

/**
 * 혜택 문구. 단위를 보고 만들기 때문에 정액 혜택에 %가 붙지 않습니다.
 *
 * 백엔드가 rate 한 값에 정률(%)과 정액(원)을 섞어 담아서, 거기에 무조건 '%'를
 * 붙이면 '1000원 할인'이 '1000% 할인'으로 나옵니다. 그래서 benefits[] 에서
 * 대표 혜택을 찾아 value/unit 으로 문구를 만듭니다.
 *
 * @param {{value:number, unit:string, name:string}|null} benefit 대표 혜택
 * @param {object} card 추천 카드 (구버전 응답 대비 fallback 용)
 */
export function benefitText(benefit, card = {}) {
  const rawValue = benefit?.value ?? null
  // 정률(%)에 100 초과 값이 오면 정액(원)으로 정상화 (예: 1000% → 1,000원 할인)
  const { value, unit } = normalizeBenefitRate(rawValue, benefit?.unit ?? null)

  if (value !== null) {
    if (unit === '%') return `${value}% 할인`
    if (unit === '원' || unit === 'KRW') return `${krw(value)}원 할인`
  }

  // 단위를 모르면 혜택 이름을 그대로 씁니다 (적립·면제 등).
  if (benefit?.name || card.benefitName) return benefit?.name || card.benefitName

  // 구버전 응답: rate 만 있을 때. 100 이하일 때만 퍼센트로 봅니다.
  if (card.rate > 0 && card.rate <= 100) return `${card.rate}% 할인`
  return '혜택 있음'
}

/** 카드의 대표 혜택(benefitName 과 같은 항목)을 benefits[] 에서 찾습니다. */
export function findMainBenefit(card) {
  const list = Array.isArray(card?.benefits) ? card.benefits : []
  return list.find((b) => b.name === card.benefitName) || null
}

/**
 * 백엔드 소비패턴 추천 카드(card-recommendations 응답) → 화면 모양.
 *
 * total 은 연회비를 뺀 순혜택이라, '혜택'(연회비 전)은 total+fee 로 되돌립니다.
 * 이미지가 응답에 없으면 우리 카드 이미지 맵으로 대체합니다.
 */
export function adaptApiRecoCard(card, i = 0) {
  return {
    id: card.id,
    name: card.name,
    issuer: card.issuer,
    benefitName: card.benefitName,
    rate: card.rate,
    total: card.total,
    fee: card.fee,
    // 총 혜택(연회비 차감 전) = 순혜택 + 연회비
    benefit: (card.total || 0) + (card.fee || 0),
    url: card.url || null,
    image: card.image_url || cardImage({ card_id: card.id }),
    short: card.name.length > 16 ? `${card.name.slice(0, 16)}…` : card.name,
    grad: CATEGORY_GRADIENTS[i % CATEGORY_GRADIENTS.length],
    cashback: null,
    // 혜택 목록 (value/unit 이 있어 문구를 정확히 만들 수 있습니다)
    benefits: Array.isArray(card.benefits) ? card.benefits : [],
    // 소비패턴 추천에만 있는 값 (분석 결과 화면에서 씀)
    benefitCategory: card.benefitCategory || null,
    monthlySpend: card.monthlySpend || 0,
    recommendationMessage: card.recommendationMessage || '',
    matchedMerchants: card.matchedMerchants || [],
  }
}

/**
 * 지금 추천 화면이 보여줄 카드 목록.
 *
 * 결제 업종 기반(recoCategory 있음)은 정적 스냅샷을, 소비패턴 기반(광고 배너)은
 * 백엔드에서 받아 state.recoCards 에 담아 둔 목록을 씁니다.
 */
export function selectRecoList(state) {
  if (state.recoCategory) {
    return rankedRecommendations(state.recoType, state.cards, state.recoCategory)
  }
  return state.recoCards?.[state.recoType] || []
}

/** 현재 선택된(또는 1위) 추천 카드. */
export function selectRecoCard(state) {
  const list = selectRecoList(state)
  return list.find((card) => card.id === state.recoSelId) || list[0] || null
}

/**
 * 탭(신용/체크)에 해당하는 추천 카드를 혜택 많은 순으로 돌려줍니다.
 *
 * category 가 있으면 그 업종에서 할인이 큰 카드를 DB 스냅샷에서 뽑고,
 * 없으면 소비패턴 기반 기본 추천을 씁니다.
 *
 * @param {'credit'|'check'} type
 * @param {Array} myCards 보유 카드 (제외 대상)
 * @param {string|null} category 결제 업종
 */
export function rankedRecommendations(type, myCards = [], category = null) {
  const byCategory = category && CATEGORY_CARDS[category]?.[type]
  if (byCategory?.length) {
    return byCategory
      .filter((card) => !isOwned(card, myCards))
      .map(adaptCategoryCard)
  }

  return (RECO_CARDS[type] || [])
    .filter((card) => !isOwned(card, myCards))
    .slice()
    .sort((a, b) => b.total - a.total)
}

/** 이 업종에 대한 추천 데이터가 있는지. */
export function hasCategoryCards(category) {
  const set = category && CATEGORY_CARDS[category]
  return Boolean(set && (set.credit?.length || set.check?.length))
}

/** id 로 추천 카드를 찾습니다. 없으면 그 탭의 1위를 돌려줍니다. */
export function findRecommendation(type, id, myCards = [], category = null) {
  const list = rankedRecommendations(type, myCards, category)
  return list.find((card) => card.id === id) || list[0] || null
}
