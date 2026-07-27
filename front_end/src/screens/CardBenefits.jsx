import { useEffect, useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { gradientForCard } from '../data/cards.js'
import { fetchCardDetail } from '../api/picka.js'
import { selectRecoCard } from '../utils/recommend.js'
import { benefitsForRecoCard } from '../data/recommendBenefits.js'
import { benefitView, isDisplayableBenefit } from '../utils/benefit.js'
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
        rows: rows.length > 0 ? rows : (ownedCard.benefits || []),
        back: 'detail',
      }

  // 플레이트 디자인 안내·홍보 문장은 혜택이 아니므로 세기 전에 걸러냅니다.
  const benefits = view.rows.filter(isDisplayableBenefit).map(benefitView)

  // 카드고릴라 원본 카드 페이지. id 를 모르면 링크를 걸지 않습니다.
  const gorillaId = fromReco ? recoCard.id : ownedCard.source_card_id
  const gorillaUrl = gorillaId
    ? `https://www.card-gorilla.com/card/detail/${gorillaId}`
    : null

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
                {b.desc && <div className={styles.itemDesc}>{b.desc}</div>}
              </div>
              <span className={styles.itemRate}>{b.rate}</span>
            </div>

            {/*
              안내 카드는 알릴 내용이 '카드사 안내를 보라'는 것뿐입니다.
              빈 한도·실적 대신 원본 카드 페이지로 가는 길만 놓아 줍니다.
            */}
            {b.kind === 'notice' ? (
              gorillaUrl && (
                <a
                  className={styles.sourceLink}
                  href={gorillaUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  카드고릴라에서 전체 혜택 보기
                  <span aria-hidden="true"> ↗</span>
                </a>
              )
            ) : (
              <>
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
              </>
            )}
          </div>
        ))}

        <div className={styles.tail} />
      </div>
    </div>
  )
}
