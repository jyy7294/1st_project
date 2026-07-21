// 카드 추천 목록을 화면에 맞게 고르고 정렬합니다.

import { RECO_CARDS } from '../data/recommend.js'

/**
 * 이미 보유한 카드는 추천에서 뺍니다.
 * 카드명이 서로 포함 관계면 같은 상품으로 봅니다 (원본 HTML과 같은 기준).
 */
function isOwned(card, myCards) {
  return myCards.some((mine) => {
    const name = mine.card_name || ''
    return name && (card.name.includes(name) || card.short.includes(name))
  })
}

/**
 * 탭(신용/체크)에 해당하는 추천 카드를 혜택 많은 순으로 돌려줍니다.
 *
 * @param {'credit'|'check'} type
 * @param {Array} myCards 보유 카드 (제외 대상)
 */
export function rankedRecommendations(type, myCards = []) {
  return (RECO_CARDS[type] || [])
    .filter((card) => !isOwned(card, myCards))
    .slice()
    .sort((a, b) => b.total - a.total)
}

/** id 로 추천 카드를 찾습니다. 없으면 그 탭의 1위를 돌려줍니다. */
export function findRecommendation(type, id, myCards = []) {
  const list = rankedRecommendations(type, myCards)
  return list.find((card) => card.id === id) || list[0] || null
}
