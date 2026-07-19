import { useEffect } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import shared from './payShared.module.css'
import styles from './PayReceived.module.css'

const HOLD_MS = 1900

export default function PayReceived() {
  const { state, dispatch } = useApp()
  const tx = state.transaction

  // 거래정보를 잠깐 보여준 뒤 분석 화면으로 넘깁니다.
  useEffect(() => {
    const timer = setTimeout(
      () => dispatch({ type: A.SET_PAY_STEP, payStep: 'analyzing' }),
      HOLD_MS,
    )
    return () => clearTimeout(timer)
  }, [dispatch])

  if (!tx) return null

  return (
    <div className={`${shared.screen} pk-screen`}>
      <div className={shared.brandRow}>picka</div>

      <div className={styles.title}>거래 정보를 확인했습니다.</div>
      <div className={styles.sub}>결제 내용을 확인하고 잠시만 기다려주세요.</div>

      <div className={styles.panelWrap}>
        <div className={shared.panel}>
          <div className={styles.meta}>
            <span>MERCHANT</span>
            <span>ID · 482910</span>
          </div>

          <div className={styles.merchant}>
            <div className={styles.merchantIcon}>{tx.emoji}</div>
            <div>
              <div className={styles.merchantName}>{tx.merchant_name}</div>
              <div className={styles.merchantLoc}>Seoul, Republic of Korea</div>
            </div>
          </div>

          <div className={`${shared.rowBetween} ${styles.line}`}>
            <span className={shared.muted}>업종</span>
            <span className={styles.lineValue}>{tx.payment_category}</span>
          </div>

          <div className={`${shared.rowBetween} ${styles.line}`}>
            <span className={shared.muted}>결제 금액</span>
            <span className={styles.amount}>
              {tx.payment_amount.toLocaleString('ko-KR')}
              <span className={styles.amountUnit}>원</span>
            </span>
          </div>
        </div>
      </div>

      <div className={styles.loadingWrap}>
        <div className={styles.spinner} />
        <div className={styles.loadingText}>결제 정보를 불러오는 중…</div>
      </div>
    </div>
  )
}
