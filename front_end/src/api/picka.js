// PICKA 백엔드 API.
//
// 엔드포인트는 picka-backend/app/main.py 기준입니다.
// 인증은 JWT(Authorization: Bearer) 로 처리하며(client.js), user_id 는 사용자별
// 리소스 경로(/users/{user_id}/...)를 가리키는 용도로 함께 실립니다.

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
 * 소비패턴 기반 신규 카드 추천 (광고 배너 → 추천 순위 화면).
 *
 * 최근 소비 내역을 분석해 미보유 카드 중 혜택이 큰 순으로 돌려줍니다.
 * @param {number} userId
 * @param {'credit'|'check'} type
 * @param {number} [limit]
 * @returns {Promise<{meta: object, cards: Array}>}
 */
export async function fetchCardRecommendations(userId, type, limit = 3) {
  const data = await request(
    `/api/v1/users/${userId}/card-recommendations?type=${type}&limit=${limit}`,
  )
  return {
    meta: {
      analysisStartDate: data.analysisStartDate,
      analysisEndDate: data.analysisEndDate,
      updateCycle: data.updateCycle,
      topCategory: data.topCategory,
      topCategorySpend: data.topCategorySpend || 0,
      topMerchants: data.topMerchants || [],
    },
    cards: data.cards || [],
  }
}

/**
 * 보유 카드 전체의 결제내역을 모아 옵니다 (소비 성향 집계용).
 *
 * 백엔드에 사용자 단위 거래 목록·빈도 집계 API 가 없어서 카드별로 받아 합칩니다.
 * usage_month 를 안 보내면 월 제한 없이 최신순 전체가 옵니다.
 *
 * @param {number} userId
 * @param {number[]} cardIds 보유 카드 id 목록
 * @param {number} [limit] 카드당 최대 건수 (백엔드 상한 100)
 */
export async function fetchAllTransactions(userId, cardIds, limit = 100) {
  const lists = await Promise.all(
    cardIds.map((cardId) =>
      request(`/api/v1/users/${userId}/cards/${cardId}/transactions?limit=${limit}`)
        .then((data) => data?.transactions || [])
        .catch(() => []),
    ),
  )
  return lists.flat()
}

/**
 * 월별 소비 리포트 (결제수단 관리 → 소비 리포트).
 *
 * 해당 월의 실제 결제내역을 집계해 총지출·전월대비·일별 누적·카테고리별 지출·
 * 카드별 혜택까지 돌려줍니다.
 * @param {number} userId
 * @param {string} month 'YYYY-MM'
 */
export async function fetchSpendingReport(userId, month) {
  return request(`/api/v1/users/${userId}/spending-report?month=${month}`)
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

/*
 * 업종(payment_category)은 일부러 보내지 않습니다.
 *
 * 보내면 백엔드가 그 값을 그대로 쓰고, 안 보내면 merchant_aliases 테이블로
 * 가맹점명을 카드사 기준 업종에 맞춰 줍니다. 카드사 기준은 우리 직관과 달라서
 * (예: 교보문고 → '문구'가 아니라 '영화/문화') 프론트가 정한 이름을 보내면
 * 혜택이 하나도 안 잡힙니다. 업종 판정의 기준은 DB 한 곳에만 둡니다.
 * 백엔드가 판정한 업종은 응답 transaction.category 로 돌아옵니다.
 */

/**
 * 결제정보로 보유카드별 예상 혜택을 계산하고 추천 결과를 받아옵니다.
 * @param {number} userId
 * @param {{merchant_name: string, payment_amount: number}} transaction
 */
export async function fetchRecommendation(userId, transaction) {
  return request('/api/v1/recommendations', {
    method: 'POST',
    body: {
      user_id: userId,
      merchant_name: transaction.merchant_name,
      payment_amount: transaction.payment_amount,
    },
  })
}

/**
 * 결제 확정. 거래를 기록하고 실적·혜택 사용량을 갱신합니다.
 *
 * @param {number} userId
 * @param {number} cardId 결제에 쓸 카드 상품 id
 * @param {{merchant_name: string, payment_amount: number}} transaction
 */
export async function payWithCard(userId, cardId, transaction) {
  return request('/api/v1/transactions', {
    method: 'POST',
    body: {
      user_id: userId,
      card_id: cardId,
      merchant_name: transaction.merchant_name,
      payment_amount: transaction.payment_amount,
    },
  })
}
