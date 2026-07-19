// 지갑에 표시할 사용자 보유 카드 (프론트 목업).
// 백엔드에 보유카드 조회 API가 아직 없어서 프론트 상수로 시뮬레이션합니다.
// card_id / card_company / card_name / last_four / nickname 은
// backend/user_cards.py 의 USER_CARD_IDS(13, 2262, 2261)와 값이 일치해야
// 홈 화면 카드와 결제 추천 결과가 같은 카드로 보입니다.

// 카드사별 그라데이션. 실제 카드사 카드 이미지는 저작권 문제로 쓰지 않고
// 브랜드 컬러 기반 오리지널 디자인을 씁니다.
const GRADIENTS = {
  신한카드: 'linear-gradient(140deg,#2F6BFF,#1846D8)',
  롯데카드: 'linear-gradient(140deg,#19D3C5,#0DAFA8)',
  현대카드: 'linear-gradient(140deg,#10275F,#071844)',
  삼성카드: 'linear-gradient(140deg,#3a3f4a,#1c1f26)',
  KB국민카드: 'linear-gradient(140deg,#5A5A5A,#2e2e2e)',
}

const DEFAULT_GRADIENT = 'linear-gradient(140deg,#10275F,#071844)'

// 같은 카드사에 카드가 둘 이상이면 색이 겹치므로 card_id 로 색을 고정합니다.
// 지갑 화면의 현재 모습이 기준입니다 — 13 파랑, 2262 청록, 2261 네이비.
const CARD_GRADIENTS = {
  13: GRADIENTS['신한카드'],
  2262: GRADIENTS['롯데카드'],
  2261: DEFAULT_GRADIENT,
}

/**
 * 카드 앞면 그라데이션. card_id 우선, 없으면 카드사, 그것도 없으면 기본 네이비.
 * 지갑·QR·결제 화면이 같은 카드에 같은 색을 쓰도록 이 함수 하나만 씁니다.
 *
 * @param {{card_id?: number|string, card_company?: string}} card
 */
export function gradientForCard(card) {
  if (!card) return DEFAULT_GRADIENT
  return CARD_GRADIENTS[card.card_id] || GRADIENTS[card.card_company] || DEFAULT_GRADIENT
}

export const WALLET_CARDS = [
  {
    card_id: 13,
    card_company: '신한카드',
    card_name: '신한카드 Mr.Life',
    last_four: '1234',
    nickname: '생활비 카드',
    spent: '318,000',
    benefit: '22,400',
    expiry: '12/27',
  },
  {
    card_id: 2262,
    card_company: '롯데카드',
    card_name: 'LOCA LIKIT Eat',
    last_four: '5678',
    nickname: '카페·외식 카드',
    spent: '506,000',
    benefit: '31,200',
    expiry: '03/28',
  },
  {
    card_id: 2261,
    card_company: '롯데카드',
    card_name: 'LOCA LIKIT 1.2',
    last_four: '9012',
    nickname: '기본 할인 카드',
    spent: '152,000',
    benefit: '9,800',
    expiry: '09/26',
  },
]
