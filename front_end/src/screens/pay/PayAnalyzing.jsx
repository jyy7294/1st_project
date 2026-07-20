import { useEffect, useState } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { fetchRecommendation } from '../../api/picka.js'
import shared from './payShared.module.css'
import styles from './PayAnalyzing.module.css'

const STEP_LABELS = ['카드 혜택 조회', '할인 계산', '적립 계산', '최적 카드 선택']
const STEP_INTERVAL_MS = 620
const MIN_DURATION_MS = 2900

export default function PayAnalyzing() {
  const { state, dispatch } = useApp()
  const [step, setStep] = useState(0)

  // 체크리스트 진행 애니메이션.
  // 마지막 단계에 닿으면 타이머를 걸지 않습니다 — setStep 업데이터는 순수하게 둡니다.
  useEffect(() => {
    if (step >= STEP_LABELS.length) return undefined
    const timer = setInterval(() => {
      setStep((s) => (s >= STEP_LABELS.length ? s : s + 1))
    }, STEP_INTERVAL_MS)
    return () => clearInterval(timer)
  }, [step])

  // 추천 API 호출. 최소 표시 시간을 함께 기다립니다.
  useEffect(() => {
    if (!state.transaction) return
    let cancelled = false

    async function run() {
      const minDelay = new Promise((resolve) => setTimeout(resolve, MIN_DURATION_MS))

      let data = null
      let failure = null
      try {
        data = await fetchRecommendation(state.transaction)
      } catch (err) {
        failure = err
      }

      await minDelay
      if (cancelled) return

      if (failure) {
        // 404는 "혜택 카드 없음" 안내로 구분합니다. 오류가 아닙니다.
        if (failure.status === 404) dispatch({ type: A.SET_NO_ELIGIBLE })
        else {
          dispatch({
            type: A.SET_ERROR,
            message: failure.message || '추천 결과를 불러오지 못했습니다.',
          })
        }
      } else {
        dispatch({ type: A.SET_RESULT, result: data })
      }

      dispatch({ type: A.SET_PAY_STEP, payStep: 'recommend' })
    }

    run()
    return () => {
      cancelled = true
    }
  }, [state.transaction, dispatch])

  const cardCount = state.cards.length

  return (
    <div className={`${shared.screen} pk-screen`}>
      <div className={`${shared.brandRow} ${shared.end}`}>picka</div>

      <div className={styles.orbWrap} role="status" aria-live="polite">
        <div className={styles.orb}>
          <div className={`${styles.ring1} pk-anim-ring`} />
          <div className={`${styles.ring2} pk-anim-ring`} />
          <div className={`${styles.spin} pk-anim-spin pk-reduced-loading`} />
          <div className={`${styles.core} pk-anim-float`}>
            {/* 중앙 아이콘만 천천히 돕니다. 바깥 오브의 float 은 그대로 유지됩니다. */}
            <span className={`${styles.coreIcon} pk-anim-spin`}>🧠</span>
          </div>
        </div>
      </div>

      <div className={styles.head}>
        <div className={styles.headTitle}>AI 분석 중</div>
        <div className={styles.headSub}>
          현재 고객님께 가장 유리한 혜택을
          <br />
          계산하고 있습니다.
        </div>
      </div>

      <div className={styles.list}>
        {STEP_LABELS.map((label, i) => {
          const done = i < step
          const active = i === step
          const mark = done ? '✓' : active ? '◐' : '○'
          const markColor = done
            ? 'var(--green-pay)'
            : active
              ? 'var(--blue-light)'
              : 'rgba(255,255,255,.3)'
          const status = done ? '완료' : active ? '진행중' : '대기'
          const statusColor = done ? 'var(--green-pay)' : 'rgba(255,255,255,.4)'

          return (
            <div className={styles.item} key={label}>
              <span className={styles.mark} style={{ color: markColor }}>
                {mark}
              </span>
              <span className={styles.itemName}>{label}</span>
              <span className={styles.itemStatus} style={{ color: statusColor }}>
                {status}
              </span>
            </div>
          )
        })}
      </div>

      <div className={styles.barWrap}>
        <div className={styles.barTrack}>
          <div
            className={styles.barFill}
            style={{ width: `${(step / STEP_LABELS.length) * 100}%` }}
          />
        </div>
        <div className={styles.barNote}>
          <span>✦</span>
          <span>등록한 카드 {cardCount}장의 혜택을 비교하고 있어요.</span>
        </div>
      </div>
    </div>
  )
}
