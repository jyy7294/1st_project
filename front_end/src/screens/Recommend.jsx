import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { rankedRecommendations } from '../utils/recommend.js'
import { krw } from '../utils/format.js'
import styles from './Recommend.module.css'

const TYPE_LABEL = { credit: '신용카드', check: '체크카드' }

/**
 * 소비패턴 분석 카드 추천 순위.
 * 홈의 광고 배너에서 들어오고, 카드를 누르면 분석 결과(recoDetail)로 넘어갑니다.
 */
export default function Recommend() {
  const { state, dispatch } = useApp()
  const { recoType, cards } = state

  const list = rankedRecommendations(recoType, cards)
  const top = list[0]
  const rest = list.slice(1)

  const openDetail = (card) => dispatch({ type: A.OPEN_RECO_DETAIL, id: card.id })

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.header}>
        <button
          type="button"
          className={styles.backBtn}
          aria-label="뒤로"
          onClick={() => dispatch({ type: A.GO_HOME })}
        >
          ‹
        </button>
      </div>

      <div className={styles.titleWrap}>
        <div className={styles.title}>내 카드 {cards.length}장 대신 쓸 때</div>
        <div className={styles.title}>혜택 많이 받는 카드 순위</div>
      </div>

      <div className={styles.tabs}>
        {['credit', 'check'].map((type) => (
          <button
            key={type}
            type="button"
            className={`${styles.tab} ${recoType === type ? styles.tabOn : ''}`}
            aria-pressed={recoType === type}
            onClick={() => dispatch({ type: A.SET_RECO_TYPE, recoType: type })}
          >
            {TYPE_LABEL[type]}
          </button>
        ))}
      </div>

      <div className={styles.divider} />

      {!top && <div className={styles.empty}>추천할 카드가 없어요.</div>}

      {top && (
        <>
          <section className={styles.topSection}>
            <div className={styles.rankTop}>
              <span className={styles.crown}>👑</span>
              <span className={styles.rankTopText}>1위</span>
            </div>

            <div className={styles.row}>
              <div className={styles.cardArtWrap}>
                <div className={styles.cardArt} style={{ background: top.grad }}>
                  <span className={styles.cardShort}>{top.short}</span>
                  <span className={styles.cardIssuer}>{top.issuer}</span>
                </div>
              </div>

              <div className={styles.info}>
                <div className={styles.cardName}>{top.name}</div>

                <div className={styles.totalRow}>
                  <span className={styles.totalLabel}>총 혜택</span>
                  <span className={styles.totalValue}>{krw(top.total)}원</span>
                </div>

                <Figures card={top} />

                <button
                  type="button"
                  className={styles.analyzeBtn}
                  onClick={() => openDetail(top)}
                >
                  분석 결과 보기
                </button>
              </div>
            </div>
          </section>

          <div className={styles.divider} />
        </>
      )}

      {rest.map((card, i) => (
        <section key={card.id} className={styles.restSection}>
          <div className={styles.restHead}>
            <span className={styles.rank}>{i + 2}위</span>
            <span className={styles.restName}>{card.name}</span>
          </div>

          <button type="button" className={styles.restRow} onClick={() => openDetail(card)}>
            <span className={styles.cardArtWrapSm}>
              <span className={styles.cardArtSm} style={{ background: card.grad }}>
                <span className={styles.cardShortSm}>{card.short}</span>
                <span className={styles.cardIssuerSm}>{card.issuer}</span>
              </span>
            </span>

            <span className={styles.info}>
              <span className={styles.totalRow}>
                <span className={styles.totalLabel}>총 혜택</span>
                <span className={styles.totalRight}>
                  <span className={styles.totalValueSm}>{krw(card.total)}원</span>
                  <span className={styles.chevron}>›</span>
                </span>
              </span>

              <Figures card={card} />
            </span>
          </button>

          <div className={styles.divider} />
        </section>
      ))}

      <div className={styles.footNote}>
        내 소비패턴 기반으로 추천된 {TYPE_LABEL[recoType]} 순위예요
      </div>
    </div>
  )
}

/** 혜택 / 연회비 / 캐시백 3줄. 1위와 나머지가 같은 표기를 씁니다. */
function Figures({ card }) {
  return (
    <>
      <span className={styles.figure}>
        <span className={styles.figureLabel}>혜택</span>
        <span className={styles.figureValue}>{krw(card.benefit)}원</span>
      </span>
      <span className={styles.figure}>
        <span className={styles.figureLabel}>연회비</span>
        <span className={styles.figureValue}>-{krw(card.fee)}원</span>
      </span>
      <span className={styles.figure}>
        <span className={styles.figureLabel}>캐시백</span>
        <span className={styles.figureCash}>최대 {krw(card.cashback)}원</span>
      </span>
    </>
  )
}
