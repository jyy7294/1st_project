import { useEffect, useRef, useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A, cardStatsVisible } from '../state/appReducer.js'
import { fetchMyCards } from '../api/picka.js'
import CardFace from '../components/CardFace.jsx'
import PickaLogo from '../components/PickaLogo.jsx'
import styles from './WalletHome.module.css'

/** 이만큼 끌어올리면 완전히 접힙니다. 그 사이는 손을 따라 서서히 접힙니다. */
const COLLAPSE_TRAVEL = 260

/** 손을 뗐을 때 이 비율을 넘겼으면 접고, 아니면 원래대로 되돌립니다. */
const COLLAPSE_SNAP = 0.45

/** 이 거리 이상 움직이면 탭이 아니라 스와이프로 봅니다. */
const DRAG_SLOP = 8

// 카드 폭 360px(화면 404 − 좌우 여백 44)에 실물 카드 비율을 적용한 높이
const CARD_HEIGHT = Math.round(360 / (85.6 / 54))
const OFFSET_COLLAPSED = 54 // 접힌 카드 간격
const OFFSET_EXPANDED = CARD_HEIGHT - 10 // 펼친 카드 간격 (10px 만 겹칩니다)

export default function WalletHome() {
  const { state, dispatch } = useApp()
  const { cards, expanded, active, cardsLoaded, showCardStats, user } = state

  // 헤더 ☰ 더보기 메뉴(카드 관리·로그아웃)와 로그아웃 확인 팝업.
  const [moreOpen, setMoreOpen] = useState(false)
  const [confirmLogout, setConfirmLogout] = useState(false)

  // 보유카드는 화면 진입 시 한 번만 불러옵니다.
  // (카드를 모두 지웠을 때 다시 불러오지 않도록 개수가 아니라 로드 여부로 판단합니다.)
  useEffect(() => {
    if (cardsLoaded || !user?.userId) return
    let cancelled = false
    fetchMyCards(user.userId)
      .then((list) => {
        if (!cancelled) dispatch({ type: A.SET_CARDS, cards: list })
      })
      .catch((err) => {
        // 보유카드를 못 불러와도 앱은 계속 동작합니다. 지갑은 빈 상태로 둡니다.
        if (!cancelled) {
          dispatch({ type: A.SET_CARDS_ERROR, message: err?.message || '보유카드를 불러오지 못했습니다.' })
        }
      })
    return () => {
      cancelled = true
    }
  }, [cardsLoaded, user?.userId, dispatch])

  // 펼친 카드 뭉치를 위로 스와이프하면 접습니다. 아래 안내 문구 버튼은 그대로 둡니다.
  const drag = useRef(null)
  const swiped = useRef(false)
  // 손을 댄 카드 index. 끌기 시작하면 이 카드가 '잡힌' 상태가 됩니다.
  const pressed = useRef(-1)
  // 끌어올린 정도 0~1. 손을 따라 카드 간격이 좁아집니다. null 이면 드래그 중이 아님.
  const [progress, setProgress] = useState(null)
  // 잡고 있는 카드 index. 손을 대면 살짝 커져서 '잡혔다'는 게 보입니다.
  const [grabbed, setGrabbed] = useState(-1)
  // 손을 뗄 때 참조할 최신 진행도. state 는 이벤트 핸들러에 늦게 반영됩니다.
  const progressRef = useRef(0)

  const dragging = progress !== null

  function onPointerDown(e) {
    if (!expanded) return
    if (e.pointerType === 'mouse' && e.button !== 0) return
    drag.current = { y: e.clientY }
    swiped.current = false
    progressRef.current = 0
    setProgress(0)
  }

  /*
   * 끌기 중에는 window 에서 좌표를 받습니다.
   *
   * 카드 뭉치에만 핸들러를 두면 손이 뭉치 밖(위쪽 QR 바 등)으로 나가는 순간
   * pointermove 가 끊겨 카드가 따라오다 멈추고, pointerup 도 밖에서 일어나
   * 끌기 상태가 풀리지 않습니다. 위로 260px 을 끌어야 접히는 동작이라
   * 뭉치를 벗어나는 일이 실제로 자주 생깁니다.
   */
  useEffect(() => {
    if (!dragging) return undefined

    function move(e) {
      if (!drag.current) return
      const up = drag.current.y - e.clientY
      if (up > DRAG_SLOP) {
        swiped.current = true
        setGrabbed((current) => (current === pressed.current ? current : pressed.current))
      }
      // 위로 끈 거리를 0~1 로 바꿔 카드 간격에 그대로 반영합니다.
      const next = Math.max(0, Math.min(up / COLLAPSE_TRAVEL, 1))
      progressRef.current = next
      setProgress(next)
    }

    function end() {
      setGrabbed(-1)
      pressed.current = -1
      if (!drag.current) return
      const reached = progressRef.current >= COLLAPSE_SNAP
      drag.current = null
      setProgress(null)
      if (reached) dispatch({ type: A.TOGGLE_EXPANDED })
    }

    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', end)
    window.addEventListener('pointercancel', end)
    return () => {
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', end)
      window.removeEventListener('pointercancel', end)
    }
  }, [dragging, dispatch])

  // 드래그 중에는 펼친 간격 → 접힌 간격 사이를 손 위치대로 오갑니다.
  const offset = expanded
    ? OFFSET_EXPANDED + (OFFSET_COLLAPSED - OFFSET_EXPANDED) * (progress ?? 0)
    : OFFSET_COLLAPSED
  const stackHeight = cards.length
    ? (cards.length - 1) * offset + CARD_HEIGHT + 8
    : 0

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.header}>
        <div className={styles.brand}>
          <PickaLogo height={30} />
        </div>
        <div className={styles.headerActions}>
          <button
            type="button"
            className={styles.iconBtn}
            aria-label="카드 등록"
            onClick={() => dispatch({ type: A.START_ADD })}
          >
            +
          </button>
          <div className={styles.menuWrap}>
            <button
              type="button"
              className={`${styles.iconBtn} ${styles.light}`}
              aria-label="더보기"
              aria-expanded={moreOpen}
              onClick={() => setMoreOpen((v) => !v)}
            >
              ☰
            </button>

            {moreOpen && (
              <>
                {/* 메뉴 밖 아무 곳이나 누르면 닫히도록 화면 전체를 덮는 투명 레이어 */}
                <div className={styles.menuBackdrop} onClick={() => setMoreOpen(false)} />
                <div className={`${styles.menu} pk-anim-pop-ease`}>
                  <button
                    type="button"
                    className={styles.menuItem}
                    onClick={() => {
                      setMoreOpen(false)
                      dispatch({ type: A.SET_SCREEN, screen: 'cards' })
                    }}
                  >
                    <span className={styles.menuIcon}>💳</span>
                    카드 관리
                  </button>
                  <button
                    type="button"
                    className={styles.menuItem}
                    onClick={() => {
                      setMoreOpen(false)
                      dispatch({ type: A.SET_SCREEN, screen: 'report' })
                    }}
                  >
                    <span className={styles.menuIcon}>📊</span>
                    소비리포트 보기
                  </button>
                  <button
                    type="button"
                    className={`${styles.menuItem} ${styles.danger}`}
                    onClick={() => {
                      setMoreOpen(false)
                      setConfirmLogout(true)
                    }}
                  >
                    <span className={styles.menuIcon}>🚪</span>
                    로그아웃
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {confirmLogout && (
        <div className={styles.confirmDim} onClick={() => setConfirmLogout(false)}>
          <div
            className={`${styles.confirm} pk-anim-pop-ease`}
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="logout-title"
            onClick={(e) => e.stopPropagation()}
          >
            <div className={styles.confirmIcon}>👋</div>
            <div className={styles.confirmTitle} id="logout-title">
              로그아웃 하시겠어요?
            </div>
            <div className={styles.confirmSub}>
              다시 이용하시려면 로그인이 필요해요.
            </div>
            <div className={styles.confirmActions}>
              <button
                type="button"
                className={styles.confirmCancel}
                onClick={() => setConfirmLogout(false)}
              >
                취소
              </button>
              <button
                type="button"
                className={styles.confirmLogout}
                onClick={() => dispatch({ type: A.LOGOUT })}
              >
                로그아웃
              </button>
            </div>
          </div>
        </div>
      )}

      <button
        type="button"
        className={styles.adBanner}
        onClick={() => dispatch({ type: A.START_RECO })}
      >
        <span className={styles.adIcon}>🔍</span>
        <span className={styles.adBody}>
          <span className={styles.adTitle}>내 소비패턴 분석 카드 추천</span>
          <span className={styles.adSub}>소비 습관을 분석해 꼭 맞는 카드를 추천해드려요</span>
        </span>
        <span className={styles.adTag}>AD ›</span>
      </button>

      <button
        type="button"
        className={styles.qrBar}
        onClick={() => dispatch({ type: A.SET_SCREEN, screen: 'qr' })}
      >
        <div>
          <div className={styles.qrBarLabel}>바로 결제</div>
          <div className={styles.qrBarTitle}>QR 열기</div>
        </div>
        <div className={styles.qrBarIcon}>
          <img
            src="/assets/qr-code.png"
            alt="QR"
            onError={(e) => { e.currentTarget.style.display = 'none' }}
          />
        </div>
      </button>

      {cards.length > 0 && (
        <div className={styles.statsToggle}>
          <span className={styles.statsToggleLabel}>금액 표시</span>
          <div className={styles.switch} role="group" aria-label="금액 표시">
            <button
              type="button"
              className={`${styles.switchBtn} ${showCardStats ? styles.switchOn : ''}`}
              aria-pressed={showCardStats}
              onClick={() => dispatch({ type: A.SET_CARD_STATS, show: true })}
            >
              ON
            </button>
            <button
              type="button"
              className={`${styles.switchBtn} ${showCardStats ? '' : styles.switchOff}`}
              aria-pressed={!showCardStats}
              onClick={() => dispatch({ type: A.SET_CARD_STATS, show: false })}
            >
              OFF
            </button>
          </div>
        </div>
      )}

      <div
        className={[
          styles.stack,
          expanded ? styles.stackDraggable : '',
          dragging ? styles.dragging : '',
        ].join(' ')}
        style={{ height: stackHeight }}
        onPointerDown={onPointerDown}
      >
        {cards.map((card, i) => {
          const selected = expanded && i === active
          return (
            <div
              key={card.card_id}
              className={[
                styles.stackItem,
                selected ? styles.selected : '',
                grabbed === i ? styles.grabbed : '',
              ].join(' ')}
              style={{ top: i * offset, zIndex: grabbed === i ? 30 : selected ? 20 : i }}
              // 잡기 확대는 실제로 끌기 시작했을 때만 켭니다.
              // 그냥 탭할 때까지 커졌다 작아지면 선택 애니메이션과 겹쳐 산만합니다.
              onPointerDown={() => {
                if (expanded) pressed.current = i
              }}
              onClick={() => {
                // 스와이프로 접은 직후에는 카드 선택이 따라오지 않게 막습니다.
                if (swiped.current) {
                  swiped.current = false
                  return
                }
                dispatch({ type: A.SELECT_CARD, index: i })
              }}
              // 카드를 두 번 누르면 상세로 들어갑니다.
              onDoubleClick={() => dispatch({ type: A.OPEN_CARD, index: i })}
            >
              <CardFace
                card={card}
                variant="stack"
                spent={card.spent}
                benefit={card.benefit}
                expiry={card.expiry}
                showStats={cardStatsVisible(state, card)}
              />
            </div>
          )
        })}
      </div>

      {cards.length === 0 && state.cardsError ? (
        <div className={styles.empty}>
          <div className={styles.emptyText}>{state.cardsError}</div>
          <button
            type="button"
            className={styles.emptyBtn}
            onClick={() => dispatch({ type: A.SET_CARDS, cards: [] }) || window.location.reload()}
          >
            다시 시도
          </button>
        </div>
      ) : cards.length === 0 ? (
        <div className={styles.empty}>
          <div className={styles.emptyText}>
            등록된 카드가 없어요.
            <br />
            카드를 등록하면 결제할 때 가장 유리한 카드를 추천해 드려요.
          </div>
          <button
            type="button"
            className={styles.emptyBtn}
            onClick={() => dispatch({ type: A.START_ADD })}
          >
            카드 등록하기
          </button>
        </div>
      ) : (
        <div
          className={styles.hint}
          onClick={() => dispatch({ type: A.TOGGLE_EXPANDED })}
        >
          {expanded
            ? '카드를 두 번 탭하면 상세 · 위로 쓸어올리거나 여기를 눌러 접기'
            : '카드를 탭해 펼쳐보세요'}
        </div>
      )}
    </div>
  )
}

