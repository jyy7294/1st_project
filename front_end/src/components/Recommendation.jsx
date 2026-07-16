import { useState } from 'react'
import { won } from '../utils/format.js'
import styles from './Recommendation.module.css'

// 추천 결과 화면. 추천 카드가 기본 표시되고, 2·3위 카드를 누르면 그 카드로 전환됨.
export default function Recommendation({ result, error, onRetry, onReset }) {
  const [selectedId, setSelectedId] = useState(null)
  const [showOthers, setShowOthers] = useState(false)

  // 에러 / 추천 불가 상태
  if (error || !result || !result.recommended_card) {
    return (
      <div className={styles.errorWrap}>
        <div className={styles.errorIcon}>😢</div>
        <h1 className={styles.errorTitle}>
          {error || '추천 가능한 카드가 없습니다.'}
        </h1>
        <div className={styles.actions}>
          <button type="button" className={styles.ghostBtn} onClick={onReset}>
            처음으로
          </button>
          {error && (
            <button type="button" className={styles.primaryBtn} onClick={onRetry}>
              다시 시도
            </button>
          )}
        </div>
      </div>
    )
  }

  const { recommended_card, comparison, transaction, saving_message } = result

  // 현재 화면에 표시할 카드 (기본: 추천 카드, 다른 카드 선택 시 그 카드)
  const displayed =
    comparison.find((card) => card.card_id === selectedId) || recommended_card
  const isRecommended = displayed.card_id === recommended_card.card_id

  // 목록에는 현재 표시 중인 카드를 제외한 나머지
  const others = comparison.filter((card) => card.card_id !== displayed.card_id)

  return (
    <div>
      <div className={styles.txnBar}>
        <span>{transaction.merchant_name}</span>
        <strong>{won(transaction.amount)}</strong>
      </div>

      <p className={`${styles.badge} ${isRecommended ? '' : styles.badgeAlt}`}>
        {isRecommended ? 'AI 추천 카드' : `선택한 카드 · ${displayed.rank}위`}
      </p>

      {/* 표시 카드 하이라이트 */}
      <div className={`${styles.heroCard} ${isRecommended ? styles.heroCardHi : ''}`}>
        <CreditCard card={displayed} />

        <div className={styles.heroBody}>
          <p className={styles.company}>{displayed.card_company}</p>
          <h2 className={styles.cardName}>{displayed.card_name}</h2>

          <div className={styles.benefitBox}>
            <span className={styles.benefitLabel}>예상 혜택</span>
            <span className={styles.benefitValue}>
              {won(displayed.expected_benefit)}
            </span>
          </div>

          <p className={styles.reason}>{displayed.reason}</p>

          {displayed.reason_details?.length > 0 && (
            <ul className={styles.reasonList}>
              {displayed.reason_details.map((detail, index) => (
                <li key={index}>{detail}</li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {isRecommended && saving_message && (
        <p className={styles.saving}>💡 {saving_message}</p>
      )}

      {/* 다른 카드 보기 (클릭하면 그 카드로 전환) */}
      {others.length > 0 && (
        <div className={styles.othersSection}>
          <button
            type="button"
            className={styles.toggle}
            onClick={() => setShowOthers((prev) => !prev)}
          >
            {showOthers
              ? '다른 카드 접기 ▲'
              : `다른 카드 보기 (${others.length}) ▼`}
          </button>

          {showOthers && (
            <ul className={styles.otherList}>
              {others.map((card) => (
                <li key={card.card_id}>
                  <button
                    type="button"
                    className={styles.otherItem}
                    onClick={() => setSelectedId(card.card_id)}
                  >
                    <div className={styles.otherRank}>{card.rank}위</div>
                    <div className={styles.otherInfo}>
                      <span className={styles.otherName}>
                        {card.card_name}
                        {card.card_id === recommended_card.card_id && (
                          <span className={styles.recoTag}>추천</span>
                        )}
                      </span>
                      <span className={styles.otherReason}>
                        {card.ranking_reason}
                      </span>
                    </div>
                    <div className={styles.otherBenefit}>
                      {won(card.expected_benefit)}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <button type="button" className={styles.resetBtn} onClick={onReset}>
        처음으로
      </button>
    </div>
  )
}

// 실제 신용카드처럼 보이는 카드 프레임.
// 카드 이미지가 로드되면 프레임에 채우고, 실패/없으면 디자인된 카드로 대체.
function CreditCard({ card }) {
  const [broken, setBroken] = useState(false)
  const showImage = card.card_image && !broken
  const maskedNumber = card.last_four
    ? `•••• •••• •••• ${card.last_four}`
    : '•••• •••• •••• ••••'

  return (
    <div className={styles.cardStage}>
      <div className={styles.card}>
        {showImage ? (
          <img
            className={styles.cardImage}
            src={card.card_image}
            alt={card.card_name}
            onError={() => setBroken(true)}
          />
        ) : (
          <div className={styles.cardFallback}>
            <div className={styles.cardTop}>
              <span className={styles.cardCompany}>{card.card_company}</span>
              <span className={styles.cardBrand}>PICKA</span>
            </div>
            <div className={styles.cardChip} />
            <div className={styles.cardBottom}>
              <span className={styles.cardNumber}>{maskedNumber}</span>
              <span className={styles.cardNickname}>
                {card.nickname || card.card_name}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
