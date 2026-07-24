import { useEffect, useMemo } from 'react'
import { useApp } from '../state/AppContext.jsx'
import CardArt from '../components/CardArt.jsx'
import { A } from '../state/appReducer.js'
import {
  rankedRecommendations,
  adaptApiRecoCard,
  selectRecoList,
  benefitText,
  findMainBenefit,
} from '../utils/recommend.js'
import { fetchCardRecommendations } from '../api/picka.js'
import { readRecoCache, writeRecoCache } from '../utils/recoCache.js'
import { krw, krwMinus, feeText } from '../utils/format.js'
import styles from './Recommend.module.css'

const TYPE_LABEL = { credit: '신용카드', check: '체크카드' }

/**
 * 소비패턴 분석 카드 추천 순위.
 * 홈의 광고 배너에서 들어오고, 카드를 누르면 분석 결과(recoDetail)로 넘어갑니다.
 *
 * 두 갈래로 동작합니다.
 *  - 광고 배너(recoCategory 없음): 백엔드가 최근 소비를 분석해 추천 (card-recommendations)
 *  - 결제 직후 '구경하러 가기'(recoCategory 있음): 그 업종 기준 정적 스냅샷
 */
export default function Recommend() {
  const { state, dispatch } = useApp()
  const { recoType, cards, recoCategory: category, recoStatus } = state

  const userId = state.user?.userId
  const isPatternReco = !category && !!userId
  // 이 탭을 아직 이번 세션 상태에 못 담았으면 데이터가 필요합니다.
  const needsData = isPatternReco && state.recoCards[recoType] === null

  // 백엔드는 KST 하루 1회만 실제 추천을 계산하므로, 프론트도 그날 결과를 로컬에
  // 캐시해 둡니다. 캐시가 있으면 로그아웃 후 재방문에도 로딩·재요청 없이 그대로 씁니다.
  const todayCache = useMemo(
    () => (isPatternReco ? readRecoCache(userId, recoType) : null),
    [isPatternReco, userId, recoType],
  )

  useEffect(() => {
    if (!needsData) return undefined

    // 1) 오늘 이미 받아 둔 캐시가 있으면 즉시 반영 — 백엔드 호출도 로딩도 없습니다.
    if (todayCache) {
      dispatch({
        type: A.SET_RECO_CARDS,
        cardType: recoType,
        cards: todayCache.cards,
        meta: todayCache.meta,
      })
      return undefined
    }

    // 2) 그날 최초 진입 — 백엔드가 실제 추천을 계산합니다(로딩 표시). 성공 시 캐시에 저장.
    let cancelled = false
    dispatch({ type: A.SET_RECO_STATUS, status: 'loading' })
    fetchCardRecommendations(userId, recoType)
      .then(({ meta, cards: apiCards }) => {
        if (cancelled) return
        const adapted = apiCards.map(adaptApiRecoCard)
        dispatch({ type: A.SET_RECO_CARDS, cardType: recoType, cards: adapted, meta })
        writeRecoCache(userId, recoType, { cards: adapted, meta })
      })
      .catch(() => {
        if (!cancelled) dispatch({ type: A.SET_RECO_STATUS, status: 'error' })
      })
    return () => {
      cancelled = true
    }
  }, [needsData, todayCache, userId, recoType, dispatch])

  const list = category
    ? rankedRecommendations(recoType, cards, category)
    : selectRecoList(state)
  const top = list[0]
  const rest = list.slice(1)

  // 광고 추천은 로딩·오류 상태가 있습니다 (정적 카테고리 추천은 즉시 준비됨).
  // 오늘자 캐시가 있으면(로그아웃 후 재방문 등) 로딩 없이 바로 반영되므로 스피너를 띄우지 않습니다.
  const loading =
    isPatternReco && !todayCache &&
    (recoStatus === 'loading' || (needsData && recoStatus === 'idle'))
  const errored = isPatternReco && recoStatus === 'error'
  // 최근 소비가 없으면 백엔드가 topCategory=null 과 0원 카드를 주므로 빈 상태로 봅니다.
  const noRecentSpending =
    isPatternReco && recoStatus === 'ready' && !state.recoMeta?.topCategory

  const showRanking = !loading && !errored && !noRecentSpending && top

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
        {category && <div className={styles.catChip}>📍 조금 전 {category} 결제 기준</div>}
        {/* 업종명이 길어도 쉼표 뒤에서 끊기도록 줄을 직접 나눕니다. */}
        <div className={styles.title}>
          {category ? (
            <>
              {category} 결제,
              <br />
              지금보다 더 할인 받아요
            </>
          ) : (
            `내 카드 ${cards.length}장 대신 쓸 때`
          )}
        </div>
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

      {loading && <div className={styles.empty}>소비 패턴을 분석하고 있어요…</div>}
      {errored && <div className={styles.empty}>추천을 불러오지 못했어요.</div>}
      {!loading && !errored && !showRanking && (
        <div className={styles.empty}>
          {category
            ? '추천할 카드가 없어요.'
            : '최근 소비 내역이 없어 추천할 카드를 찾지 못했어요.'}
        </div>
      )}

      {showRanking && (
        <>
          <section className={styles.topSection}>
            <div className={styles.rankTop}>
              <span className={styles.crown}>👑</span>
              <span className={styles.rankTopText}>1위</span>
            </div>

            <div className={styles.row}>
              <div className={styles.cardArtWrap}>
                <div className={styles.cardArt} style={{ background: top.grad }}>
                  {top.image ? (
                    <CardArt src={top.image} frame="landscape" />
                  ) : (
                    <>
                      <span className={styles.cardShort}>{top.short}</span>
                      <span className={styles.cardIssuer}>{top.issuer}</span>
                    </>
                  )}
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

      {showRanking && rest.map((card, i) => (
        <section key={card.id} className={styles.restSection}>
          <div className={styles.restHead}>
            <span className={styles.rank}>{i + 2}위</span>
            <span className={styles.restName}>{card.name}</span>
          </div>

          <button type="button" className={styles.restRow} onClick={() => openDetail(card)}>
            <span className={styles.cardArtWrapSm}>
              <span className={styles.cardArtSm} style={{ background: card.grad }}>
                {card.image ? (
                  <CardArt src={card.image} frame="landscape" />
                ) : (
                  <>
                    <span className={styles.cardShortSm}>{card.short}</span>
                    <span className={styles.cardIssuerSm}>{card.issuer}</span>
                  </>
                )}
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
        {category
          ? `${category} 혜택 기준으로 추천된 ${TYPE_LABEL[recoType]} 순위예요`
          : `내 소비패턴 기반으로 추천된 ${TYPE_LABEL[recoType]} 순위예요`}
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
        <span className={styles.figureValue}>{feeText(card.fee)}</span>
      </span>
      {card.cashback ? (
        <span className={styles.figure}>
          <span className={styles.figureLabel}>캐시백</span>
          <span className={styles.figureCash}>최대 {krw(card.cashback)}원</span>
        </span>
      ) : (
        <span className={styles.figure}>
          <span className={styles.figureLabel}>주요 혜택</span>
          <span className={styles.figureCash}>
            {benefitText(findMainBenefit(card), card)}
          </span>
        </span>
      )}
    </>
  )
}
