import { useEffect, useState } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { SCANNED_PRODUCT } from '../../data/cards.js'
import styles from './add.module.css'

/** 인식 완료 연출을 보여주고 다음 단계로 넘어가기까지의 시간. */
const RECOGNIZE_MS = 700

/**
 * 1단계 · 카드 스캔.
 * 실제 카메라 인식은 없고 스캔 연출만 보여줍니다. 어느 쪽을 눌러도
 * 카드사·상품명이 인식된 상태로 2단계(직접 입력)로 넘어갑니다.
 *
 * recognized 가 되면 반복 애니메이션(스캔 라인·글로우·플로트)이 멈추고
 * 그 뒤에 기존 다음 단계인 'input' 으로 이동합니다.
 * 실제 카드 인식 API를 붙일 때는 setRecognized(true) 를 응답 성공 시점으로 옮기면 됩니다.
 */
export default function AddScan() {
  const { dispatch } = useApp()
  const [recognized, setRecognized] = useState(false)

  useEffect(() => {
    if (!recognized) return undefined
    const timer = setTimeout(() => dispatch({ type: A.SET_ADD_STEP, step: 'input' }), RECOGNIZE_MS)
    return () => clearTimeout(timer)
  }, [recognized, dispatch])

  // 연속으로 눌러도 인식 흐름은 한 번만 시작됩니다.
  const toInput = () => setRecognized(true)

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

      <div className={styles.tabs}>
        <button type="button" className={`${styles.tab} ${styles.active}`}>
          <span className={styles.tabIcon}>📷</span>
          카드 스캔
        </button>
        <button type="button" className={styles.tab} onClick={toInput} disabled={recognized}>
          <span className={styles.tabIcon}>✏️</span>
          직접 입력
        </button>
      </div>

      <div
        className={`${styles.scanFrame} ${recognized ? styles.recognized : ''}`}
        role="status"
        aria-live="polite"
      >
        <span className={`${styles.corner} ${styles.tl}`} />
        <span className={`${styles.corner} ${styles.tr}`} />
        <span className={`${styles.corner} ${styles.bl}`} />
        <span className={`${styles.corner} ${styles.br}`} />

        <div className={`${styles.scanCard} ${recognized ? '' : 'pk-anim-cardscan'}`}>
          <span className={styles.scanChip} />
          <span className={styles.scanLineWide} />
          <span className={styles.scanLineShort} />
        </div>

        <div className={`${styles.scanBeam} ${recognized ? '' : 'pk-anim-scanbeam'}`} />
        <span className={styles.scanHint}>카드를 사각형 안에 맞춰주세요</span>
      </div>

      <div className={styles.note}>
        {SCANNED_PRODUCT.card_company} {SCANNED_PRODUCT.card_name}로 인식했어요.
        <br />
        번호와 유효기간은 다음 화면에서 확인해 주세요.
      </div>

      <button
        type="button"
        className={`${styles.primaryBtn} ${styles.pinToBottom}`}
        onClick={toInput}
        disabled={recognized}
      >
        등록하기 →
      </button>
    </div>
  )
}
