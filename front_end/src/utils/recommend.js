// 카드 추천 목록을 화면에 맞게 고르고 정렬합니다.

import { RECO_CARDS } from '../data/recommend.js'
import { CATEGORY_CARDS } from '../data/categoryRecommend.js'

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
    // 카드 앞면에 크게 넣을 짧은 이름 (긴 상품명은 잘라 씁니다)
    short: card.name.length > 16 ? `${card.name.slice(0, 16)}…` : card.name,
    grad: CATEGORY_GRADIENTS[i % CATEGORY_GRADIENTS.length],
    // 카테고리 추천은 신규 발급 캐시백 정보가 없어 비워 둡니다.
    cashback: null,
  }
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
