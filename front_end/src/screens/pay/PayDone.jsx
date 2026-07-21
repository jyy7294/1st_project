import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { orderedComparison } from '../../utils/compare.js'
import { hasCategoryCards } from '../../utils/recommend.js'
import { gradientForCard } from '../../data/cards.js'
import { krw } from '../../utils/format.js'
import styles from './PayDone.module.css'

export default function PayDone() {
  const { state, dispatch } = useApp()

  const ranked = orderedComparison(state.result?.comparison)
  const chosen = ranked[state.payIdx] || ranked[0]
  const amount = state.transaction?.payment_amount || 0
  const discount = chosen?.expected_benefit || 0
  const category = state.transaction?.payment_category

  if (!chosen) return null

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.brand}>
        picka
      </div>

      <div className={styles.badge}>
        <div className={styles.badgeGlow} />
        <div className={`${styles.badgeCore} pk-anim-pop`}>✓</div>
      </div>

      <div className={styles.head}>
        <div className={styles.headTitle}>결제 완료</div>
        <div className={styles.headSub}>성공적으로 처리되었습니다.</div>
      </div>

      <div className={styles.panel}>
        <div className={styles.cardRow}>
          <div
            className={styles.swatch}
            style={{ background: gradientForCard(chosen) }}
          />
          <div style={{ flex: 1 }}>
            <div className={styles.cardName}>
              {chosen.card_company} {chosen.card_name}
            </div>
            <div className={styles.cardNumber}>
              •••• •••• •••• {chosen.last_four}
            </div>
          </div>
        </div>

        <div className={styles.row}>
          <span className={styles.rowLabel}>결제 금액</span>
          <span className={styles.rowValue}>{krw(amount)}원</span>
        </div>

        <div className={styles.row}>
          <span className={styles.rowLabel}>✦ 절약 혜택</span>
          <span className={styles.rowGood}>-{krw(discount)}원</span>
        </div>

        <div className={styles.total}>
          <span className={styles.totalLabel}>최종 승인 금액</span>
          <span className={styles.totalValue}>{krw(amount - discount)}원</span>
        </div>
      </div>

      {/* 방금 결제한 업종에 더 좋은 카드가 있으면 추천 순위로 안내합니다. */}
      {hasCategoryCards(category) && (
        <button
          type="button"
          className={styles.recoBanner}
          onClick={() => dispatch({ type: A.START_RECO, category })}
        >
          <span className={styles.recoIcon}>💡</span>
          <span className={styles.recoBody}>
            <span className={styles.recoText}>
              조금 전 이용하신 <span className={styles.recoCat}>{category}</span>에서
              <br />
              혜택을 받을 수 있는 카드가 있어요
            </span>
            <span className={styles.recoMore}>구경하러 가기 ›</span>
          </span>
        </button>
      )}

      <button
        type="button"
        className={styles.homeBtn}
        onClick={() => dispatch({ type: A.RESET_PAY })}
      >
        홈으로
      </button>
    </div>
  )
}
