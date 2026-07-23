import { useEffect, useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { gradientForCard } from '../data/cards.js'
import { fetchCardDetail } from '../api/picka.js'
import { selectRecoCard } from '../utils/recommend.js'
import { benefitsForRecoCard } from '../data/recommendBenefits.js'
import { benefitView } from '../utils/benefit.js'
import styles from './CardBenefits.module.css'

/** 카드가 가진 모든 혜택을 한도·실적·유의사항까지 펼쳐 보여줍니다. */
export default function CardBenefits() {
  const { state, dispatch } = useApp()
  const fromReco = state.benefitsSource === 'reco'

  // 추천 카드는 정적 스냅샷에서, 보유 카드는 백엔드에서 혜택을 가져옵니다.
  const recoCard = fromReco ? selectRecoCard(state) : null
  const ownedCard = state.cards[state.active]

  const [rows, setRows] = useState([])

  const userId = state.user?.userId
  const cardId = ownedCard?.card_id

  useEffect(() => {
    if (fromReco || !userId || !cardId) return undefined
    let cancelled = false
    fetchCardDetail(userId, cardId)
      .then((data) => {
        if (!cancelled) setRows(data.benefits)
      })
      .catch(() => {
        if (!cancelled) setRows([])
      })
    return () => {
      cancelled = true
    }
  }, [fromReco, userId, cardId])

  if (fromReco && !recoCard) return null
  if (!fromReco && !ownedCard) return null

  // 화면 표기에 필요한 값만 두 소스에서 공통 모양으로 맞춥니다.
  const view = fromReco
    ? {
        company: recoCard.issuer,
        product: recoCard.name,
        background: recoCard.grad || gradientForCard(recoCard),
        rows: benefitsForRecoCard(recoCard.id),
        back: 'recoDetail',
      }
    : {
        company: ownedCard.card_company,
        product: ownedCard.card_name,
        background: gradientForCard(ownedCard),
        rows,
        back: 'detail',
      }

  const benefits = view.rows.map(benefitView)

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.header}>
        <button
          type="button"
          className={styles.iconBtn}
          aria-label="뒤로"
          onClick={() => dispatch({ type: A.SET_SCREEN, screen: view.back })}
        >
          ‹
        </button>
        <span className={styles.headerTitle}>상세 혜택</span>
        <span className={styles.spacer} />
      </div>

      <div className={styles.summary} style={{ background: view.background }}>
        <div>
          <div className={styles.summaryCompany}>{view.company}</div>
          <div className={styles.summaryProduct}>{view.product}</div>
        </div>
      </div>

      <div className={styles.sectionHead}>
        <span className={styles.sectionTitle}>카드 혜택</span>
        <span className={styles.count}>{benefits.length}개</span>
      </div>

      <div className={styles.list}>
        {benefits.length === 0 && (
          <div className={styles.empty}>
            등록된 상세 혜택 정보가 없어요.
            <br />
            카드사 혜택이 반영되면 여기에 표시됩니다.
          </div>
        )}

        {benefits.map((b) => (
          <div key={b.id} className={styles.item}>
            <div className={styles.itemHead}>
              <div className={styles.icon} style={{ background: b.tint }}>
                {b.icon}
              </div>
              <div className={styles.itemBody}>
                <div className={styles.itemTitle}>{b.title}</div>
                <div className={styles.itemDesc}>{b.desc}</div>
              </div>
              <span className={styles.itemRate}>{b.rate}</span>
            </div>

            <div className={styles.facts}>
              <div className={styles.fact}>
                <div className={styles.factLabel}>월 통합한도</div>
                <div className={styles.factValue}>{b.limitText}</div>
              </div>
              <div className={styles.fact}>
                <div className={styles.factLabel}>전월 실적</div>
                <div className={styles.factValue}>{b.conditionText}</div>
              </div>
            </div>

            <div className={styles.notesLabel}>유의사항</div>
            <ul className={styles.notes}>
              {b.notes.map((note) => (
                <li key={note} className={styles.note}>
                  <span className={styles.bullet}>•</span>
                  {note}
                </li>
              ))}
            </ul>
          </div>
        ))}

        <div className={styles.tail} />
      </div>
    </div>
  )
}
