import { useEffect, useState } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { SCANNED_CARD_INPUT } from '../../data/cards.js'
import styles from './add.module.css'

const ZOOM_MS = 1500 // 카드가 격자(코너 틀)에 서서히 다다르기까지
const DONE_MS = 600 // '인식 완료' 표시 후 다음 화면까지

/**
 * 1단계 · 카드 스캔.
 * 시연이라 실제 카메라 인식은 없고, 스캔 영역(뷰파인더)을 탭하면 잠깐 '인식' 연출을
 * 보여준 뒤 카드정보·유효기간·CVC 가 자동입력된 입력 화면(비번만 남음)으로 넘어갑니다.
 * 아래 '직접 입력하기'는 스캔 대신 직접 입력하는 대안 경로입니다.
 */
export default function AddScan() {
  const { dispatch } = useApp()
  // 'idle' → 탭 → 'scanning'(카드가 격자까지 확대) → 'done'(인식 완료) → 다음 화면
  const [phase, setPhase] = useState('idle')
  const scanning = phase !== 'idle'
  const done = phase === 'done'

  useEffect(() => {
    if (phase === 'scanning') {
      const t = setTimeout(() => setPhase('done'), ZOOM_MS)
      return () => clearTimeout(t)
    }
    if (phase === 'done') {
      const t = setTimeout(() => {
        dispatch({ type: A.ENTER_ADD_INPUT, mode: 'scan', form: SCANNED_CARD_INPUT })
      }, DONE_MS)
      return () => clearTimeout(t)
    }
    return undefined
  }, [phase, dispatch])

  const startScan = () => setPhase('scanning')
  const manual = () => dispatch({ type: A.ENTER_ADD_INPUT, mode: 'manual' })

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.header}>
        <button
          type="button"
          className={styles.backBtn}
          aria-label="닫기"
          onClick={() => dispatch({ type: A.GO_HOME })}
        >
          ✕
        </button>
        <span className={styles.headerTitle}>카드 등록</span>
        <span className={styles.spacer} />
      </div>

      {/* 뷰파인더 — 탭하면 인식 연출 후 정보 입력 화면으로 넘어갑니다. */}
      <div
        className={`${styles.viewfinder} ${scanning ? styles.scanning : ''}`}
        role="button"
        tabIndex={0}
        aria-label="카드 스캔하기"
        onClick={scanning ? undefined : startScan}
        onKeyDown={(e) => {
          if (!scanning && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault()
            startScan()
          }
        }}
      >
        <span className={`${styles.corner} ${styles.tl}`} />
        <span className={`${styles.corner} ${styles.tr}`} />
        <span className={`${styles.corner} ${styles.bl}`} />
        <span className={`${styles.corner} ${styles.br}`} />

        <div className={`${styles.scanCard} ${scanning ? 'pk-anim-cardgrow' : 'pk-anim-float'}`}>
          <img src="/assets/shinhan-card.png" alt="" className={styles.scanCardImg} />
        </div>

        <div className={`${styles.beam} ${scanning ? '' : 'pk-anim-scanbeam'}`} />

        {done ? (
          <span className={styles.scanDone}>
            <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <path
                d="M2.5 7.5l3 3 6-7"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            인식 완료
          </span>
        ) : (
          <span className={styles.hint}>카드를 사각형 안에 맞춰 주세요</span>
        )}
      </div>

      <div className={styles.manualHelp}>
        카드 인식이 잘 되지 않을 경우에는 직접 입력하세요
      </div>

      <button type="button" className={styles.primaryBtn} onClick={manual}>
        직접 입력하기
        <svg width="17" height="14" viewBox="0 0 18 14" fill="none" aria-hidden="true">
          <path
            d="M2 7h13M10 2l5 5-5 5"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
    </div>
  )
}
