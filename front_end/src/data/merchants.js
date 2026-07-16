// 가상 QR 안에 담기는 "결제정보 데이터".
// 실제 서비스라면 POS가 만들어 QR에 넣지만, 여기서는 프론트 상수로 시뮬레이션합니다.
// payment_category 값은 백엔드 카드 혜택의 카테고리명과 정확히 일치해야 혜택이 계산됩니다.
export const MERCHANTS = [
  {
    id: 'starbucks',
    merchant_name: '스타벅스 강남점',
    payment_category: '카페/디저트',
    payment_amount: 5000,
    emoji: '☕',
  },
  {
    id: 'emart',
    merchant_name: '이마트 성수점',
    payment_category: '마트/쇼핑',
    payment_amount: 45000,
    emoji: '🛒',
  },
  {
    id: 'baemin',
    merchant_name: '배달의민족',
    payment_category: '배달앱',
    payment_amount: 22000,
    emoji: '🛵',
  },
  {
    id: 'gs25',
    merchant_name: 'GS25 편의점',
    payment_category: '편의점',
    payment_amount: 3500,
    emoji: '🏪',
  },
  {
    id: 'kyobo',
    merchant_name: '교보문고 문구',
    payment_category: '문구',
    payment_amount: 18000,
    emoji: '✏️',
  },
]
