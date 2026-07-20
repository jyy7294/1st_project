import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { LABEL_CHOICES } from '../data/labels.js'
import styles from './LabelSheet.module.css'

/**
 * 라벨(별칭) 편집 바텀시트. 화면 위에 덮이는 오버레이라 화면 컴포넌트가 아니라
 * 상세 화면 안에서 조건부로 렌더합니다. 배경을 누르면 닫힙니다.
 */
export default function LabelSheet() {
  const { state, dispatch } = useApp()
  const card = state.cards[state.active]

  if (!card) return null

  const close = () => dispatch({ type: A.SET_LABEL_SHEET, open: false })

  return (
    <div className={styles.dim} onClick={close}>
      <div className={`${styles.sheet} pk-anim-up`} onClick={(e) => e.stopPropagation()}>
        <div className={styles.grip} />
        <div className={styles.title}>라벨 선택</div>
        <div className={styles.sub}>
          {card.card_company} · {card.card_name}
        </div>

        <div className={styles.chips}>
          {LABEL_CHOICES.map((choice) => {
            const selected = card.nickname === choice.name
            return (
              <button
                key={choice.name}
                type="button"
                className={`${styles.chip} ${selected ? styles.selected : ''}`}
                onClick={() =>
                  dispatch({
                    type: A.SET_NICKNAME,
                    index: state.active,
                    nickname: choice.name,
                  })
                }
              >
                <span className={styles.chipIcon}>{choice.icon}</span>
                {choice.name}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
