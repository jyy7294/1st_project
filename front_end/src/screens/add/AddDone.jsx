import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { gradientForCard } from '../../data/cards.js'
import styles from './add.module.css'

/** 4단계 · 등록 완료. 방금 지갑에 추가된 카드를 그대로 보여줍니다. */
export default function AddDone() {
  const { state, dispatch } = useApp()
  const card = state.addedCard

  if (!card) return null

  const index = state.cards.findIndex((c) => c.card_id === card.card_id)

  return (
    <div className={`${styles.screen} ${styles.doneScreen} pk-screen`}>
      <div className={`${styles.doneBadge} pk-anim-pop`}>✓</div>
      <div className={styles.doneTitle}>카드 등록 완료</div>
      <div className={styles.doneSub}>
        {card.card_company} {card.card_name}가
        <br />
        성공적으로 등록되었습니다.
      </div>

      <div className={styles.doneCard} style={{ background: gradientForCard(card) }}>
        <div>
          <div className={styles.previewCompany}>{card.card_company}</div>
          <div className={styles.previewProduct}>{card.card_name}</div>
        </div>
        <div className={styles.doneCardNumber}>**** **** **** {card.last_four}</div>
        <div className={styles.doneCardExpiry}>EXP {card.expiry}</div>
      </div>

      <div className={styles.doneFacts}>
        <div className={styles.doneFact}>
          <span className={styles.doneFactLabel}>카드 별칭</span>
          <span className={styles.doneFactValue}>{card.nickname}</span>
        </div>
        <div className={styles.doneFact}>
          <span className={styles.doneFactLabel}>보유 카드</span>
          <span className={styles.doneFactValue}>{state.cards.length}장</span>
        </div>
      </div>

      <button
        type="button"
        className={styles.doneBtn}
        onClick={() => dispatch({ type: A.GO_HOME })}
      >
        확인
      </button>
      <button
        type="button"
        className={styles.doneGhostBtn}
        disabled={index < 0}
        onClick={() => dispatch({ type: A.OPEN_CARD, index })}
      >
        카드 상세 보기
      </button>
    </div>
  )
}
