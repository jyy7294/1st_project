import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { orderedComparison } from '../../utils/compare.js'
import { gradientForCard } from '../../data/cards.js'
import { krw } from '../../utils/format.js'
import ServiceNotice from './ServiceNotice.jsx'
import shared from './payShared.module.css'
import styles from './PayConfirm.module.css'

export default function PayConfirm() {
  const { state, dispatch } = useApp()
  const { transaction, result, payIdx, payStep } = state

  const ranked = orderedComparison(result?.comparison)
  const chosen = ranked[payIdx] || ranked[0]
  const amount = transaction?.payment_amount || 0
  const discount = chosen?.expected_benefit || 0

  // faceid 단계에서는 이 화면이 배경으로만 깔립니다. 버튼을 못 누르게 막습니다.
  const asBackdrop = payStep === 'faceid'

  if (!chosen) return null

  return (
    <div
      className={`${shared.screen} pk-screen`}
      style={asBackdrop ? { pointerEvents: 'none' } : undefined}
    >
      <div className={shared.brandRow} style={{ justifyContent: 'space-between' }}>
        <span>picka</span>
        <span
          style={{
            fontSize: 11,
            fontWeight: 400,
            color: 'rgba(255,255,255,.5)',
            background: 'rgba(255,255,255,.08)',
            padding: '4px 10px',
            borderRadius: 8,
          }}
        >
          결제 확인
        </span>
      </div>

      <div className={styles.shieldWrap}>
        <div className={styles.shield}>
          <div className={styles.shieldRing} />
          <div className={`${styles.shieldGlow} pk-anim-ring`} />
          <div className={styles.shieldCore}>🛡️</div>
        </div>
        <div>
          <div className={styles.shieldTitle}>안전한 결제 환경</div>
          <div className={styles.shieldSub}>실시간 보안 프로토콜 활성화됨</div>
        </div>
      </div>

      <div className={styles.panelWrap}>
        <div className={shared.panel}>
          <div className={styles.cardRow}>
            <div
              className={styles.swatch}
              style={{ background: gradientForCard(chosen) }}
            />
            <div style={{ flex: 1 }}>
              <div className={styles.cardLabel}>선택된 카드</div>
              <div className={styles.cardName}>
                {chosen.card_company} {chosen.card_name}
              </div>
            </div>
            <span className={styles.check}>✓</span>
          </div>

          <div className={`${shared.rowBetween} ${styles.line}`}>
            <span className={shared.muted}>결제 금액</span>
            <span className={styles.lineValue}>{krw(amount)}원</span>
          </div>

          <div className={`${shared.rowBetween} ${styles.line}`}>
            <span className={shared.muted}>할인 혜택</span>
            <span className={styles.lineGood}>-{krw(discount)}원</span>
          </div>

          <div className={styles.total}>
            <span className={styles.totalLabel}>최종 결제 금액</span>
            <span className={styles.totalValue}>
              {krw(amount - discount)}
              <span className={styles.totalUnit}>원</span>
            </span>
          </div>

          <div className={styles.reason}>
            <span style={{ fontSize: 13 }}>✦</span>
            <span className={styles.reasonText}>{chosen.reason}</span>
          </div>
        </div>
      </div>

      <div className={styles.actions}>
        <button
          type="button"
          className={shared.primaryBtn}
          disabled={asBackdrop}
          onClick={() => dispatch({ type: A.SET_PAY_STEP, payStep: 'faceid' })}
        >
          결제하기
        </button>
        <button
          type="button"
          className={shared.ghostBtn}
          disabled={asBackdrop}
          onClick={() => dispatch({ type: A.SET_PAY_STEP, payStep: 'recommend' })}
        >
          다른 카드 선택
        </button>

        <ServiceNotice />
      </div>
    </div>
  )
}
