import { gradientForCard } from '../data/cards.js'
import { cardImage } from '../data/cardImages.js'
import CardArt from './CardArt.jsx'
import styles from './CardFace.module.css'

/**
 * 카드 앞면.
 *
 * 카드사·카드명은 카드 사진에 이미 인쇄돼 있어 따로 얹지 않습니다.
 * 위에 올리는 정보(카드번호·금액)는 흰 글자로 두고, 그 아래에만
 * 옅은 어두운 막을 깔아 밝은 카드에서도 읽히게 합니다.
 *
 * @param {object} props
 * @param {object} props.card `{ card_id, card_company, card_name, last_four }`
 * @param {'stack'|'detail'} [props.variant] 크기
 * @param {string} [props.spent] 이번 달 사용액 (포맷된 문자열)
 * @param {string} [props.benefit] 받은 혜택 (포맷된 문자열)
 * @param {string} [props.expiry] 만료일 `MM/YY`
 * @param {boolean} [props.showStats] 사용금액·받은 혜택 표시 여부. 기본 true
 */
export default function CardFace({
  card,
  variant = 'stack',
  spent,
  benefit,
  expiry,
  showStats = true,
}) {
  const background = gradientForCard(card)
  const image = cardImage(card)

  // 카드번호는 홈에서는 감추고 상세 화면에서만 좌측 하단에 보여줍니다.
  const showNumber = variant === 'detail' && card.last_four

  return (
    <div
      className={[
        styles.card,
        styles[variant],
        image ? styles.hasImage : '',
        variant === 'detail' ? 'pk-anim-pop-ease' : '',
      ].join(' ')}
      style={{ background }}
    >
      {image && <CardArt src={image} frame="landscape" />}

      {/* 얹을 글자가 있을 때만 막을 깝니다. 아무것도 없으면 사진 그대로. */}
      {(showStats || showNumber) && <span className={styles.scrim} aria-hidden="true" />}

      <div className={styles.foot}>
        <div className={styles.footLeft}>
          {showNumber && (
            <div className={styles.number}>
              <span className={styles.dots}>••••</span>
              {card.last_four}
            </div>
          )}

          {/* OFF 로 두면 금액을 숨겨 카드 사진만 깔끔하게 보여줍니다. */}
          {showStats && (
            <div className={styles.stats}>
              <div className={styles.stat}>
                <div className={styles.statLabel}>이번 달 사용</div>
                <div className={styles.statValue}>
                  {spent}
                  <span className={styles.statUnit}>원</span>
                </div>
              </div>
              <div className={styles.stat}>
                <div className={styles.statLabel}>받은 혜택</div>
                <div className={styles.statValue}>
                  {benefit}
                  <span className={styles.statUnit}>원</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {expiry && <div className={styles.expiry}>EXP {expiry}</div>}
      </div>
    </div>
  )
}
