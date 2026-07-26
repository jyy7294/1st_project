import { useEffect, useState } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { orderedComparison } from '../../utils/compare.js'
import { krw } from '../../utils/format.js'
import styles from './PayFaceId.module.css'

const OK_AT_MS = 1200 // 인증 성공 표시
const NEXT_AT_MS = 2100 // 승인 화면으로 이동

export default function PayFaceId() {
  const { state, dispatch } = useApp()
  const [ok, setOk] = useState(false)

  useEffect(() => {
    const okTimer = setTimeout(() => setOk(true), OK_AT_MS)
    const nextTimer = setTimeout(
      () => dispatch({ type: A.SET_PAY_STEP, payStep: 'approving' }),
      NEXT_AT_MS,
    )
    return () => {
      clearTimeout(okTimer)
      clearTimeout(nextTimer)
    }
  }, [dispatch])

  const ranked = orderedComparison(state.result?.comparison)
  const chosen = ranked[state.payIdx] || ranked[0]
  const amount = state.transaction?.payment_amount || 0
  const final = amount - (chosen?.expected_benefit || 0)

  if (!chosen) return null

  return (
    <div className={styles.overlay}>
      <div
        className={`${styles.island} ${ok ? `${styles.ok} pk-anim-facepop` : 'pk-anim-islandgrow'}`}
      >
        {ok ? (
          <svg
            className={`${styles.okIcon} pk-anim-pop`}
            width="62" height="62" viewBox="0 0 44 44" fill="none"
            stroke="#34C759" strokeWidth="3.4"
            strokeLinecap="round" strokeLinejoin="round"
          >
            <path d="M34 15 19 31l-8-8" />
          </svg>
        ) : (
          <>
            {/* 인증 중 얼굴 아이콘 주변으로 퍼지는 스캔 링 */}
            <span className={`${styles.scanRing} pk-anim-ring`} />
            <span className={`${styles.faceScan} pk-anim-facescan`}>
              <svg
                className={`${styles.faceIcon} pk-anim-facespin`}
                width="74" height="74" viewBox="0 0 44 44" fill="none"
                stroke="#34C759" strokeWidth="3"
                strokeLinecap="round" strokeLinejoin="round"
              >
                <circle cx="22" cy="22" r="18" />
                <path d="M16 17v3" />
                <path d="M28 17v3" />
                <path d="M15 26a10 10 0 0 0 14 0" />
              </svg>
            </span>
          </>
        )}
      </div>

      <div className={styles.caption} role="status" aria-live="polite">
        <div className={`${styles.hint} ${ok ? styles.ok : styles.scanning}`}>
          {ok ? '인증되었습니다' : 'Face ID로 인증하는 중…'}
        </div>
        <div className={styles.detail}>
          {chosen?.card_company} · {krw(final)}원
        </div>
      </div>
    </div>
  )
}
