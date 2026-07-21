import { useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import {
  CURRENT_YEAR_BENEFIT,
  NOTICE_CONTACT,
  PAY_NOTICE,
  RECO_CATEGORY_SPLIT,
  RECO_NOTICE,
} from '../data/recommend.js'
import { findRecommendation } from '../utils/recommend.js'
import { krw } from '../utils/format.js'
import styles from './RecommendDetail.module.css'

/** 카테고리 혜택은 상위 몇 개만 먼저 보여줍니다. */
const CATEGORY_PREVIEW = 3

/**
 * 추천 카드 분석 결과.
 * '분석 결과 보기' 또는 순위 목록의 카드에서 들어옵니다.
 * 맨 아래 '카드 자세히 보기'는 그 카드의 카드고릴라 상세 페이지로 나갑니다.
 */
export default function RecommendDetail() {
  const { state, dispatch } = useApp()
  const card = findRecommendation(state.recoType, state.recoSelId, state.cards)
  // 목록이 길어 화면이 답답해지지 않도록 접어 두고, 필요할 때만 펼칩니다.
  const [catOpen, setCatOpen] = useState(false)
  const [recoNoteOpen, setRecoNoteOpen] = useState(false)
  const [payNoteOpen, setPayNoteOpen] = useState(false)

  if (!card) return null

  // 총 혜택을 카테고리 비율로 나눠 보여줍니다. 0원 항목은 감춥니다.
  const categories = RECO_CATEGORY_SPLIT
    .map((c) => ({ ...c, amount: Math.round(card.benefit * c.fraction) }))
    .filter((c) => c.amount > 0)
    .sort((a, b) => b.amount - a.amount)

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.header}>
        <button
          type="button"
          className={styles.backBtn}
          aria-label="뒤로"
          onClick={() => dispatch({ type: A.SET_SCREEN, screen: 'recommend' })}
        >
          ‹
        </button>
      </div>

      <div className={styles.headWrap}>
        <div className={styles.title}>
          이 카드만 쓰면 지금보다
          <br />
          <span className={styles.gain}>{krw(card.total - CURRENT_YEAR_BENEFIT)}원</span> 더 받아요
        </div>
        <div className={styles.current}>
          지금 받고 있는 혜택
          <span className={styles.currentValue}>{krw(CURRENT_YEAR_BENEFIT)}원</span>
        </div>
      </div>

      <div className={styles.cardWrap}>
        <div className={`${styles.cardArt} pk-anim-pop-ease`} style={{ background: card.grad }}>
          <span className={styles.cardShort}>{card.short}</span>
          <span className={styles.cardIssuer}>{card.issuer}</span>
        </div>
        <div className={styles.cardName}>{card.name}</div>
      </div>

      <div className={styles.summary}>
        <div className={styles.summaryTop}>
          <span className={styles.summaryLabel}>총 혜택</span>
          <span className={styles.summaryValue}>{krw(card.total)}원</span>
        </div>
        <div className={styles.figure}>
          <span className={styles.figureLabel}>혜택</span>
          <span className={styles.figureValue}>{krw(card.benefit)}원</span>
        </div>
        <div className={styles.figure}>
          <span className={styles.figureLabel}>연회비</span>
          <span className={styles.figureValue}>-{krw(card.fee)}원</span>
        </div>
        <div className={styles.figure}>
          <span className={styles.figureLabel}>캐시백</span>
          <span className={styles.figureCash}>최대 {krw(card.cashback)}원</span>
        </div>
      </div>

      <section className={styles.section}>
        <div className={styles.sectionTitle}>내 1년 소비로 예상한 혜택</div>
        <div className={styles.catList}>
          {(catOpen ? categories : categories.slice(0, CATEGORY_PREVIEW)).map((c) => (
            <div key={c.name} className={styles.catRow}>
              <div className={styles.catIcon} style={{ background: c.tint }}>
                {c.icon}
              </div>
              <span className={styles.catName}>{c.name}</span>
              <span className={styles.catAmount}>{krw(c.amount)}원</span>
            </div>
          ))}
        </div>
        {categories.length > CATEGORY_PREVIEW && (
          <button
            type="button"
            className={styles.more}
            aria-expanded={catOpen}
            onClick={() => setCatOpen((v) => !v)}
          >
            {catOpen ? '접기' : `전체 보기 (${categories.length})`}
          </button>
        )}
      </section>

      <section className={styles.section}>
        <div className={styles.sectionTitle}>서비스 안내 및 유의사항</div>
        <NoteList notes={RECO_NOTICE} open={recoNoteOpen} onToggle={() => setRecoNoteOpen((v) => !v)} />

        <div className={`${styles.sectionTitle} ${styles.spaced}`}>결제 서비스 이용 안내</div>
        <NoteList notes={PAY_NOTICE} open={payNoteOpen} onToggle={() => setPayNoteOpen((v) => !v)} />

        <div className={styles.contact}>
          {NOTICE_CONTACT[0]}
          <br />
          {NOTICE_CONTACT[1]}
        </div>
      </section>

      <div className={styles.linkWrap}>
        {/* 카드고릴라의 해당 카드 상세 페이지로 나갑니다. */}
        <a
          className={styles.link}
          href={card.url}
          target="_blank"
          rel="noopener noreferrer"
        >
          카드 자세히 보기
        </a>
      </div>
    </div>
  )
}

/** 유의사항 목록. 접힌 상태에서는 첫 줄만 보여줍니다. */
function NoteList({ notes, open, onToggle }) {
  return (
    <>
      <ul className={styles.notes}>
        {(open ? notes : notes.slice(0, 1)).map((note) => (
          <li key={note} className={styles.note}>
            {note}
          </li>
        ))}
      </ul>
      {notes.length > 1 && (
        <button type="button" className={styles.more} aria-expanded={open} onClick={onToggle}>
          {open ? '접기' : '자세히 보기'}
        </button>
      )}
    </>
  )
}
