// 가상 QR 안에 담기는 "결제정보 데이터".
// 실제 서비스라면 POS가 만들어 QR에 넣지만, 여기서는 프론트 상수로 시뮬레이션합니다.
//
// payment_category 는 결제정보 수신 화면 표시용 + 아래 페르소나 매칭용입니다.
// 혜택 계산에 쓰는 업종은 백엔드가 가맹점명(merchant_name)으로 판정합니다(merchant_aliases).
// 아래 이름은 모두 백엔드가 그 업종으로 정확히 판정하는 걸 확인해 둔 값이라,
// 화면 표기와 실제 혜택 계산 결과가 어긋나지 않습니다.
//
// QR 결제는 '오프라인 대면 결제'이므로, 앱·온라인·자동납부로만 결제하는 업종
// (통신요금·온라인쇼핑·배달앱·여행예약 등)은 여기 결제처에서 제외합니다.
export const MERCHANTS = [
  { id: 'starbucks', merchant_name: '스타벅스 강남점', payment_category: '카페/디저트', payment_amount: 5500, emoji: '☕' },
  { id: 'emart', merchant_name: '이마트 성수점', payment_category: '마트/쇼핑', payment_amount: 48000, emoji: '🛒' },
  { id: 'gs25', merchant_name: 'GS25 편의점', payment_category: '편의점', payment_amount: 4200, emoji: '🏪' },
  { id: 'cgv', merchant_name: 'CGV 강남점', payment_category: '영화/문화', payment_amount: 15000, emoji: '🎬' },
  { id: 'korail', merchant_name: '코레일 KTX', payment_category: '교통', payment_amount: 47000, emoji: '🚄' },
  { id: 'pharmacy', merchant_name: '온누리약국 강남점', payment_category: '병원/약국', payment_amount: 12000, emoji: '💊' },
  { id: 'pagoda', merchant_name: '파고다어학원', payment_category: '교육/육아', payment_amount: 180000, emoji: '📚' },
  { id: 'oliveyoung', merchant_name: '올리브영 강남', payment_category: '뷰티/피트니스', payment_amount: 32000, emoji: '💄' },
  { id: 'hyundai', merchant_name: '현대백화점 판교', payment_category: '백화점', payment_amount: 150000, emoji: '🛍️' },
]

// 직전에 뽑힌 결제처. 결제를 하든 안 하든(취소 후 재진입 포함) 매번 새 세션으로 보고
// 이 값을 제외해, 같은 가맹점이 연속으로 나오지 않게 합니다. (세션 동안만 기억)
let lastMerchantId = null

/**
 * 보유 카드(페르소나)의 혜택 업종에 맞는 결제처를 우선 고릅니다.
 *
 * 어떤 페르소나로 결제해도 그 사람 카드에 혜택이 걸리도록,
 * 보유 카드 혜택 업종과 겹치는 결제처만 후보로 두고 그중 하나를 무작위로 고릅니다.
 * (카드 혜택 데이터가 없거나 겹치는 업종이 없으면 전체에서 무작위로 고릅니다.)
 * 직전에 뽑힌 결제처는 제외해, 결제 취소 후 다시 들어와도 같은 곳이 연속으로 안 나옵니다.
 *
 * @param {Array} cards 보유 카드 (각 카드에 benefits[].category 가 있음)
 */
export function pickMerchantForCards(cards = []) {
  const ownedCategories = new Set()
  for (const card of cards) {
    for (const benefit of card.benefits || []) {
      if (benefit.category) ownedCategories.add(benefit.category)
    }
  }
  const matching = MERCHANTS.filter((m) => ownedCategories.has(m.payment_category))
  const base = matching.length > 0 ? matching : MERCHANTS
  // 직전 가맹점 제외 (후보가 2곳 이상일 때만 — 1곳뿐이면 그대로 씀)
  const pool = base.length > 1 ? base.filter((m) => m.id !== lastMerchantId) : base
  const picked = pool[Math.floor(Math.random() * pool.length)]
  lastMerchantId = picked.id
  return picked
}
