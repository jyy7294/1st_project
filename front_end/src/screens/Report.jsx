import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { gradientForCard } from '../data/cards.js'
import { benefitsForCard } from '../data/benefits.js'
import { REPORT_MONTHS, monthAt, totalBenefit } from '../data/report.js'
import { buildDonut, buildSpendChart, splitBenefitByCategory } from '../utils/report.js'
import { krw } from '../utils/format.js'
import styles from './Report.module.css'

/** 월별 소비 리포트. 결제수단 관리의 요약/문구 바에서 들어옵니다. */
export default function Report() {
  const { state, dispatch } = useApp()
  const { cur, prev } = monthAt(state.reportMonth)

  const spentDiff = prev ? cur.spent - prev.spent : 0
  const savedDiff = prev ? totalBenefit(cur) - totalBenefit(prev) : 0

  const chart = buildSpendChart(cur, prev)
  const donut = buildDonut(cur.categories)

  // 혜택이 큰 카드부터 보여줍니다.
  const rankedCards = state.cards
    .map((card, index) => ({ card, index, benefit: cur.benefitByCard[card.card_id] || 0 }))
    .sort((a, b) => b.benefit - a.benefit)

  const maxBenefit = Math.max(1, ...rankedCards.map((r) => r.benefit))

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.header}>
        <button
          type="button"
          className={styles.iconBtn}
          aria-label="뒤로"
          onClick={() => dispatch({ type: A.SET_SCREEN, screen: 'cards' })}
        >
          ‹
        </button>
        <span className={styles.headerTitle}>소비 리포트</span>
        <span className={styles.spacer} />
      </div>

      <div className={styles.tabs}>
        {REPORT_MONTHS.map((month, i) => (
          <button
            key={month.key}
            type="button"
            className={`${styles.tab} ${i === state.reportMonth ? styles.tabActive : ''}`}
            onClick={() => dispatch({ type: A.SET_REPORT_MONTH, index: i })}
          >
            {month.key}
          </button>
        ))}
      </div>

      {/* 이번 달 지출 + 누적 곡선 */}
      <section className={styles.panel}>
        <div className={styles.panelLabel}>{cur.key} 지출</div>
        <div className={styles.bigNumber}>
          {krw(cur.spent)}
          <span className={styles.bigUnit}>원</span>
        </div>
        <div className={styles.compare}>
          지난달 대비{' '}
          {prev ? (
            <span
              className={styles.compareValue}
              style={{ color: spentDiff <= 0 ? 'var(--green-chart)' : 'var(--danger)' }}
            >
              {spentDiff <= 0 ? '▼' : '▲'}
              {krw(Math.abs(spentDiff))}원
            </span>
          ) : (
            <span className={styles.compareValue}>비교할 지난달 데이터가 없어요</span>
          )}
        </div>

        <div className={styles.axisUnit}>(만원)</div>
        <svg viewBox="0 0 300 150" className={styles.chart}>
          {chart.yTicks.map((tick) => (
            <g key={tick.label}>
              <line
                x1={chart.axisLeft}
                y1={tick.y}
                x2={chart.axisRight}
                y2={tick.y}
                stroke="#f0f2f6"
                strokeWidth="1"
              />
              <text
                x={chart.axisLeft - 4}
                y={tick.y}
                dy="3.5"
                fontSize="10"
                fontWeight="600"
                fill="#7a8299"
                textAnchor="end"
              >
                {tick.label}
              </text>
            </g>
          ))}

          <line
            x1={chart.todayX}
            y1={chart.axisTop}
            x2={chart.todayX}
            y2={chart.axisBottom}
            stroke="#cdd3e0"
            strokeWidth="1"
            strokeDasharray="3 3"
          />

          {chart.linePrev && (
            <polyline
              points={chart.linePrev}
              fill="none"
              stroke="#c4ccda"
              strokeWidth="2.5"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          )}
          <polyline
            points={chart.lineCur}
            fill="none"
            stroke="var(--green-chart)"
            strokeWidth="2.5"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          <circle cx={chart.todayX} cy={chart.todayY} r="4" fill="#2F8F3E" stroke="#fff" strokeWidth="2" />
        </svg>

        <div className={styles.axisDays}>
          <span>01일</span>
          <span>31일</span>
        </div>

        <div className={styles.legend}>
          <div className={styles.legendRow}>
            <span className={styles.legendName}>
              <span className={styles.legendDashCur} />
              {cur.key} (1~12일)
            </span>
            <span className={styles.legendCur}>{krw(cur.spent)}원</span>
          </div>
          {prev && (
            <div className={styles.legendRow}>
              <span className={styles.legendName}>
                <span className={styles.legendDashPrev} />
                {prev.key} (전체)
              </span>
              <span className={styles.legendPrev}>{krw(prev.full)}원</span>
            </div>
          )}
        </div>
      </section>

      {/* 카드별 혜택 */}
      <section className={styles.panel}>
        <div className={styles.savedBox}>
          <div className={styles.savedLabel}>{cur.key} 챙긴 혜택</div>
          <div className={styles.savedValue}>
            {krw(totalBenefit(cur))}
            <span className={styles.savedUnit}>원</span>
          </div>
          <div className={styles.insight}>
            <span>💡</span>
            <span>
              {!prev
                ? `${cur.key}에 받은 혜택이에요.`
                : savedDiff >= 0
                  ? `${cur.key}에는 ${prev.key}보다 혜택을 ${krw(savedDiff)}원 더 받았어요!`
                  : `${cur.key}에는 ${prev.key}보다 혜택이 ${krw(-savedDiff)}원 줄었어요.`}
            </span>
          </div>
        </div>

        <div className={styles.sectionHead}>
          <span className={styles.sectionTitle}>카드별 혜택</span>
          <span className={styles.sectionHint}>카드를 눌러 상세 보기</span>
        </div>

        <div className={styles.cardList}>
          {rankedCards.length === 0 && (
            <div className={styles.empty}>등록된 카드가 없어요.</div>
          )}

          {rankedCards.map(({ card, index, benefit }, rank) => {
            const open = state.reportCardOpen === index
            const detail = splitBenefitByCategory(benefit, benefitsForCard(card))
            const detailMax = Math.max(1, ...detail.map((d) => d.amount))

            return (
              <button
                key={card.card_id}
                type="button"
                className={styles.cardItem}
                aria-expanded={open}
                onClick={() => dispatch({ type: A.TOGGLE_REPORT_CARD, index })}
              >
                <span className={styles.cardHead}>
                  <span className={styles.cardName}>
                    <span
                      className={styles.cardSwatch}
                      style={{ background: gradientForCard(card) }}
                    />
                    {card.card_company} · {card.card_name}
                  </span>
                  <span className={styles.cardRight}>
                    <span
                      className={styles.cardBenefit}
                      style={{ color: rank === 0 ? 'var(--teal-deep)' : 'var(--navy-text)' }}
                    >
                      {krw(benefit)}원
                    </span>
                    <span className={styles.arrow}>{open ? '▲' : '▼'}</span>
                  </span>
                </span>

                <span className={styles.bar}>
                  <span
                    className={styles.barFill}
                    style={{
                      width: `${(benefit / maxBenefit) * 100}%`,
                      background: gradientForCard(card),
                    }}
                  />
                </span>

                {rank === 0 && benefit > 0 && (
                  <span className={styles.best}>🏆 {cur.key} 최대 혜택 카드</span>
                )}

                {open && (
                  <span className={styles.detail}>
                    <span className={styles.detailLabel}>카테고리별 받은 혜택</span>
                    {detail.map((d) => (
                      <span key={d.category} className={styles.detailRow}>
                        <span className={styles.detailHead}>
                          <span className={styles.detailCat}>{d.category}</span>
                          <span className={styles.detailAmount}>{krw(d.amount)}원</span>
                        </span>
                        <span className={styles.detailBar}>
                          <span
                            className={styles.detailBarFill}
                            style={{
                              width: `${(d.amount / detailMax) * 100}%`,
                              background: gradientForCard(card),
                            }}
                          />
                        </span>
                      </span>
                    ))}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      </section>

      {/* 카테고리별 지출 */}
      <section className={`${styles.panel} ${styles.last}`}>
        <div className={styles.sectionHead}>
          <span className={styles.sectionTitle}>카테고리별 지출</span>
          <span className={styles.sectionTotal}>{krw(donut.total)}원</span>
        </div>

        <div className={styles.donutWrap}>
          <div className={styles.donut}>
            <svg viewBox="0 0 140 140" className={styles.donutSvg}>
              {donut.segments.map((seg) => (
                <circle
                  key={seg.name}
                  cx="70"
                  cy="70"
                  r="52"
                  fill="none"
                  stroke={seg.color}
                  strokeWidth="18"
                  strokeDasharray={seg.dash}
                  strokeDashoffset={seg.offset}
                />
              ))}
            </svg>
            <div className={styles.donutCenter}>
              <span className={styles.donutTopName}>{donut.topName}</span>
              <span className={styles.donutTopPct} style={{ color: donut.topColor }}>
                {donut.topPercent}
              </span>
            </div>
          </div>
        </div>

        <div className={styles.catList}>
          {donut.items.map((item) => (
            <div key={item.name} className={styles.catRow}>
              <span className={styles.catName}>
                <span className={styles.dot} style={{ background: item.color }} />
                {item.name}
                <span className={styles.catPct}>{item.percent}</span>
              </span>
              <span className={styles.catAmount}>{krw(item.amount)}원</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
