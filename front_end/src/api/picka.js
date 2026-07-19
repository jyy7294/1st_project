import { WALLET_CARDS } from '../data/cards.js'

// PICKA 백엔드(FastAPI) 연동.
// uvicorn 기본 포트(8000)를 가정합니다. 백엔드 포트가 다르면 여기만 바꾸세요.
const API_BASE = 'http://127.0.0.1:8000'

/**
 * 결제정보로 보유카드별 예상 혜택을 계산하고 추천 결과를 받아옵니다.
 * @param {{merchant_name: string, payment_category: string, payment_amount: number}} transaction
 * @returns 백엔드 recommend_cards 결과 (recommended_card, comparison, saving_message ...)
 */
export async function fetchRecommendation(transaction) {
  const response = await fetch(`${API_BASE}/api/v1/recommendations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      merchant_name: transaction.merchant_name,
      payment_category: transaction.payment_category,
      payment_amount: transaction.payment_amount,
    }),
  })

  if (response.status === 404) {
    throw new ApiError('추천 가능한 카드가 없습니다.', 404)
  }

  if (!response.ok) {
    throw new ApiError('추천 결과를 불러오지 못했습니다.', response.status)
  }

  return response.json()
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/**
 * 사용자의 보유카드 목록을 가져옵니다.
 *
 * 지금은 프론트 목업(data/cards.js)을 반환합니다.
 * 백엔드에 GET /api/v1/cards 가 생기면 이 함수 안쪽만 아래처럼 바꾸면 됩니다:
 *
 *   const res = await fetch(`${API_BASE}/api/v1/cards`)
 *   if (!res.ok) throw new ApiError('보유카드를 불러오지 못했습니다.', res.status)
 *   return res.json()
 *
 * @returns {Promise<Array>} 보유카드 배열
 */
export async function fetchMyCards() {
  return WALLET_CARDS
}
