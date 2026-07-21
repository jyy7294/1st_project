// PICKA 백엔드 API.
//
// 엔드포인트는 picka-backend/app/main.py 기준입니다.
// 백엔드에 인증 미들웨어가 없어 토큰 대신 user_id 로 사용자를 식별합니다.

import { ApiError, request } from './client.js'
import { adaptCard, adaptTransaction } from './adapters.js'

export { ApiError }

/**
 * 보유 카드 목록.
 * @param {number} userId
 * @returns {Promise<Array>} 지갑 화면용 카드 배열
 */
export async function fetchMyCards(userId) {
  try {
    const data = await request(`/api/v1/users/${userId}/cards`)
    return (data?.cards || []).map(adaptCard)
  } catch (err) {
    // 등록된 카드가 하나도 없으면 백엔드가 404 를 줍니다. 오류가 아니라 빈 지갑입니다.
    if (err instanceof ApiError && err.status === 404) return []
    throw err
  }
}

/**
 * 카드 한 장의 상세 — 혜택 목록과 최근 결제내역.
 * @param {number} userId
 * @param {number} cardId 카드 상품 id (user_card_id 아님)
 * @param {{limit?: number}} [options] 가져올 결제내역 개수
 */
export async function fetchCardDetail(userId, cardId, { limit = 20 } = {}) {
  const [detail, history] = await Promise.all([
    request(`/api/v1/users/${userId}/cards/${cardId}`),
    // 상세 응답의 recent_transactions 는 5건까지라, 목록 API 로 더 받아옵니다.
    request(`/api/v1/users/${userId}/cards/${cardId}/transactions?limit=${limit}`).catch(() => null),
  ])

  const card = adaptCard(detail?.card || {})
  const rows = history?.transactions || detail?.recent_transactions || []

  return {
    card,
    benefits: card.benefits,
    transactions: rows.map(adaptTransaction),
  }
}

/**
 * 카드 등록. 스캔·직접 입력 모두 같은 본문을 쓰고 경로만 다릅니다.
 *
 * @param {number} userId
 * @param {{number: string, expiry: string, cvc: string, pin: string}} form 화면 입력값
 * @param {'manual'|'scan'} [method]
 */
export async function registerCard(userId, form, method = 'manual') {
  const [month, year] = form.expiry.split('/')
  return request(`/api/v1/users/${userId}/cards/${method}`, {
    method: 'POST',
    body: {
      card_number: form.number.replace(/\D/g, ''),
      expiry_month: Number(month),
      // 화면은 두 자리(YY)로 받고 백엔드는 네 자리를 기대합니다.
      expiry_year: 2000 + Number(year),
      cvc: form.cvc,
      card_password_first2: form.pin,
    },
  })
}

/** 보유 카드 삭제(백엔드에서는 비활성화). */
export async function removeCard(userId, cardId) {
  return request(`/api/v1/users/${userId}/cards/${cardId}`, { method: 'DELETE' })
}

/**
 * 결제정보로 보유카드별 예상 혜택을 계산하고 추천 결과를 받아옵니다.
 * @param {number} userId
 * @param {{merchant_name: string, payment_category: string, payment_amount: number}} transaction
 */
export async function fetchRecommendation(userId, transaction) {
  return request('/api/v1/recommendations', {
    method: 'POST',
    body: {
      user_id: userId,
      merchant_name: transaction.merchant_name,
      payment_category: transaction.payment_category,
      payment_amount: transaction.payment_amount,
    },
  })
}

/**
 * 결제 확정. 거래를 기록하고 실적·혜택 사용량을 갱신합니다.
 *
 * @param {number} userId
 * @param {number} cardId 결제에 쓸 카드 상품 id
 * @param {{merchant_name: string, payment_category: string, payment_amount: number}} transaction
 */
export async function payWithCard(userId, cardId, transaction) {
  return request('/api/v1/transactions', {
    method: 'POST',
    body: {
      user_id: userId,
      card_id: cardId,
      merchant_name: transaction.merchant_name,
      payment_category: transaction.payment_category,
      payment_amount: transaction.payment_amount,
    },
  })
}
