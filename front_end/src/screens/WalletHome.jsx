import { useEffect } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { fetchMyCards } from '../api/picka.js'
import CardFace from '../components/CardFace.jsx'
import PickaLogo from '../components/PickaLogo.jsx'
import styles from './WalletHome.module.css'

const CARD_HEIGHT = 186
const OFFSET_COLLAPSED = 54 // 접힌 카드 간격
const OFFSET_EXPANDED = 176 // 펼친 카드 간격

export default function WalletHome() {
  const { state, dispatch } = useApp()
  const { cards, expanded, active, cardsLoaded, showCardStats } = state

  // 보유카드는 화면 진입 시 한 번만 불러옵니다.
  // (카드를 모두 지웠을 때 다시 불러오지 않도록 개수가 아니라 로드 여부로 판단합니다.)
  useEffect(() => {
    if (cardsLoaded) return
    let cancelled = false
    fetchMyCards()
      .then((list) => {
        if (!cancelled) dispatch({ type: A.SET_CARDS, cards: list })
      })
      .catch((err) => {
        // 보유카드를 못 불러와도 앱은 계속 동작합니다. 지갑은 빈 상태로 둡니다.
        console.error('보유카드를 불러오지 못했습니다.', err)
      })
    return () => {
      cancelled = true
    }
  }, [cardsLoaded, dispatch])

  const offset = expanded ? OFFSET_EXPANDED : OFFSET_COLLAPSED
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
          <button
            type="button"
            className={`${styles.iconBtn} ${styles.light}`}
            aria-label="결제수단 관리"
            onClick={() => dispatch({ type: A.SET_SCREEN, screen: 'cards' })}
          >
            ☰
          </button>
        </div>
      </div>

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

      <div className={styles.stack} style={{ height: stackHeight }}>
        {cards.map((card, i) => {
          const selected = expanded && i === active
          return (
            <div
              key={card.card_id}
              className={`${styles.stackItem} ${selected ? styles.selected : ''}`}
              style={{ top: i * offset, zIndex: selected ? 20 : i }}
              onClick={() => dispatch({ type: A.SELECT_CARD, index: i })}
              // 카드를 두 번 누르면 상세로 들어갑니다.
              onDoubleClick={() => dispatch({ type: A.OPEN_CARD, index: i })}
            >
              <CardFace
                card={card}
                variant="stack"
                spent={card.spent}
                benefit={card.benefit}
                expiry={card.expiry}
                showStats={showCardStats}
              />
            </div>
          )
        })}
      </div>

      {cards.length === 0 ? (
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
            ? '카드를 두 번 탭하면 상세 · 여기를 눌러 접기'
            : '카드를 탭해 펼쳐보세요'}
        </div>
      )}
    </div>
  )
}

