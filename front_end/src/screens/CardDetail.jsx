import { useEffect, useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A, cardStatsVisible } from '../state/appReducer.js'
import CardFace from '../components/CardFace.jsx'
import { fetchCardDetail, removeCard } from '../api/picka.js'
import { benefitView } from '../utils/benefit.js'
import { krw, krwMinus } from '../utils/format.js'
import styles from './CardDetail.module.css'

/** 상세 상단에 요약으로 보여줄 주요 혜택 개수. 나머지는 전체 혜택 화면에서 봅니다. */
const HIGHLIGHT_COUNT = 3

/** 결제내역이 적어도 이 개수만큼은 자리를 차지하도록 빈 줄로 채웁니다. */
const MIN_TX_ROWS = 3

/** 접힌 상태에서 보여줄 결제내역 개수. 나머지는 '전체보기'로 펼칩니다. */
const TX_PREVIEW = 5

/** 'YYYY.MM.DD' 문자열을 Date 로. 형식이 아니면 null. */
function parseTxDate(text) {
  const parts = String(text || '').split('.').map(Number)
  if (parts.length !== 3 || parts.some(Number.isNaN)) return null
  return new Date(parts[0], parts[1] - 1, parts[2])
}

/** 기준일에서 한 달 뺀 날짜. */
function oneMonthBefore(date) {
  const d = new Date(date)
  d.setMonth(d.getMonth() - 1)
  return d
}

/**
 * 전체보기에서 보여줄 '최근 1달' 결제내역.
 *
 * 가장 최근 결제일을 기준으로 한 달 전까지만 남깁니다. 데모 데이터가
 * 과거 날짜라 '오늘' 기준으로 자르면 목록이 거의 비므로, 실제 데이터의
 * 마지막 한 달을 기준으로 삼아 그보다 오래된 내역만 걸러냅니다.
 *
 * @param {Array} txList 최신순 결제내역
 */
function lastMonthTx(txList) {
  if (txList.length === 0) return txList

  const newest = parseTxDate(txList[0].date)
  if (!newest) return txList // 날짜를 못 읽으면 그대로 둡니다.

  const cutoff = oneMonthBefore(newest)
  return txList.filter((t) => {
    const d = parseTxDate(t.date)
    return d ? d >= cutoff : true
  })
}

/**
 * 실적·한도 막대 한 줄.
 *
 * @param {object} props
 * @param {string} props.label 줄 제목
 * @param {number} props.value 현재 값
 * @param {number} props.total 기준 값
 * @param {boolean} [props.isLimit] 혜택 한도 줄인지. 다 차면 좋은 게 아니라 경고입니다.
 */
function QuotaRow({ label, value, total, isLimit = false, showRemaining = false }) {
  const ratio = total > 0 ? Math.min(value / total, 1) : 0
  const full = total > 0 && value >= total
  const remaining = Math.max(0, total - value)

  let status
  let statusClass
  let fillClass

  if (isLimit) {
    // 한도를 다 쓰면 더 받을 혜택이 없다는 뜻이라 다른 카드를 권합니다.
    status = full ? '한도 달성' : `${krw(remaining)}원 남음`
    statusClass = full ? styles.quotaOver : ''
    fillClass = full ? styles.quotaFillOver : styles.quotaFillLimit
  } else if (showRemaining) {
    // 이번 달 실적 진행 — 목표까지 남은 금액을 안내합니다.
    status = full ? '달성' : `${krw(remaining)}원 남음`
    statusClass = full ? styles.quotaDone : ''
    // 진행 막대는 초록으로 고정합니다.
    fillClass = styles.quotaFillDone
  } else {
    // 전월 실적 — 달성 여부만 이진으로 보여 줍니다 (초록/빨강).
    status = full ? '달성' : '미달성'
    statusClass = full ? styles.quotaDone : styles.quotaMiss
    fillClass = full
      ? styles.quotaFillDone
      : ratio >= 0.5
        ? styles.quotaFillWarn
        : styles.quotaFillDanger
  }

  return (
    <div className={styles.quotaRow}>
      <div className={styles.quotaHead}>
        <span className={styles.quotaLabel}>{label}</span>
        <span className={`${styles.quotaStatus} ${statusClass}`}>{status}</span>
      </div>
      <div className={styles.quotaTrack}>
        <div
          className={`${styles.quotaFill} ${fillClass}`}
          style={{ width: `${ratio * 100}%` }}
        />
      </div>
      <div className={styles.quotaNums}>
        {/* 한도는 다 채우면 거기서 멈춥니다 (한도보다 큰 값이 찍히지 않게). */}
        {krw(isLimit ? Math.min(value, total) : value)}원 / {krw(total)}원
      </div>

      {isLimit && full && (
        <div className={styles.quotaHint}>💡 다른 카드 사용을 추천해요!</div>
      )}
    </div>
  )
}

export default function CardDetail() {
  const { state, dispatch } = useApp()
  const card = state.cards[state.active]
  // 카드 제거는 되돌릴 수 없어 확인 창을 한 번 거칩니다.
  const [confirmRemove, setConfirmRemove] = useState(false)
  const [removing, setRemoving] = useState(false)
  const [txOpen, setTxOpen] = useState(false)
  // 혜택·결제내역은 이 화면에 들어올 때 백엔드에서 받아옵니다.
  const [detail, setDetail] = useState({ card: null, benefits: [], transactions: [] })

  const userId = state.user?.userId
  const cardId = card?.card_id
  // 이 카드의 금액 표시 여부 (카드별 설정 > 전체 설정)
  const statsOn = cardStatsVisible(state, card)

  useEffect(() => {
    if (!userId || !cardId) return undefined
    let cancelled = false
    fetchCardDetail(userId, cardId)
      .then((data) => {
        if (!cancelled) {
          setDetail({ card: data.card, benefits: data.benefits, transactions: data.transactions })
        }
      })
      .catch(() => {
        // 상세를 못 받아도 카드 앞면은 그대로 보여 줍니다.
        if (!cancelled) setDetail({ card: null, benefits: [], transactions: [] })
      })
    return () => {
      cancelled = true
    }
  }, [userId, cardId])

  // 카드를 지운 직후처럼 선택 index가 비면 홈으로 되돌립니다.
  if (!card) return null

  // 실적·한도 숫자는 결제 직후 바뀌므로 상세 응답이 오면 그쪽을 씁니다.
  const usage = detail.card || card
  const required = usage.required_spending || 0
  const benefitLimit = usage.benefit_limit || 0
  const showQuota = required > 0 || benefitLimit > 0

  const benefits = detail.benefits
  const highlights = benefits.slice(0, HIGHLIGHT_COUNT).map(benefitView)
  const allTx = detail.transactions
  // 전체보기는 최근 1달치만, 접힌 상태는 최신 5건만 보여줍니다.
  const monthTx = lastMonthTx(allTx)
  /*
   * 펼쳤을 때 실제로 더 보여줄 게 있을 때만 토글을 답니다.
   * (받아온 건수가 많아도 최근 1달치가 5건 이하면 눌러도 목록이 그대로입니다.)
   */
  const canExpand = monthTx.length > TX_PREVIEW
  const recent = txOpen && canExpand ? monthTx : allTx.slice(0, TX_PREVIEW)
  // 내역이 3건보다 적으면 빈 줄로 채워 목록 높이를 유지합니다.
  const blanks = Math.max(0, MIN_TX_ROWS - recent.length)

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.header}>
        <button
          type="button"
          className={styles.iconBtn}
          aria-label="뒤로"
          onClick={() =>
            state.detailReturn === 'home'
              ? dispatch({ type: A.GO_HOME })
              : dispatch({ type: A.SET_SCREEN, screen: state.detailReturn })
          }
        >
          ‹
        </button>
        <span className={styles.headerTitle}>카드 상세</span>

        <div className={styles.menuWrap}>
          <button
            type="button"
            className={styles.iconBtn}
            aria-label="카드 메뉴"
            aria-expanded={state.menuOpen}
            onClick={() => dispatch({ type: A.SET_MENU, open: !state.menuOpen })}
          >
            ⋯
          </button>

          {state.menuOpen && (
            <>
              {/* 메뉴 밖 아무 곳이나 누르면 닫히도록 화면 전체를 덮는 투명 레이어 */}
              <div
                className={styles.menuBackdrop}
                onClick={() => dispatch({ type: A.SET_MENU, open: false })}
              />
              <div className={`${styles.menu} pk-anim-pop-ease`}>
              {/* 이 카드에만 적용되는 금액 표시 설정입니다. */}
              <div className={styles.menuItem}>
                <span>💰 금액 표시</span>
                <span className={styles.menuSwitch}>
                  <button
                    type="button"
                    className={`${styles.menuSwitchBtn} ${statsOn ? styles.menuSwitchOn : ''}`}
                    aria-pressed={statsOn}
                    onClick={() =>
                      dispatch({ type: A.SET_CARD_STATS_FOR, cardId, show: true })
                    }
                  >
                    ON
                  </button>
                  <button
                    type="button"
                    className={`${styles.menuSwitchBtn} ${statsOn ? '' : styles.menuSwitchOn}`}
                    aria-pressed={!statsOn}
                    onClick={() =>
                      dispatch({ type: A.SET_CARD_STATS_FOR, cardId, show: false })
                    }
                  >
                    OFF
                  </button>
                </span>
              </div>
              <button
                type="button"
                className={`${styles.menuItem} ${styles.danger}`}
                onClick={() => {
                  dispatch({ type: A.SET_MENU, open: false })
                  setConfirmRemove(true)
                }}
              >
                🗑️ 카드 제거
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      <div className={styles.cardWrap}>
        <CardFace
          card={card}
          variant="detail"
          spent={card.spent}
          benefit={card.benefit}
          expiry={card.expiry}
          showStats={statsOn}
        />
      </div>

      {showQuota && (
        <div className={styles.quotaPanel}>
          <div className={styles.quotaTitle}>실적 · 혜택 한도</div>

          {required > 0 ? (
            <>
              <QuotaRow
                label="전월 실적 달성"
                value={usage.previous_month_spending || 0}
                total={required}
              />
              <QuotaRow
                label="이번 달 실적 진행"
                value={usage.current_month_spending || 0}
                total={required}
                showRemaining
              />
            </>
          ) : (
            <div className={styles.quotaNote}>전월 실적 조건이 없는 카드예요.</div>
          )}

          {benefitLimit > 0 && (
            <QuotaRow
              label="월 혜택 한도"
              value={usage.benefit_used || 0}
              total={benefitLimit}
              isLimit
            />
          )}
        </div>
      )}

      <div className={styles.sectionHead}>
        <span className={styles.sectionTitle}>주요 혜택</span>
        {benefits.length > 0 && (
          <button
            type="button"
            className={styles.moreBtn}
            onClick={() => dispatch({ type: A.OPEN_BENEFITS, source: 'owned' })}
          >
            전체보기
          </button>
        )}
      </div>

      <div className={styles.list}>
        {highlights.length === 0 && (
          <div className={styles.empty}>등록된 상세 혜택 정보가 없어요.</div>
        )}

        {highlights.map((b) => (
          <div key={b.id} className={styles.benefitRow}>
            <div className={styles.icon} style={{ background: b.tint }}>
              {b.icon}
            </div>
            <div className={styles.benefitBody}>
              <div className={styles.benefitHead}>
                <span className={styles.benefitTitle}>{b.title}</span>
                <span className={styles.benefitRate}>{b.rate}</span>
              </div>
              <div className={styles.benefitDesc}>{b.desc}</div>
            </div>
          </div>
        ))}
      </div>

      <div className={styles.sectionHead}>
        <span className={styles.sectionTitle}>최근 결제내역</span>
        {canExpand && (
          <button
            type="button"
            className={styles.moreBtn}
            aria-expanded={txOpen}
            onClick={() => setTxOpen((v) => !v)}
          >
            {txOpen ? '접기' : '전체보기'}
          </button>
        )}
      </div>

      <div className={styles.txPanel}>
        {recent.map((t) => (
          <div key={t.id} className={styles.txRow}>
            <div className={styles.icon} style={{ background: '#f4f6fa' }}>
              {t.icon}
            </div>
            <div className={styles.txBody}>
              <div className={styles.txPlace}>{t.place}</div>
              <div className={styles.txMeta}>
                <span className={styles.txTag}>{t.category}</span>
                <span className={styles.txDate}>{t.date}</span>
              </div>
            </div>
            <div className={styles.txAmountBox}>
              <div className={styles.txAmount}>{krwMinus(t.amount)}원</div>
              <div className={styles.txSaved}>{t.saved}</div>
            </div>
          </div>
        ))}

        {Array.from({ length: blanks }, (_, i) => (
          <div key={`blank-${i}`} className={`${styles.txRow} ${styles.txBlank}`}>
            <div className={styles.icon} style={{ background: '#f4f6fa' }} />
            <div className={styles.txBody}>
              <div className={styles.txPlace}>
                {recent.length === 0 && i === 0 ? '아직 결제내역이 없어요.' : ''}
              </div>
            </div>
          </div>
        ))}
      </div>

      {confirmRemove && (
        <div className={styles.confirmDim} onClick={() => setConfirmRemove(false)}>
          <div
            className={`${styles.confirm} pk-anim-pop-ease`}
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="remove-card-title"
            onClick={(e) => e.stopPropagation()}
          >
            <div className={styles.confirmIcon}>🗑️</div>
            <div className={styles.confirmTitle} id="remove-card-title">
              정말로 카드를 삭제하시겠습니까?
            </div>
            <div className={styles.confirmSub}>
              {card.card_company} {card.card_name} · {card.last_four}
              <br />
              삭제하면 결제 추천 대상에서 제외됩니다.
            </div>
            <div className={styles.confirmActions}>
              <button
                type="button"
                className={styles.confirmCancel}
                onClick={() => setConfirmRemove(false)}
              >
                취소
              </button>
              <button
                type="button"
                className={styles.confirmDelete}
                disabled={removing}
                onClick={async () => {
                  if (removing) return
                  setRemoving(true)
                  try {
                    await removeCard(userId, cardId)
                  } catch {
                    // 서버에서 실패해도 화면에서는 목록을 갱신해 흐름을 막지 않습니다.
                  }
                  dispatch({ type: A.REMOVE_CARD, index: state.active })
                }}
              >
                삭제
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
