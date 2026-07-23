import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { gradientForCard } from '../data/cards.js'
import { cardImage } from '../data/cardImages.js'
import CardArt from '../components/CardArt.jsx'
import { REPORT_MONTHS } from '../data/report.js'
import { krw, parseKrw } from '../utils/format.js'
import styles from './CardsManage.module.css'

/**
 * 결제수단 관리. 홈 헤더의 더보기(☰)로 들어옵니다.
 * 상단 요약과 '지난달보다 ~원 덜 썼어요' 바를 누르면 월별 소비 리포트로 넘어가고,
 * 보유 카드를 누르면 그 카드의 상세로 넘어갑니다.
 */
export default function CardsManage() {
  const { state, dispatch } = useApp()
  const { cards } = state

  const totalSpent = cards.reduce((sum, c) => sum + parseKrw(c.spent), 0)
  const totalSaved = cards.reduce((sum, c) => sum + parseKrw(c.benefit), 0)

  // 지출 비교는 리포트와 같은 데이터를 씁니다 (이번 달 vs 지난달 같은 기간).
  const cur = REPORT_MONTHS[REPORT_MONTHS.length - 1]
  const prev = REPORT_MONTHS[REPORT_MONTHS.length - 2]
  const spentDiff = prev ? cur.spent - prev.spent : 0

  const goReport = () => dispatch({ type: A.SET_SCREEN, screen: 'report' })

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.header}>
        <button
          type="button"
          className={styles.iconBtn}
          aria-label="뒤로"
          onClick={() => dispatch({ type: A.GO_HOME })}
        >
          ‹
        </button>
        <span className={styles.headerTitle}>결제수단 관리</span>
        <span className={styles.spacer} />
      </div>

      <div className={styles.summary}>
        <button type="button" className={styles.summaryTop} onClick={goReport}>
          <div className={styles.summaryCell}>
            <div className={styles.summaryLabel}>이번 달 전체 사용</div>
            <div className={styles.summaryValue}>
              {krw(totalSpent)}
              <span className={styles.summaryUnit}>원</span>
            </div>
          </div>
          <div className={styles.divider} />
          <div className={styles.summaryCell}>
            <div className={styles.summaryLabel}>이번 달 챙긴 혜택</div>
            <div className={`${styles.summaryValue} ${styles.gold}`}>
              {krw(totalSaved)}
              <span className={styles.summaryUnit}>원</span>
            </div>
          </div>
          <span className={styles.summaryChevron}>📊</span>
        </button>

        <button type="button" className={styles.insightBar} onClick={goReport}>
          <span>✨</span>
          <span className={styles.insightText}>
            {spentDiff <= 0
              ? `지난달보다 ${krw(Math.abs(spentDiff))}원 덜 썼어요!`
              : `지난달보다 ${krw(spentDiff)}원 더 썼어요.`}
          </span>
          <span className={styles.insightChevron}>›</span>
        </button>
      </div>

      <div className={styles.sectionTitle}>보유 카드 {cards.length}개</div>

      <div className={styles.list}>
        {cards.length === 0 && (
          <div className={styles.empty}>등록된 카드가 없어요.</div>
        )}

        {cards.map((card, i) => (
          <button
            key={card.card_id}
            type="button"
            className={styles.cardRow}
            onClick={() => dispatch({ type: A.OPEN_CARD, index: i, from: 'cards' })}
          >
            <span className={styles.swatch} style={{ background: gradientForCard(card) }}>
              <CardArt src={cardImage(card)} frame="landscape" />
            </span>
            <span className={styles.cardBody}>
              <span className={styles.cardCompany}>{card.card_company}</span>
              <span className={styles.cardName}>
                {card.card_name} · {card.last_four}
              </span>
            </span>
            <span className={styles.cardAmountBox}>
              <span className={styles.cardSpent}>
                {krw(parseKrw(card.spent))}
                <span className={styles.cardUnit}>원</span>
              </span>
              <span className={styles.cardBenefit}>
                혜택 +{krw(parseKrw(card.benefit))}원
              </span>
            </span>
          </button>
        ))}
      </div>

      <button
        type="button"
        className={styles.fab}
        aria-label="카드 등록"
        onClick={() => dispatch({ type: A.START_ADD })}
      >
        +
      </button>
    </div>
  )
}
