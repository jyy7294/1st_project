// 소비패턴 분석 카드 추천 데이터.
// 디자인 원본(Picka Wallet.dc.html)의 personaReco() 값을 그대로 옮겼습니다.
// url·id 는 원본 HTML 값이 실제와 다른 카드를 가리켜,
// backend/card_database.json(카드고릴라 스냅샷)에서 카드명으로 조회해 교정했습니다.

export const RECO_CARDS = {
  credit: [
    {
      id: "2632",
      name: "디지로카 London",
      short: "DiGi·LOCA London",
      issuer: "LOTTE CARD",
      grad: "linear-gradient(150deg,#1a1a2e,#16213e)",
      total: 1245722,
      benefit: 425722,
      fee: 20000,
      cashback: 840000,
      url: "https://www.card-gorilla.com/card/detail/2632",
    },
    {
      id: "2835",
      name: "신한카드 Discount Plan+",
      short: "DISCOUNT PLAN+",
      issuer: "ShinhanCard",
      grad: "linear-gradient(150deg,#2F6BFF,#0a2a8f)",
      total: 1217159,
      benefit: 417159,
      fee: 50000,
      cashback: 850000,
      url: "https://www.card-gorilla.com/card/detail/2835",
    },
    {
      id: "51",
      name: "삼성카드 taptap O",
      short: "taptap O",
      issuer: "SAMSUNG",
      grad: "linear-gradient(150deg,#19D3C5,#0DAFA8)",
      total: 1175674,
      benefit: 375674,
      fee: 50000,
      cashback: 850000,
      url: "https://www.card-gorilla.com/card/detail/51",
    },
    {
      id: "134",
      name: "KB국민 탄탄대로 온리유",
      short: "탄탄대로 온리유",
      issuer: "KB CARD",
      grad: "linear-gradient(150deg,#5a4a2a,#8a7332)",
      total: 1098220,
      benefit: 328220,
      fee: 30000,
      cashback: 800000,
      url: "https://www.card-gorilla.com/card/detail/134",
    },
  ],
  check: [
    {
      id: "2269",
      name: "토스뱅크 체크카드",
      short: "toss",
      issuer: "TossBank",
      grad: "linear-gradient(150deg,#3182f6,#1b64da)",
      total: 384500,
      benefit: 384500,
      fee: 0,
      cashback: 120000,
      url: "https://www.card-gorilla.com/card/detail/2269",
    },
    {
      id: "435",
      name: "카카오뱅크 프렌즈 체크카드",
      short: "kakaobank",
      issuer: "kakaobank",
      grad: "linear-gradient(150deg,#ffd83d,#f2b705)",
      total: 352000,
      benefit: 352000,
      fee: 0,
      cashback: 100000,
      url: "https://www.card-gorilla.com/card/detail/435",
    },
    {
      id: "2422",
      name: "KB국민 노리2 체크카드",
      short: "NORI 2",
      issuer: "KB CARD",
      grad: "linear-gradient(150deg,#6b5b95,#4a3f6b)",
      total: 318700,
      benefit: 318700,
      fee: 0,
      cashback: 90000,
      url: "https://www.card-gorilla.com/card/detail/2422",
    },
  ],
}

/** 현재 받고 있는 연간 혜택(원). 비교 기준값입니다. */
export const CURRENT_YEAR_BENEFIT = 73232

/**
 * 카드 혜택을 카테고리별로 나눠 보여줄 때 쓰는 비율.
 * 실제 카테고리 집계 API 가 없어 총 혜택을 이 비율로 배분합니다.
 */
export const RECO_CATEGORY_SPLIT = [
  { icon: '🏠', tint: '#FDEAEA', name: '생활', fraction: 0.31 },
  { icon: '🛍️', tint: '#FDE9EC', name: '쇼핑', fraction: 0.25 },
  { icon: '🍽️', tint: '#E6F0FF', name: '음식점', fraction: 0.155 },
  { icon: '🧾', tint: '#eef1f6', name: '공과금', fraction: 0.085 },
  { icon: '🚗', tint: '#E6F0FF', name: '이동', fraction: 0.08 },
  { icon: '🛵', tint: '#EFEBFF', name: '배달앱', fraction: 0.038 },
  { icon: '☕', tint: '#FBF0DD', name: '카페', fraction: 0.025 },
  { icon: '🎫', tint: '#E6FAF7', name: '멤버십', fraction: 0.011 },
  { icon: '🏋️', tint: '#E6F0FF', name: '피트니스', fraction: 0.011 },
  { icon: '🏪', tint: '#EFEBFF', name: '편의점', fraction: 0 },
  { icon: '📺', tint: '#E6FAF7', name: '디지털구독', fraction: 0 },
]

/** 서비스 안내 및 유의사항 */
export const RECO_NOTICE = ["'카드 혜택 시뮬레이션'은 고객님의 신용카드 사용 내역을 분석하고, 사용 내역에 맞는 신용카드를 추천해 주는 서비스입니다.", "본 서비스는 고객님이 마이데이터 서비스에 연결하고, 정보 제공에 동의한 신용카드의 최근 1년간 결제 내역을 바탕으로 최적의 카드를 제안합니다.", "추천 카드는 당사가 모집업무 제휴 계약을 체결한 신용카드사의 상품으로 제한됩니다.", "본 서비스는 현재 시범 운영 중이며 회사는 본 서비스에 따른 분석 내용 및 결과의 정확성을 보장하지 않습니다. 분석 내용 및 결과에 대하여 고객님의 최종 확인이 필요합니다.", "전년 실적은 최근 1년간 카드 사용 내역을 기준으로 계산됩니다. 데이터 조회 범위에 따라 실제 값과 다를 수 있습니다.", "상환능력에 비해 신용카드 사용액이 과도할 경우 신용점수가 하락할 수 있으며, 신용점수 하락 시 금융거래 관련 불이익이 발생할 수 있습니다.", "계약 체결 전 상품설명서와 약관을 확인하시기 바랍니다.", "본 서비스는 회사의 사정에 따라 사전 고지 없이 변경 또는 종료될 수 있습니다."]

/** 결제 서비스 이용 안내 */
export const PAY_NOTICE = ["(주)PICKA는 「전자금융거래법」에 따라 등록된 전자지급결제대행(PG) 서비스로, 고객과 가맹점 사이의 결제 처리 및 정산을 대행합니다.", "카드 추천은 고객의 소비 내역을 분석해 정보를 제공하는 서비스이며, PICKA는 카드 발급·심사·계약의 당사자가 아닙니다. 카드 발급 및 심사는 각 카드사의 기준에 따라 진행됩니다.", "결제·정산 내역, 취소 및 환불은 가맹점의 정책과 카드사 승인 결과에 따르며, 관련 문의는 PICKA 고객센터 또는 해당 가맹점으로 접수해 주세요.", "고객의 결제·개인정보는 관련 법령 및 PICKA 개인정보처리방침에 따라 안전하게 보호·관리됩니다.", "상환능력에 비해 신용카드 사용액이 과도할 경우 신용점수가 하락할 수 있으며, 계획적인 소비를 권장합니다."]

export const NOTICE_CONTACT = ["PICKA 고객센터 : help@picka.co.kr", "전자금융업 등록번호 2026-서울-0018"]
