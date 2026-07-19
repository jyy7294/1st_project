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

/** 카드사 이름으로 카드 앞면 그라데이션을 찾습니다. */
export function gradientFor(cardCompany) {
  return GRADIENTS[cardCompany] || DEFAULT_GRADIENT
}

export const WALLET_CARDS = [
  {
    card_id: 13,
    card_company: '신한카드',
    card_name: '신한카드 Mr.Life',
    last_four: '1234',
    nickname: '생활비 카드',
    gradient: GRADIENTS['신한카드'],
  },
  {
    card_id: 2262,
    card_company: '롯데카드',
    card_name: 'LOCA LIKIT Eat',
    last_four: '5678',
    nickname: '카페·외식 카드',
    gradient: GRADIENTS['롯데카드'],
  },
  {
    card_id: 2261,
    card_company: '롯데카드',
    card_name: 'LOCA LIKIT 1.2',
    last_four: '9012',
    nickname: '기본 할인 카드',
    gradient: DEFAULT_GRADIENT,
  },
]
