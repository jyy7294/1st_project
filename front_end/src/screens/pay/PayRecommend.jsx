import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import {
  orderedComparison,
  needsManualSelection,
  isPerformanceOnly,
  displayCategory,
} from '../../utils/compare.js'
import { gradientForCard } from '../../data/cards.js'
import { cardImage } from '../../data/cardImages.js'
import CardArt from '../../components/CardArt.jsx'
import CardFace from '../../components/CardFace.jsx'
import { krw, krwMinus } from '../../utils/format.js'
import shared from './payShared.module.css'
import styles from './PayRecommend.module.css'

/** 이만큼 끌면 반대 상태(내림/올림)로 붙습니다. */
const SNAP = 44

/** 이보다 적게 움직였으면 끌기가 아니라 탭으로 봅니다. */
const TAP_SLOP = 6

/*
 * 실적 기준 추천 문구.
 *
 * 백엔드 문구는 '전월 실적'이라고 하는데, 전월 실적은 이미 확정된 값이라
 * 이번 결제로 바뀌지 않습니다. 이번 결제가 쌓이는 건 '이번 달 실적'이므로
 * 화면에서는 그 기준으로 말합니다.
 */
/** 목표까지 이 금액 이하로 남으면 '얼마 안 남았다'고 알려 줍니다. */
const NEAR_TARGET = 10000

const PERFORMANCE_LEAD = '즉시 적용 가능한 혜택이 없어 실적 달성에 유리한 카드를 추천했습니다.'
const PERFORMANCE_REASON =
  '이번 결제에 적용할 혜택은 없지만, 이번 달 실적을 채우는 데 가장 유리한 카드예요.'

export default function PayRecommend() {
  const { state, dispatch } = useApp()
  const { transaction, result, error, noEligibleCard, payIdx } = state

  const ranked = orderedComparison(result?.comparison)
  const selectedIdx = payIdx < ranked.length ? payIdx : 0
  const chosen = ranked[selectedIdx] || null
  const amount = transaction?.payment_amount || 0
  const discount = chosen?.expected_benefit || 0
  // 업종은 백엔드가 가맹점명으로 판정한 값을 씁니다.
  const category = displayCategory(result, transaction)

  // 즉시 혜택은 없지만 실적에 유리한 카드를 추천한 경우 — 추천을 그대로 보여줍니다.
  const performanceOnly = isPerformanceOnly(result)

  /*
   * 이번 결제가 실제로 쌓이는 값은 '이번 달 사용액'입니다.
   * (백엔드 performance_after_payment 는 전월 실적에 결제액을 더해 주므로 쓰지 않습니다.)
   */
  const monthTarget = chosen?.required_spending ?? chosen?.performance_required ?? 0
  const monthAfterPay = (chosen?.current_month_spending ?? 0) + amount
  // 이 카드로 결제했다고 볼 때 목표까지 남는 금액
  const monthRemainAfter = Math.max(0, monthTarget - monthAfterPay)
  // 이번 결제로 목표를 채우는지 / 목표가 코앞인지
  const willReachTarget = monthTarget > 0 && monthAfterPay >= monthTarget
  const almostThere =
    monthTarget > 0 && !willReachTarget && monthRemainAfter <= NEAR_TARGET
  // 혜택도 실적도 나을 게 없어 직접 골라야 하는 경우에만 "직접 선택" 화면입니다.
  const mustSelect = needsManualSelection(result, noEligibleCard)

  // '다른 카드로 결제하기' 시트를 잡아 내리면 뒤의 할인 혜택·최종 승인 금액이 보입니다.
  const sheetRef = useRef(null)
  const headRef = useRef(null)
  const dragStart = useRef(null)

  /*
   * 추천 카드가 없을 때(혜택 카드 없음·오류)는 카드를 직접 골라야 하므로
   * 시트를 펼친 채로 시작합니다. 추천 카드가 있으면 추천 내용이 먼저
   * 보이도록 내려두고, '다른 카드 선택하기' 버튼으로 다시 올립니다.
   */
  const sheetOpenAtStart = !chosen || !!error || mustSelect
  const [lowered, setLowered] = useState(!sheetOpenAtStart)

  /*
   * 올라오는 등장 애니메이션은 펼친 채로 시작할 때만 씁니다.
   * 내려둔 채로 시작하면 애니메이션이 inline transform 을 눌러
   * 시트가 끝까지 올라왔다가 다시 내려가는 게 보입니다.
   */
  const enterAnim = useRef(sheetOpenAtStart).current
  const [maxOffset, setMaxOffset] = useState(0)
  const [dragOffset, setDragOffset] = useState(null)

  // 추천 결과가 늦게 도착해 상황이 바뀌면 시작 상태를 다시 맞춥니다.
  useEffect(() => {
    if (sheetOpenAtStart) setLowered(false)
  }, [sheetOpenAtStart])

  // 내려도 손잡이(제목 줄)는 남겨서 다시 올릴 수 있게 합니다.
  useLayoutEffect(() => {
    const sheet = sheetRef.current
    const head = headRef.current
    if (!sheet || !head) return
    setMaxOffset(Math.max(0, sheet.offsetHeight - head.offsetHeight))
  }, [ranked.length])

  const offset = dragOffset != null ? dragOffset : lowered ? maxOffset : 0

  function onPointerDown(e) {
    if (e.pointerType === 'mouse' && e.button !== 0) return
    dragStart.current = { y: e.clientY, base: lowered ? maxOffset : 0 }
    setDragOffset(dragStart.current.base)
    e.currentTarget.setPointerCapture(e.pointerId)
  }

  function onPointerMove(e) {
    if (!dragStart.current) return
    const next = dragStart.current.base + (e.clientY - dragStart.current.y)
    setDragOffset(Math.min(Math.max(next, 0), maxOffset))
  }

  function onPointerUp() {
    if (!dragStart.current) return
    const { base } = dragStart.current
    const moved = (dragOffset ?? base) - base
    dragStart.current = null
    setDragOffset(null)

    // 손잡이를 그냥 탭하면 내려둔 시트를 다시 올립니다 (위로 스와이프 대신).
    if (Math.abs(moved) < TAP_SLOP) {
      if (lowered) setLowered(false)
      return
    }

    // 내려간 상태면 위로, 올라간 상태면 아래로 SNAP 이상 움직였을 때만 전환합니다.
    if (Math.abs(moved) > SNAP) setLowered(moved > 0)
  }

  function retry() {
    // 분석 화면으로 되돌리면 추천 API가 다시 호출됩니다.
    dispatch({ type: A.SET_PAY_STEP, payStep: 'analyzing' })
  }

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={`${styles.scroll} ${lowered ? styles.scrollLow : ''}`}>
        <div className={`${shared.brandRow} ${shared.end}`}>
          picka
        </div>

        {error && <ErrorNotice message={error} onRetry={retry} />}

        {mustSelect && !error && (
          <div className={styles.notice}>
            <div className={styles.noticeIcon}>💡</div>
            <div className={styles.noticeTitle}>이 업종에 해당하는 혜택 카드가 없어요</div>
            <div className={styles.noticeBody}>
              {category} 업종에 적용되는 혜택이 없습니다.
              <br />
              원하시는 카드로 결제하세요.
            </div>
          </div>
        )}

        {chosen && !error && !mustSelect && (
          <>
            <div className={styles.badgeRow}>
              <span className={styles.badge}>
                {performanceOnly ? '📈 PERFORMANCE PICK' : '✦ SMART SUGGESTION'}
              </span>
            </div>

            <div className={styles.title}>
              {performanceOnly ? '실적 달성 추천 카드' : 'AI 추천 카드'}
            </div>

            {/* 혜택 기준 추천은 백엔드 문구를 그대로 쓰고,
                실적 기준 추천만 이번 결제가 쌓이는 '이번 달 실적' 기준으로 다시 씁니다. */}
            <div className={styles.lead}>
              {performanceOnly ? (
                PERFORMANCE_LEAD
              ) : (
                result?.saving_message || (
                  <>
                    {chosen.card_company}가 {category}에서
                    {' '}
                    {/* 실제 할인액으로 말합니다. benefit_rate 는 정률·정액이 섞여 있어
                        '%'를 붙이면 1,000원 할인이 '1000% 할인'이 됩니다. */}
                    {discount > 0 ? `${krw(discount)}원 할인` : '가장 큰 혜택'}으로
                    <br />
                    혜택이 가장 좋아요. 이 카드로 결제할까요?
                  </>
                )
              )}
            </div>

            {/* 지갑과 같은 카드 앞면 — 실물 카드 사진이 있으면 그대로 씁니다. */}
            <div className={styles.bigCard}>
              <CardFace card={chosen} variant="detail" showStats={false} />
            </div>

            <div className={styles.stats}>
              {performanceOnly ? (
                <div className={styles.stat}>
                  <div className={styles.statLabel}>📈 이번 달 남은 실적</div>
                  <div className={`${styles.statValue} ${styles.perf}`}>
                    {krw(monthRemainAfter)}원
                  </div>
                  <div className={styles.statNote}>목표 {krw(monthTarget)}원</div>
                </div>
              ) : (
                <div className={styles.stat}>
                  <div className={styles.statLabel}>🏷 할인 혜택</div>
                  <div className={`${styles.statValue} ${styles.good}`}>
                    {krwMinus(discount)}원
                  </div>
                  <div className={styles.statNote}>{category}</div>
                </div>
              )}
              <div className={styles.stat}>
                <div className={styles.statLabel}>최종 승인 금액</div>
                <div className={`${styles.statValue} ${styles.plain}`}>
                  {krw(amount - discount)}원
                </div>
                <div className={styles.statNote}>정가 {krw(amount)}원</div>
              </div>
            </div>

            {/* 실적이 채워지거나 코앞일 때만 짧게 짚어 줍니다. */}
            {performanceOnly && (willReachTarget || almostThere) && (
              <div
                className={`${styles.perfHint} ${willReachTarget ? styles.perfHintDone : ''}`}
              >
                {willReachTarget
                  ? '🎉 이 카드를 쓰면 이번 달 실적을 채울 수 있어요!'
                  : '🔥 실적 달성까지 얼마 남지 않았어요!'}
              </div>
            )}

            <div className={styles.reason}>
              <span style={{ fontSize: 15 }}>💡</span>
              <span className={styles.reasonText}>
                추천 이유 · {performanceOnly ? PERFORMANCE_REASON : chosen.reason}
              </span>
            </div>

            {/*
              시트를 내려둔 동안에는 시트 안의 버튼이 화면 밖으로 나가므로
              여기에 같은 동작을 두고, 손잡이를 찾지 않아도 목록을 다시 열 수 있게 합니다.
            */}
            {lowered && (
              <div className={styles.actions}>
                <button
                  type="button"
                  className={shared.primaryBtn}
                  onClick={() => dispatch({ type: A.SET_PAY_STEP, payStep: 'confirm' })}
                >
                  이 카드로 결제
                </button>
                <button
                  type="button"
                  className={styles.pickOther}
                  onClick={() => setLowered(false)}
                >
                  다른 카드 선택하기
                </button>
              </div>
            )}
          </>
        )}
      </div>

      <div className={`${styles.scrim} ${lowered ? styles.scrimOff : ''}`} />

      <div
        ref={sheetRef}
        className={`${styles.sheet} ${enterAnim ? 'pk-anim-up' : ''}`}
        style={{
          transform: offset ? `translateY(${offset}px)` : undefined,
          transition: dragOffset != null ? 'none' : undefined,
        }}
      >
        <div
          ref={headRef}
          className={`${styles.sheetHead} ${lowered ? styles.sheetHeadRaise : ''}`}
          role={lowered ? 'button' : undefined}
          aria-label={lowered ? '카드 목록 다시 열기' : undefined}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
        >
          <div className={styles.grabber} />
          <div className={styles.sheetTitle}>다른 카드로 결제하기</div>
          <div className={styles.sheetSub}>
            추천 순서대로 정렬했어요. 원하는 카드를 선택하세요.
          </div>
        </div>

        <div className={styles.sheetList}>
          {ranked.map((card, i) => (
            <div
              key={card.card_id}
              className={[
                styles.row,
                i === selectedIdx ? styles.selected : '',
                card.eligible ? '' : styles.dim,
              ].join(' ')}
              onClick={() => dispatch({ type: A.SELECT_PAY_CARD, index: i })}
            >
              <span className={styles.rank}>{i + 1}</span>
              <div
                className={styles.swatch}
                style={{ background: gradientForCard(card) }}
              >
                <CardArt src={cardImage(card)} frame="landscape" />
              </div>
              <div className={styles.rowMain}>
                <div className={styles.rowName}>
                  {card.card_company} {card.card_name}
                </div>
                <div className={styles.rowSub}>
                  {card.eligible
                    ? `할인 -${krw(card.expected_benefit)}원`
                    : '적용 가능한 혜택 없음'}
                </div>
              </div>
              <div className={styles.rowRight}>
                <div className={styles.rowAmount}>
                  {krw(amount - (card.expected_benefit || 0))}원
                </div>
                <div className={styles.rowNote}>결제 예상</div>
              </div>
            </div>
          ))}
        </div>

        <div className={styles.sheetFoot}>
          <button
            type="button"
            className={shared.primaryBtn}
            disabled={!chosen}
            onClick={() => dispatch({ type: A.SET_PAY_STEP, payStep: 'confirm' })}
          >
            이 카드로 결제
          </button>
          <button
            type="button"
            className={shared.ghostBtn}
            onClick={() => dispatch({ type: A.RESET_PAY })}
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    </div>
  )
}

function ErrorNotice({ message, onRetry }) {
  return (
    <div className={styles.notice}>
      <div className={styles.noticeIcon}>⚠️</div>
      <div className={styles.noticeTitle}>추천을 불러오지 못했어요</div>
      <div className={styles.noticeBody}>{message}</div>
      <button type="button" className={styles.retry} onClick={onRetry}>
        다시 시도
      </button>
    </div>
  )
}
