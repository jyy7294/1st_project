import { gradientFor } from '../data/cards.js'
import styles from './CardFace.module.css'

/**
 * 카드 앞면.
 *
 * @param {object} props
 * @param {object} props.card `{ card_company, card_name, last_four, nickname, gradient? }`
 * @param {'stack'|'detail'} [props.variant] 크기
 * @param {string} [props.spent] 이번 달 사용액 (포맷된 문자열)
 * @param {string} [props.benefit] 받은 혜택 (포맷된 문자열)
 * @param {string} [props.expiry] 만료일 `MM/YY`
 */
export default function CardFace({
  card,
  variant = 'stack',
  spent,
  benefit,
  expiry,
}) {
  const background = card.gradient || gradientFor(card.card_company)

  return (
    <div className={`${styles.card} ${styles[variant]}`} style={{ background }}>
      <div className={styles.head}>
        <div>
          <div className={styles.company}>{card.card_company}</div>
          <div className={styles.product}>{card.card_name}</div>
        </div>
        {card.nickname && <span className={styles.chip}>{card.nickname}</span>}
      </div>

      <div className={styles.number}>•••• •••• •••• {card.last_four}</div>

      <div className={styles.foot}>
        <div className={styles.stats}>
          <div>
            <div className={styles.statLabel}>이번 달 사용</div>
            <div className={styles.statValue}>
              {spent}
              <span className={styles.statUnit}>원</span>
            </div>
          </div>
          <div>
            <div className={styles.statLabel}>받은 혜택</div>
            <div className={`${styles.statValue} ${styles.gold}`}>
              {benefit}
              <span className={styles.statUnit}>원</span>
            </div>
          </div>
        </div>
        {expiry && <div className={styles.expiry}>EXP {expiry}</div>}
      </div>
    </div>
  )
}
