import { useEffect, useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import CardArt from '../components/CardArt.jsx'
import { A } from '../state/appReducer.js'
import {
  CURRENT_YEAR_BENEFIT,
  NOTICE_CONTACT,
  PAY_NOTICE,
  RECO_CATEGORY_SPLIT,
  RECO_NOTICE,
} from '../data/recommend.js'
import { selectRecoCard, benefitText, findMainBenefit } from '../utils/recommend.js'
import { benefitsForRecoCard } from '../data/recommendBenefits.js'
import { benefitView } from '../utils/benefit.js'
import { buildDonut, buildSpendingMix } from '../utils/report.js'
import { fetchAllTransactions } from '../api/picka.js'
import { krw, krwMinus, feeText } from '../utils/format.js'
import styles from './RecommendDetail.module.css'

/** 카테고리 혜택은 상위 몇 개만 먼저 보여줍니다. */
const CATEGORY_PREVIEW = 3

/** 상세 혜택도 주요 몇 개만 먼저 보여주고, 나머지는 '자세히 보기'로 봅니다. */
const BENEFIT_PREVIEW = 3

/**
 * 추천 카드 분석 결과.
 * '분석 결과 보기' 또는 순위 목록의 카드에서 들어옵니다.
 * 맨 아래 '카드 자세히 보기'는 그 카드의 카드고릴라 상세 페이지로 나갑니다.
 */
export default function RecommendDetail() {
  const { state, dispatch } = useApp()
  const card = selectRecoCard(state)
  // 목록이 길어 화면이 답답해지지 않도록 접어 두고, 필요할 때만 펼칩니다.
  const [catOpen, setCatOpen] = useState(false)
  // 소비 성향 범례를 상위 3개만 볼지, 전체를 볼지
  const [mixOpen, setMixOpen] = useState(false)

  const userId = state.user?.userId
  const cardIds = state.cards.map((c) => c.card_id)
  const mix = state.spendingMix

  // 최근 3개월 소비 성향(빈도·금액)은 한 번만 모아 두고 재사용합니다.
  useEffect(() => {
    if (!userId || mix || cardIds.length === 0) return undefined
    let cancelled = false
    fetchAllTransactions(userId, cardIds)
      .then((txs) => {
        if (!cancelled) {
          dispatch({ type: A.SET_SPENDING_MIX, mix: buildSpendingMix(txs) })
        }
      })
      .catch(() => {
        // 소비 성향을 못 불러와도 나머지 분석 결과는 그대로 보여 줍니다.
        if (!cancelled) dispatch({ type: A.SET_SPENDING_MIX, mix: { byCount: [], byAmount: [] } })
      })
    return () => {
      cancelled = true
    }
    // cardIds 는 매 렌더 새 배열이라 길이로만 의존합니다.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, mix, cardIds.length, dispatch])

  if (!card) return null

  // 광고 배너(소비패턴) 추천은 백엔드 분석 결과를, 결제 업종 추천은 정적 데이터를 씁니다.
  const fromSpending = !state.recoCategory
  const meta = state.recoMeta

  // 대표 혜택 문구 — 단위(%/원)를 보고 만들어 정액 혜택에 %가 붙지 않게 합니다.
  const mainBenefitText = benefitText(findMainBenefit(card), card)

  // 카드 상세 페이지와 같은 포맷으로 상세 혜택을 표기합니다.
  const benefits = benefitsForRecoCard(card.id).map(benefitView)
  const highlights = benefits.slice(0, BENEFIT_PREVIEW)

  // (정적 카테고리 추천에서만) 총 혜택을 카테고리 비율로 나눠 보여줍니다.
  const categories = RECO_CATEGORY_SPLIT
    .map((c) => ({ ...c, amount: Math.round(card.benefit * c.fraction) }))
    .filter((c) => c.amount > 0)
    .sort((a, b) => b.amount - a.amount)

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.header}>
        <button
          type="button"
          className={styles.backBtn}
          aria-label="뒤로"
          onClick={() => dispatch({ type: A.SET_SCREEN, screen: 'recommend' })}
        >
          ‹
        </button>
      </div>

      <div className={styles.headWrap}>
        {fromSpending ? (
          <>
            <div className={styles.title}>
              이 카드로 연간
              <br />
              <span className={styles.gain}>{krw(card.total)}원</span> 받을 수 있어요
            </div>
            {meta?.analysisStartDate && (
              <div className={styles.current}>
                최근 소비 분석 · {meta.analysisStartDate} ~ {meta.analysisEndDate}
              </div>
            )}
          </>
        ) : (
          <>
            <div className={styles.title}>
              이 카드만 쓰면 지금보다
              <br />
              <span className={styles.gain}>{krw(card.total - CURRENT_YEAR_BENEFIT)}원</span> 더 받아요
            </div>
            <div className={styles.current}>
              지금 받고 있는 혜택
              <span className={styles.currentValue}>{krw(CURRENT_YEAR_BENEFIT)}원</span>
            </div>
          </>
        )}
      </div>

      <div className={styles.cardWrap}>
        <div className={`${styles.cardArt} pk-anim-pop-ease`} style={{ background: card.grad }}>
          {card.image ? (
            <CardArt src={card.image} frame="portrait" />
          ) : (
            <>
              <span className={styles.cardShort}>{card.short}</span>
              <span className={styles.cardIssuer}>{card.issuer}</span>
            </>
          )}
        </div>
        <div className={styles.cardName}>{card.name}</div>
      </div>

      <div className={styles.summary}>
        <div className={styles.summaryTop}>
          <span className={styles.summaryLabel}>총 혜택</span>
          <span className={styles.summaryValue}>{krw(card.total)}원</span>
        </div>
        <div className={styles.figure}>
          <span className={styles.figureLabel}>혜택</span>
          <span className={styles.figureValue}>{krw(card.benefit)}원</span>
        </div>
        <div className={styles.figure}>
          <span className={styles.figureLabel}>연회비</span>
          <span className={styles.figureValue}>{feeText(card.fee)}</span>
        </div>
        {card.cashback ? (
          <div className={styles.figure}>
            <span className={styles.figureLabel}>캐시백</span>
            <span className={styles.figureCash}>최대 {krw(card.cashback)}원</span>
          </div>
        ) : (
          <div className={styles.figure}>
            <span className={styles.figureLabel}>{state.recoCategory || '주요'} 혜택</span>
            <span className={styles.figureCash}>{mainBenefitText}</span>
          </div>
        )}
      </div>

      {fromSpending ? (
        <>
          {/* 줄글 대신 근거를 항목으로 나눠 한눈에 */}
          <section className={styles.section}>
            <div className={styles.sectionTitle}>왜 이 카드인가요?</div>
            <div className={styles.factList}>
              {card.benefitCategory && (
                <div className={styles.factRow}>
                  <span className={styles.factLabel}>많이 쓴 업종</span>
                  <span className={styles.factValue}>
                    {card.benefitCategory}
                    {card.monthlySpend > 0 && (
                      <span className={styles.factSub}> · {krw(card.monthlySpend)}원</span>
                    )}
                  </span>
                </div>
              )}
              <div className={styles.factRow}>
                <span className={styles.factLabel}>적용 혜택</span>
                <span className={styles.factValue}>{card.benefitName}</span>
              </div>
              <div className={styles.factRow}>
                <span className={styles.factLabel}>할인 조건</span>
                <span className={styles.factValue}>{mainBenefitText}</span>
              </div>
              <div className={styles.factRow}>
                <span className={styles.factLabel}>예상 연혜택</span>
                <span className={`${styles.factValue} ${styles.factStrong}`}>
                  {krw(card.total)}원
                </span>
              </div>
            </div>
            {meta?.analysisStartDate && (
              <div className={styles.factNote}>
                {meta.analysisStartDate} ~ {meta.analysisEndDate} 소비 기준
                <br />
                최근 소비일수록 크게 반영해요 · 최근 30일 50% / 그 전 30일 30% / 그 전 30일 20%
              </div>
            )}
          </section>

          {/* 최근 3개월 소비 성향 — 빈도 / 금액 두 기준으로 비교 */}
          {(mix?.byCount?.length > 0 || mix?.byAmount?.length > 0) && (
            <section className={styles.section}>
              <div className={styles.sectionTitle}>최근 3개월 소비 성향</div>

              <div className={styles.mixCard}>
                <div className={styles.mixWrap}>
                  <MixChart title="이용 빈도" data={mix.byCount} />
                  <MixChart title="이용 금액" data={mix.byAmount} />
                </div>

                {/* 차트와 범례 사이, 우측에 전체 보기 */}
                <div className={styles.mixToggleRow}>
                  <button
                    type="button"
                    className={styles.moreInline}
                    aria-expanded={mixOpen}
                    onClick={() => setMixOpen((v) => !v)}
                  >
                    {mixOpen ? '접기' : '전체 보기'}
                  </button>
                </div>

                <div className={styles.mixWrap}>
                  <MixLegend
                    data={mix.byCount}
                    format={(v) => `${v}회`}
                    showAll={mixOpen}
                  />
                  <MixLegend
                    data={mix.byAmount}
                    format={(v) => `${krw(v)}원`}
                    showAll={mixOpen}
                  />
                </div>

                {/* '기타'가 1위보다 커 보일 수 있어 왜 순위에서 빠졌는지 밝혀 둡니다. */}
                <div className={styles.mixFootNote}>
                  기타는 상위 5개 밖 업종을 모두 합친 값이라 순위에서 제외했어요
                </div>
              </div>
            </section>
          )}
        </>
      ) : (
        <section className={styles.section}>
          <div className={styles.benefitHeadRow}>
            <span className={styles.sectionTitle}>내 1년 소비로 예상한 혜택</span>
            {categories.length > CATEGORY_PREVIEW && (
              <button
                type="button"
                className={styles.moreInline}
                aria-expanded={catOpen}
                onClick={() => setCatOpen((v) => !v)}
              >
                {catOpen ? '접기' : '전체 보기'}
              </button>
            )}
          </div>
          <div className={styles.catList}>
            {(catOpen ? categories : categories.slice(0, CATEGORY_PREVIEW)).map((c) => (
              <div key={c.name} className={styles.catRow}>
                <div className={styles.catIcon} style={{ background: c.tint }}>
                  {c.icon}
                </div>
                <span className={styles.catName}>{c.name}</span>
                <span className={styles.catAmount}>{krw(c.amount)}원</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {highlights.length > 0 && (
        <section className={styles.section}>
          <div className={styles.benefitHeadRow}>
            <span className={styles.sectionTitle}>주요 혜택</span>
            {/* 상세 혜택 전체는 보유 카드와 같은 화면에서 봅니다. */}
            <button
              type="button"
              className={styles.moreInline}
              onClick={() => dispatch({ type: A.OPEN_BENEFITS, source: 'reco' })}
            >
              전체 보기
            </button>
          </div>
          <div className={styles.benefitList}>
            {highlights.map((b) => (
              <BenefitRow key={b.id} benefit={b} />
            ))}
          </div>
        </section>
      )}

      <div className={styles.linkWrap}>
        {/* 카드고릴라의 해당 카드 상세 페이지로 나갑니다. */}
        <a
          className={styles.link}
          href={card.url}
          target="_blank"
          rel="noopener noreferrer"
        >
          카드 신청하기
        </a>
      </div>

      {/* 안내·유의사항은 맨 아래에 둬서 필요할 때만 스크롤로 보게 합니다. */}
      <section className={`${styles.section} ${styles.notesSection}`}>
        <div className={styles.sectionTitle}>서비스 안내 및 유의사항</div>
        <ul className={styles.notes}>
          {RECO_NOTICE.map((note) => (
            <li key={note} className={styles.note}>{note}</li>
          ))}
        </ul>

        <div className={`${styles.sectionTitle} ${styles.spaced}`}>결제 서비스 이용 안내</div>
        <ul className={styles.notes}>
          {PAY_NOTICE.map((note) => (
            <li key={note} className={styles.note}>{note}</li>
          ))}
        </ul>

        <div className={styles.contact}>
          {NOTICE_CONTACT[0]}
          <br />
          {NOTICE_CONTACT[1]}
        </div>
      </section>
    </div>
  )
}

/**
 * 도넛 구멍 안에 들어갈 업종명 글자 크기.
 * '카페/디저트', '공과금/생활요금'처럼 이름이 길면 줄여서 링에 닿지 않게 합니다.
 */
function nameFontSize(name = '') {
  const len = name.length
  if (len <= 4) return 14
  if (len <= 5) return 12.5
  if (len <= 6) return 11
  if (len <= 8) return 9.5
  return 8.5
}

/**
 * 소비 성향 원형 차트 하나 (빈도 또는 금액).
 * 조각이 클수록 그 업종을 많이 쓴 것입니다.
 */
function MixChart({ title, data }) {
  if (!data || data.length === 0) return <div className={styles.mix} />
  const donut = buildDonut(data)

  return (
    <div className={styles.mix}>
      <div className={styles.mixTitle}>{title}</div>

      {/* 차트 위 가운데 배지 */}
      <div className={styles.mixRankBadge}>
        <span className={styles.mixCrown} aria-hidden="true">👑</span>
        <span className={styles.mixRank}>1위</span>
      </div>

      <div className={styles.mixDonut}>
        <svg viewBox="0 0 140 140" className={styles.mixSvg}>
          {donut.segments.map((seg) => (
            <circle
              key={seg.name}
              cx="70"
              cy="70"
              r="52"
              fill="none"
              stroke={seg.color}
              strokeWidth="16"
              strokeDasharray={seg.dash}
              strokeDashoffset={seg.offset}
            />
          ))}
        </svg>
        <div className={styles.mixCenter}>
          <div className={styles.mixCenterText}>
            <span
              className={styles.mixTopName}
              style={{ fontSize: nameFontSize(donut.topName) }}
            >
              {donut.topName}
            </span>
            <span className={styles.mixTopPct} style={{ color: donut.topColor }}>
              {donut.topPercent}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

/** 위 차트의 범례. 접으면 상위 3개, 펼치면 전체 조각을 보여줍니다. */
function MixLegend({ data, format, showAll = false }) {
  if (!data || data.length === 0) return <div className={styles.mixLegend} />
  const { items } = buildDonut(data)
  const legend = showAll ? items : items.slice(0, 3)

  return (
    <div className={styles.mixLegend}>
      {legend.map((item) => (
        <div key={item.name} className={styles.mixRow}>
          <span className={styles.mixDot} style={{ background: item.color }} />
          <span className={styles.mixName}>{item.name}</span>
          <span className={styles.mixValue}>{format(item.amount)}</span>
        </div>
      ))}
    </div>
  )
}

/** 카드 상세 페이지와 동일한 혜택 한 줄. */
function BenefitRow({ benefit }) {
  return (
    <div className={styles.benefitRow}>
      <div className={styles.benefitIcon} style={{ background: benefit.tint }}>
        {benefit.icon}
      </div>
      <div className={styles.benefitBody}>
        <div className={styles.benefitHead}>
          <span className={styles.benefitTitle}>{benefit.title}</span>
          <span className={styles.benefitRate}>{benefit.rate}</span>
        </div>
        <div className={styles.benefitDesc}>{benefit.desc}</div>
      </div>
    </div>
  )
}
