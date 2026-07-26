import { useEffect, useMemo, useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { gradientForCard } from '../data/cards.js'
import { cardImage } from '../data/cardImages.js'
import CardArt from '../components/CardArt.jsx'
import { recentMonths } from '../data/report.js'
import { fetchSpendingReport } from '../api/picka.js'
import { adaptSpendingReport } from '../api/adapters.js'
import { buildBarAxis, buildDonut, buildSpendChart, daysInMonth } from '../utils/report.js'
import { krw } from '../utils/format.js'
import styles from './Report.module.css'

/**
 * 월별 소비 리포트. 결제수단 관리의 요약/문구 바에서 들어옵니다.
 * 로그인한 페르소나의 실제 결제내역을 백엔드에서 집계해 보여줍니다.
 */
export default function Report() {
  const { state, dispatch } = useApp()
  // 탭 목록은 렌더마다 새로 만들지 않습니다 (아래 조회 effect 가 매번 돌지 않도록).
  const months = useMemo(() => recentMonths(), [])
  const monthIdx = Math.min(state.reportMonth, months.length - 1)
  const active = months[monthIdx]
  const monthKey = active.key

  const userId = state.user?.userId
  const raw = state.reportData[monthKey]
  // 막대를 두 번 누르면 그 달의 일별 추이(선 그래프)를 보여줍니다. null 이면 막대 보기.
  const [lineMonth, setLineMonth] = useState(null)

  // 막대 그래프에 3개월이 모두 필요하므로 아직 못 받은 달을 한 번에 받아옵니다.
  useEffect(() => {
    if (!userId) return undefined
    const missing = months.filter((m) => !state.reportData[m.key])
    if (missing.length === 0) return undefined

    let cancelled = false
    dispatch({ type: A.SET_REPORT_STATUS, status: 'loading' })
    Promise.all(
      missing.map((m) =>
        fetchSpendingReport(userId, m.key)
          .then((data) => ({ month: m.key, data }))
          .catch(() => null),
      ),
    ).then((results) => {
      if (cancelled) return
      const ok = results.filter(Boolean)
      if (ok.length === 0) {
        dispatch({ type: A.SET_REPORT_STATUS, status: 'error' })
        return
      }
      ok.forEach(({ month, data }) =>
        dispatch({ type: A.SET_REPORT_DATA, month, report: data }),
      )
    })
    return () => {
      cancelled = true
    }
  }, [userId, months, state.reportData, dispatch])

  const loading = !raw && state.reportStatus !== 'error'
  const errored = !raw && state.reportStatus === 'error'

  const report = raw ? adaptSpendingReport(raw, active.label) : null
  // X축은 그 달의 실제 일수만큼만 그립니다 (6월 30일, 2월 28일 …).
  const chart = report
    ? buildSpendChart(report.daily, report.prevDaily, {
        days: daysInMonth(report.month),
        prevDays: daysInMonth(report.prevMonth || report.month),
      })
    : null
  const donut = report ? buildDonut(report.categories) : null

  // 혜택이 큰 카드부터. 리포트 응답의 cardBenefits 를 그대로 씁니다.
  const rankedCards = report ? [...report.cards].sort((a, b) => b.benefit - a.benefit) : []
  const maxBenefit = Math.max(1, ...rankedCards.map((r) => r.benefit))

  const prevLabel = months[monthIdx - 1]?.label

  // 3개월 막대 그래프 — 받아둔 달만 값이 채워집니다.
  const bars = months.map((m) => ({
    ...m,
    spent: state.reportData[m.key]?.totalSpending || 0,
  }))
  const maxSpent = Math.max(1, ...bars.map((b) => b.spent))
  // Y축 눈금. 막대 높이도 이 상한(yMax)에 맞춰야 눈금선과 맞습니다.
  const barAxis = buildBarAxis(maxSpent)

  // 지난달 대비 증감률 (지난달 지출이 있을 때만)
  const diffPct =
    report && report.prevSpent > 0
      ? Math.round((Math.abs(report.spentDiff) / report.prevSpent) * 100)
      : null

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
        <span className={styles.headerTitle}>소비 리포트</span>
        <span className={styles.spacer} />
      </div>

      <div className={styles.tabs}>
        {months.map((month, i) => (
          <button
            key={month.key}
            type="button"
            className={`${styles.tab} ${i === monthIdx ? styles.tabActive : ''}`}
            onClick={() => dispatch({ type: A.SET_REPORT_MONTH, index: i })}
          >
            {month.label}
          </button>
        ))}
      </div>

      {loading && <div className={styles.stateBox}>소비 내역을 불러오는 중…</div>}
      {errored && <div className={styles.stateBox}>리포트를 불러오지 못했어요.</div>}

      {report && (
        <>
          {/* 이번 달 지출 + 누적 곡선 */}
          <section className={styles.panel}>
            <div className={styles.panelLabel}>{report.key} 지출</div>
            <div className={styles.bigNumber}>
              {krw(report.spent)}
              <span className={styles.bigUnit}>원</span>
            </div>
            <div className={styles.compare}>
              지난달 대비{' '}
              {report.hasPrev ? (
                <span
                  className={styles.compareValue}
                  style={{ color: report.spentDiff <= 0 ? 'var(--green-chart)' : 'var(--danger)' }}
                >
                  {report.spentDiff <= 0 ? '▼' : '▲'}
                  {krw(Math.abs(report.spentDiff))}원
                  {diffPct !== null && ` (${diffPct}%)`}
                  {report.spentDiff <= 0 ? ' 덜 썼어요' : ' 더 썼어요'}
                </span>
              ) : (
                <span className={styles.compareValue}>비교할 지난달 데이터가 없어요</span>
              )}
            </div>

            {!lineMonth ? (
              /* 3개월 지출 막대 — 한눈에 비교하고, 두 번 누르면 일별 추이로 */
              <>
                <div className={styles.axisUnit}>(만원)</div>

                <div className={styles.plot}>
                  {/* Y축 눈금선 + 값 */}
                  {barAxis.ticks.map((t) => (
                    <span key={t.won} className={styles.gridLine} style={{ bottom: `${t.pct}%` }}>
                      <span className={styles.gridLabel}>{t.label}</span>
                    </span>
                  ))}
                  {/* X축 (0 기준선) */}
                  <span className={styles.baseLine}>
                    <span className={styles.gridLabel}>0</span>
                  </span>

                  <div className={styles.barRow}>
                    {bars.map((b, i) => (
                      <button
                        key={b.key}
                        type="button"
                        className={`${styles.barCol} ${i === monthIdx ? styles.barColOn : ''}`}
                        onClick={() => dispatch({ type: A.SET_REPORT_MONTH, index: i })}
                        onDoubleClick={() => {
                          dispatch({ type: A.SET_REPORT_MONTH, index: i })
                          setLineMonth(b.key)
                        }}
                      >
                        <span className={styles.barAmount}>
                          {b.spent > 0 ? `${krw(Math.round(b.spent / 10000))}만` : '-'}
                        </span>
                        <span
                          className={styles.barValue}
                          style={{ height: `${(b.spent / barAxis.yMax) * 100}%` }}
                        />
                      </button>
                    ))}
                  </div>
                </div>

                {/* X축 눈금 (달) */}
                <div className={styles.xLabels}>
                  {bars.map((b, i) => (
                    <span
                      key={b.key}
                      className={`${styles.xLabel} ${i === monthIdx ? styles.xLabelOn : ''}`}
                    >
                      {b.label}
                    </span>
                  ))}
                </div>

                <div className={styles.barHint}>막대를 두 번 누르면 일별 추이를 볼 수 있어요</div>
              </>
            ) : (
              <>
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
              <span>{chart.lastDayLabel}</span>
            </div>

            <div className={styles.legend}>
              <div className={styles.legendRow}>
                <span className={styles.legendName}>
                  <span className={styles.legendDashCur} />
                  {report.key}
                </span>
                <span className={styles.legendCur}>{krw(report.spent)}원</span>
              </div>
              {report.hasPrev && (
                <div className={styles.legendRow}>
                  <span className={styles.legendName}>
                    <span className={styles.legendDashPrev} />
                    {prevLabel || '지난달'}
                  </span>
                  <span className={styles.legendPrev}>{krw(report.prevSpent)}원</span>
                </div>
              )}
            </div>

                <button
                  type="button"
                  className={styles.backToBars}
                  onClick={() => setLineMonth(null)}
                >
                  ‹ 월별 비교로 돌아가기
                </button>
              </>
            )}
          </section>

          {/* 카드별 혜택 */}
          <section className={styles.panel}>
            <div className={styles.savedBox}>
              <div className={styles.savedLabel}>{report.key} 챙긴 혜택</div>
              <div className={styles.savedValue}>
                {krw(report.benefit)}
                <span className={styles.savedUnit}>원</span>
              </div>
              <div className={styles.insight}>
                <span>💡</span>
                <span>
                  {!report.hasPrev
                    ? `${report.key}에 받은 혜택이에요.`
                    : report.benefitDiff >= 0
                      ? `${report.key}에는 지난달보다 혜택을 ${krw(report.benefitDiff)}원 더 받았어요!`
                      : `${report.key}에는 지난달보다 혜택이 ${krw(-report.benefitDiff)}원 줄었어요.`}
                </span>
              </div>
            </div>

            <div className={styles.sectionHead}>
              <span className={styles.sectionTitle}>카드별 혜택</span>
            </div>

            <div className={styles.cardList}>
              {rankedCards.length === 0 && (
                <div className={styles.empty}>이 달에 받은 카드 혜택이 없어요.</div>
              )}

              {rankedCards.map((c, rank) => {
                const pseudo = { card_id: c.cardId, card_name: c.name, card_company: c.company }
                return (
                  <div key={c.cardId} className={styles.cardItem}>
                    <span className={styles.cardHead}>
                      <span className={styles.cardName}>
                        <span
                          className={styles.cardSwatch}
                          style={{ background: gradientForCard(pseudo) }}
                        >
                          <CardArt src={cardImage(pseudo)} frame="landscape" />
                        </span>
                        {c.company} · {c.name}
                      </span>
                      <span className={styles.cardRight}>
                        <span
                          className={styles.cardBenefit}
                          style={{ color: rank === 0 ? 'var(--teal-deep)' : 'var(--navy-text)' }}
                        >
                          {krw(c.benefit)}원
                        </span>
                      </span>
                    </span>

                    <span className={styles.bar}>
                      <span
                        className={styles.barFill}
                        style={{
                          width: `${(c.benefit / maxBenefit) * 100}%`,
                          background: gradientForCard(pseudo),
                        }}
                      />
                    </span>

                    {rank === 0 && c.benefit > 0 && (
                      <span className={styles.best}>🏆 {report.key} 최대 혜택 카드</span>
                    )}
                  </div>
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
                  <div className={styles.donutCenterText}>
                    <span className={styles.donutTopName}>{donut.topName}</span>
                    <span className={styles.donutTopPct} style={{ color: donut.topColor }}>
                      {donut.topPercent}
                    </span>
                  </div>
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

            {/* '기타'가 뭔지 몰라 헷갈리지 않도록 어떤 지출이 묶이는지 밝혀 둡니다. */}
            {donut.items.some((item) => item.name === '기타') && (
              <div className={styles.catNote}>
                기타는 위 분류에 속하지 않는 지출이에요 · 간편결제, 해외결제, 멤버십·포인트 등
              </div>
            )}
          </section>
        </>
      )}
    </div>
  )
}
