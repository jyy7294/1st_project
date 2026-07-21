import { useEffect, useRef } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { payWithCard } from '../../api/picka.js'
import { orderedComparison } from '../../utils/compare.js'
import { krw } from '../../utils/format.js'
import styles from './PayApproving.module.css'

const APPROVE_MS = 4000

export default function PayApproving() {
  const { state, dispatch } = useApp()

  const ranked = orderedComparison(state.result?.comparison)
  const chosen = ranked[state.payIdx] || ranked[0]
  // 결제는 한 번만 보냅니다. 화면이 다시 그려져도 중복 승인되지 않습니다.
  const sent = useRef(false)

  // 승인 연출을 보여주는 동안 실제 결제(거래 기록·실적 갱신)를 요청합니다.
  useEffect(() => {
    const userId = state.user?.userId
    const cardId = chosen?.card_id
    if (!sent.current && userId && cardId && state.transaction) {
      sent.current = true
      payWithCard(userId, cardId, state.transaction).catch(() => {
        // 결제 기록에 실패해도 데모 흐름은 완료 화면까지 진행합니다.
      })
    }

    const timer = setTimeout(
      () => dispatch({ type: A.SET_PAY_STEP, payStep: 'done' }),
      APPROVE_MS,
    )
    return () => clearTimeout(timer)
  }, [dispatch, chosen?.card_id, state.user?.userId, state.transaction])
  const amount = state.transaction?.payment_amount || 0
  const final = amount - (chosen?.expected_benefit || 0)

  if (!chosen) return null

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.brand}>
        picka
      </div>

      <div className={styles.orb} role="status" aria-live="polite">
        <div className={styles.ring} />
        <div className={`${styles.glow} pk-anim-ring`} />
        <div className={`${styles.spin} pk-anim-spin pk-reduced-loading`} />
        <div className={`${styles.core} pk-anim-corepulse`}>🔐</div>
      </div>

      <div className={styles.head}>
        <div className={styles.headTitle}>카드 승인 중</div>
        <div className={styles.headSub}>
          은행 서버와 안전하게 연결하여
          <br />
          결제 승인을 요청하고 있습니다.
        </div>
      </div>

      <div className={styles.panel}>
        <div className={styles.row}>
          <span className={styles.rowLabel}>Merchant</span>
          <span className={styles.rowValue}>{state.transaction?.merchant_name}</span>
        </div>
        <div className={styles.row}>
          <span className={styles.rowLabel}>Amount</span>
          <span className={styles.rowValue}>₩{krw(final)}</span>
        </div>
        <div className={styles.barTrack}>
          <div className={`${styles.barFill} pk-anim-grow`} />
        </div>
      </div>

      <div className={styles.foot}>
        <span>✦</span>
        AI is verifying transaction safety…
      </div>
    </div>
  )
}
