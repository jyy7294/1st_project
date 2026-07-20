import { useEffect } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { fetchMyCards } from '../api/picka.js'
import CardFace from '../components/CardFace.jsx'
import styles from './WalletHome.module.css'

const CARD_HEIGHT = 186
const OFFSET_COLLAPSED = 54 // 접힌 카드 간격
const OFFSET_EXPANDED = 176 // 펼친 카드 간격

export default function WalletHome() {
  const { state, dispatch } = useApp()
  const { cards, expanded, active, cardsLoaded } = state

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
          <PickaAppIcon />
          <span className={styles.brandText}>지갑</span>
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

      <div className={styles.stack} style={{ height: stackHeight }}>
        {cards.map((card, i) => {
          const selected = expanded && i === active
          return (
            <div
              key={card.card_id}
              className={`${styles.stackItem} ${selected ? styles.selected : ''}`}
              style={{ top: i * offset, zIndex: selected ? 20 : i }}
              onClick={() => dispatch({ type: A.SELECT_CARD, index: i })}
              // 카드를 두 번 누르면 상세로, 라벨 칩을 누르면 라벨 편집이 열린 상세로 갑니다.
              onDoubleClick={() => dispatch({ type: A.OPEN_CARD, index: i })}
            >
              <CardFace
                card={card}
                variant="stack"
                spent={card.spent}
                benefit={card.benefit}
                expiry={card.expiry}
                onLabelClick={() =>
                  dispatch({ type: A.OPEN_CARD, index: i, labelSheet: true })
                }
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

/** 헤더용 앱 아이콘 (네이비 사각 배경 + 마크). */
function PickaAppIcon() {
  return (
    <svg width="26" height="26" viewBox="24 24 464 464">
      <rect x="24" y="24" width="464" height="464" rx="108" fill="#0E245D" />
      <g>
        <PickaMarkPaths />
      </g>
    </svg>
  )
}

function PickaMarkPaths() {
  return (
    <>
      <path
        d="M150 398V168C150 143.699 169.699 124 194 124H286C344.542 124 392 171.458 392 230C392 281.568 355.159 324.569 306.36 334.07L288 268C313.688 264.031 328 248.513 328 226C328 201.699 308.301 182 284 182H232C218.745 182 208 192.745 208 206V398H150Z"
        fill="#fff"
      />
      <path
        d="M150 324L278 287C297.562 281.343 317.956 292.79 322.586 312.623L332.7 355.938C337.415 376.13 322.955 395.905 302.31 397.94L150 413V324Z"
        fill="#2F6BFF"
      />
      <path
        d="M191 315L251 251.5C261.2 240.7 279.9 244.2 285.3 258.4L304 307.6C307.4 316.5 300.8 326 291.3 326H200.2C191.3 326 184.9 319.8 191 315Z"
        fill="#19D3C5"
      />
    </>
  )
}
