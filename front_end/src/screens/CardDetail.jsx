import { useEffect, useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A, cardStatsVisible } from '../state/appReducer.js'
import CardFace from '../components/CardFace.jsx'
import { fetchCardDetail, removeCard } from '../api/picka.js'
import { benefitView } from '../utils/benefit.js'
import { krw } from '../utils/format.js'
import styles from './CardDetail.module.css'

/** 상세 상단에 요약으로 보여줄 주요 혜택 개수. 나머지는 전체 혜택 화면에서 봅니다. */
const HIGHLIGHT_COUNT = 3

/** 결제내역이 적어도 이 개수만큼은 자리를 차지하도록 빈 줄로 채웁니다. */
const MIN_TX_ROWS = 3

/** 접힌 상태에서 보여줄 결제내역 개수. 나머지는 '전체보기'로 펼칩니다. */
const TX_PREVIEW = 5

export default function CardDetail() {
  const { state, dispatch } = useApp()
  const card = state.cards[state.active]
  // 카드 제거는 되돌릴 수 없어 확인 창을 한 번 거칩니다.
  const [confirmRemove, setConfirmRemove] = useState(false)
  const [removing, setRemoving] = useState(false)
  const [txOpen, setTxOpen] = useState(false)
  // 혜택·결제내역은 이 화면에 들어올 때 백엔드에서 받아옵니다.
  const [detail, setDetail] = useState({ benefits: [], transactions: [] })

  const userId = state.user?.userId
  const cardId = card?.card_id
  // 이 카드의 금액 표시 여부 (카드별 설정 > 전체 설정)
  const statsOn = cardStatsVisible(state, card)

  useEffect(() => {
    if (!userId || !cardId) return undefined
    let cancelled = false
    fetchCardDetail(userId, cardId)
      .then((data) => {
        if (!cancelled) setDetail({ benefits: data.benefits, transactions: data.transactions })
      })
      .catch(() => {
        // 상세를 못 받아도 카드 앞면은 그대로 보여 줍니다.
        if (!cancelled) setDetail({ benefits: [], transactions: [] })
      })
    return () => {
      cancelled = true
    }
  }, [userId, cardId])

  // 카드를 지운 직후처럼 선택 index가 비면 홈으로 되돌립니다.
  if (!card) return null

  const benefits = detail.benefits
  const highlights = benefits.slice(0, HIGHLIGHT_COUNT).map(benefitView)
  const allTx = detail.transactions
  const recent = txOpen ? allTx : allTx.slice(0, TX_PREVIEW)
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

      <div className={styles.sectionHead}>
        <span className={styles.sectionTitle}>주요 혜택</span>
        {benefits.length > 0 && (
          <button
            type="button"
            className={styles.moreBtn}
            onClick={() => dispatch({ type: A.SET_SCREEN, screen: 'benefits' })}
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
        {allTx.length > TX_PREVIEW && (
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
              <div className={styles.txAmount}>-{krw(t.amount)}원</div>
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
