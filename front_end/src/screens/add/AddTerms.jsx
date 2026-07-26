import { useState } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { SCANNED_PRODUCT, buildRegisteredCard } from '../../data/cards.js'
import { registerCard } from '../../api/picka.js'
import { lastFourOf } from '../../utils/cardForm.js'
import styles from './add.module.css'

const TERMS = [
  { key: 't1', required: true, name: '카드 이용약관 동의' },
  { key: 't2', required: true, name: '개인정보 수집 및 이용 동의' },
  { key: 't3', required: true, name: '고유식별정보 처리 동의' },
  { key: 't4', required: false, name: '마케팅 정보 수신 동의' },
]

/** 3단계 · 약관 동의. 필수 3개를 모두 체크해야 등록이 완료됩니다. */
export default function AddTerms() {
  const { state, dispatch } = useApp()
  const { terms, addForm } = state

  const requiredDone = terms.t1 && terms.t2 && terms.t3
  const allChecked = requiredDone && terms.t4
  const [pending, setPending] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)

  const submit = async () => {
    if (!requiredDone || pending) return
    setPending(true)

    // 데모(가상 카드)라서 백엔드 등록이 실패해도 흐름은 완료까지 진행합니다.
    // 성공하면 백엔드가 돌려준 실제 카드 정보를, 실패하면 스캔 상품명을 사용합니다.
    let registered = {}
    try {
      const data = await registerCard(state.user?.userId, addForm, 'manual')
      registered = data?.card || {}
    } catch {
      registered = {}
    }

    dispatch({
      type: A.ADD_CARD,
      card: buildRegisteredCard({
        card_id: registered.card_id,
        card_company: registered.card_company,
        card_name: registered.card_name,
        last_four: lastFourOf(addForm.number),
        expiry: addForm.expiry,
      }),
    })
    // 지갑 목록을 다시 받아오도록 표시합니다.
    dispatch({ type: A.SET_CARDS_ERROR, message: null })
    setPending(false)
  }

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.header}>
        <button
          type="button"
          className={styles.backBtn}
          aria-label="뒤로"
          onClick={() => dispatch({ type: A.SET_ADD_STEP, step: 'input' })}
        >
          ‹
        </button>
        <span className={styles.headerTitle}>약관 동의</span>
        <span className={styles.spacer} />
      </div>

      <div className={styles.termsIntro}>
        <div className={styles.termsTitle}>
          안전한 사용을 위해
          <br />
          약관에 동의해 주세요.
        </div>
        <div className={styles.termsSub}>
          선택 약관에 동의하지 않으셔도 카드 등록 및 기본 서비스 이용이 가능합니다.
        </div>
      </div>

      <div className={styles.termsCard}>
        <div
          className={styles.termsSwatch}
          style={{ backgroundImage: 'url(/assets/shinhan-card.png)' }}
        />
        <div>
          <div className={styles.termsCardLabel}>등록 중인 카드</div>
          <div className={styles.termsCardName}>
            {SCANNED_PRODUCT.card_company} {SCANNED_PRODUCT.card_name}
          </div>
        </div>
      </div>

      <button
        type="button"
        className={styles.allRow}
        onClick={() => dispatch({ type: A.SET_ALL_TERMS, value: !allChecked })}
      >
        <span className={`${styles.check} ${styles.big} ${allChecked ? styles.on : ''}`}>✓</span>
        <span className={styles.allText}>전체 동의하기</span>
      </button>

      <div className={styles.termsList}>
        {TERMS.map((term) => (
          <button
            key={term.key}
            type="button"
            className={styles.termRow}
            aria-pressed={terms[term.key]}
            onClick={() => dispatch({ type: A.TOGGLE_TERM, key: term.key })}
          >
            <span className={`${styles.check} ${terms[term.key] ? styles.on : ''}`}>✓</span>
            <span className={styles.termName}>
              <b className={term.required ? styles.termReq : styles.termOpt}>
                [{term.required ? '필수' : '선택'}]
              </b>{' '}
              {term.name}
            </span>
            <span className={styles.termChevron}>›</span>
          </button>
        ))}
      </div>

      <button
        type="button"
        className={`${styles.primaryBtn} ${styles.pinToBottom}`}
        disabled={!requiredDone || pending}
        onClick={() => setConfirmOpen(true)}
      >
        등록 완료
      </button>

      {confirmOpen && (
        <div className={styles.addConfirmDim} onClick={() => setConfirmOpen(false)}>
          <div
            className={`${styles.addConfirm} pk-anim-pop-ease`}
            onClick={(e) => e.stopPropagation()}
          >
            <div className={styles.addConfirmImg}>
              <img src="/assets/shinhan-card.png" alt="" />
            </div>
            <div className={styles.addConfirmTitle}>정말 이 카드를 등록하시겠습니까?</div>
            <div className={styles.addConfirmSub}>
              {SCANNED_PRODUCT.card_company} {SCANNED_PRODUCT.card_name}
            </div>
            <div className={styles.addConfirmActions}>
              <button
                type="button"
                className={styles.addConfirmNo}
                onClick={() => setConfirmOpen(false)}
              >
                취소
              </button>
              <button
                type="button"
                className={styles.addConfirmYes}
                disabled={pending}
                onClick={() => {
                  setConfirmOpen(false)
                  submit()
                }}
              >
                등록
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
