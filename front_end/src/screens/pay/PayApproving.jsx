import { useEffect } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { orderedComparison } from '../../utils/compare.js'
import { krw } from '../../utils/format.js'
import styles from './PayApproving.module.css'

const APPROVE_MS = 4000

export default function PayApproving() {
  const { state, dispatch } = useApp()

  // 실제 결제 승인 API가 생기면 이 타이머를 호출로 바꿉니다.
  useEffect(() => {
    const timer = setTimeout(
      () => dispatch({ type: A.SET_PAY_STEP, payStep: 'done' }),
      APPROVE_MS,
    )
    return () => clearTimeout(timer)
  }, [dispatch])

  const ranked = orderedComparison(state.result?.comparison)
  const chosen = ranked[state.payIdx] || ranked[0]
  const amount = state.transaction?.payment_amount || 0
  const final = amount - (chosen?.expected_benefit || 0)

  if (!chosen) return null

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.brand}>picka</div>

      <div className={styles.orb}>
        <div className={styles.ring} />
        <div className={styles.glow} />
        <div className={styles.spin} />
        <div className={styles.core}>🔐</div>
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
          <div className={styles.barFill} />
        </div>
      </div>

      <div className={styles.foot}>
        <span>✦</span>
        AI is verifying transaction safety…
      </div>
    </div>
  )
}
