import { useState } from 'react'
import { WALLET_CARDS } from '../data/cards.js'
import styles from './WalletHome.module.css'

// 첫 홈 화면: Apple Wallet 스타일의 겹쳐진 카드 스택.
// 카드를 탭하면 그 카드가 펼쳐지고 나머지는 접힌 채 겹쳐 있습니다.
// QR 결제 타일을 탭하면 기존 결제 흐름(onScan)으로 진입합니다.
const COLLAPSE_OVERLAP = -14 // 접힌 카드끼리 겹치는 정도(px)
const OPEN_GAP = 12 // 펼쳐진 카드 아래 카드와의 간격(px)

export default function WalletHome({ onScan }) {
  const [selectedId, setSelectedId] = useState(WALLET_CARDS[0].id)

  return (
    <div className={styles.wrap}>
      <div className={styles.head}>
        <h1 className={styles.title}>내 지갑</h1>
        <p className={styles.subtitle}>보유 카드 {WALLET_CARDS.length}장</p>
      </div>

      <button type="button" className={styles.qrTile} onClick={onScan}>
        <span className={styles.qrGlyph} aria-hidden="true">
          <QrGlyph />
        </span>
        <span className={styles.qrText}>
          <span className={styles.qrTitle}>QR로 결제하기</span>
          <span className={styles.qrSub}>탭하면 결제가 시작돼요</span>
        </span>
        <span className={styles.qrArrow} aria-hidden="true">
          ›
        </span>
      </button>

      <div className={styles.stack}>
        {WALLET_CARDS.map((card, i) => {
          const selected = card.id === selectedId
          const prevOpen = i > 0 && WALLET_CARDS[i - 1].id === selectedId
          // 첫 카드는 겹치지 않고, 펼쳐진 카드 바로 뒤 카드는 살짝 띄웁니다.
          const marginTop = i === 0 ? 0 : prevOpen ? OPEN_GAP : COLLAPSE_OVERLAP

          return (
            <button
              key={card.id}
              type="button"
              className={`${styles.card} ${selected ? styles.cardOpen : ''}`}
              style={{
                background: card.gradient,
                marginTop,
                zIndex: selected ? 50 : i + 1,
              }}
              onClick={() => setSelectedId(card.id)}
              aria-expanded={selected}
            >
              <div className={styles.cardStrip}>
                <div className={styles.cardHeadText}>
                  <span className={styles.cardCompany}>{card.company}</span>
                  <span className={styles.cardName}>{card.name}</span>
                </div>
                <span className={styles.labelChip}>{card.label}</span>
              </div>

              <div className={styles.cardFace}>
                <div className={styles.chip} />
                <div className={styles.cardBottom}>
                  <span className={styles.cardNumber}>
                    •••• •••• •••• {card.last4}
                  </span>
                  <span className={styles.brand}>PICKA</span>
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

// 작은 QR 느낌의 아이콘 (실제 QR 아님, 장식용).
function QrGlyph() {
  return (
    <svg width="26" height="26" viewBox="0 0 26 26" fill="currentColor">
      <path d="M1 1h9v9H1V1zm2 2v5h5V3H3z" />
      <rect x="4.5" y="4.5" width="2" height="2" />
      <path d="M16 1h9v9h-9V1zm2 2v5h5V3h-5z" />
      <rect x="19.5" y="4.5" width="2" height="2" />
      <path d="M1 16h9v9H1v-9zm2 2v5h5v-5H3z" />
      <rect x="4.5" y="19.5" width="2" height="2" />
      <rect x="15" y="15" width="3" height="3" />
      <rect x="21" y="15" width="4" height="3" />
      <rect x="15" y="20" width="3" height="5" />
      <rect x="20" y="21" width="5" height="4" />
    </svg>
  )
}
