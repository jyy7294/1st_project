import { useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import CardFace from '../components/CardFace.jsx'
import { benefitsForCard } from '../data/benefits.js'
import { recentForCard } from '../data/transactions.js'
import { benefitView } from '../utils/benefit.js'
import { krw } from '../utils/format.js'
import styles from './CardDetail.module.css'

/** 상세 상단에 요약으로 보여줄 주요 혜택 개수. 나머지는 전체 혜택 화면에서 봅니다. */
const HIGHLIGHT_COUNT = 3

export default function CardDetail() {
  const { state, dispatch } = useApp()
  const card = state.cards[state.active]
  // 카드 제거는 되돌릴 수 없어 확인 창을 한 번 거칩니다.
  const [confirmRemove, setConfirmRemove] = useState(false)

  // 카드를 지운 직후처럼 선택 index가 비면 홈으로 되돌립니다.
  if (!card) return null

  const benefits = benefitsForCard(card)
  const highlights = benefits.slice(0, HIGHLIGHT_COUNT).map(benefitView)
  const recent = recentForCard(card)

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
            <div className={`${styles.menu} pk-anim-pop-ease`}>
              <button
                type="button"
                className={styles.menuItem}
                onClick={() => dispatch({ type: A.TOGGLE_NOTIFY })}
              >
                <span>🔔 알림 설정</span>
                <span className={styles.menuValue}>
                  {state.notify ? '켜짐' : '꺼짐'}
                </span>
              </button>
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
          showStats={state.showCardStats}
        />
      </div>

      <div className={styles.sectionHead}>
        <span className={styles.sectionTitle}>주요 혜택</span>
        {benefits.length > 0 && (
          <button
            type="button"
            className={styles.moreBtn}
            onClick={() => dispatch({ type: A.SET_SCREEN, screen: 'benefits' })}
          >
            전체보기 ({benefits.length})
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
      </div>

      <div className={styles.txPanel}>
        {recent.length === 0 && (
          <div className={styles.empty}>아직 결제내역이 없어요.</div>
        )}

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
              <div className={styles.txAmount}>-{krw(t.amount)}원</div>
              <div className={styles.txSaved}>{t.saved}</div>
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
                onClick={() => dispatch({ type: A.REMOVE_CARD, index: state.active })}
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
