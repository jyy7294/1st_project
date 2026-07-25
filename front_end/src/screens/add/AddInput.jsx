import { useEffect, useRef, useState } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { SCANNED_PRODUCT } from '../../data/cards.js'
import {
  formatCardNumber,
  formatCvc,
  formatExpiry,
  formatPin,
  isAddFormValid,
  isCardNumberValid,
  isCvcValid,
  isExpiryValid,
  isPinValid,
} from '../../utils/cardForm.js'
import styles from './add.module.css'

/**
 * 2단계 · 카드 정보 입력.
 * - 스캔(addMode 'scan'): 카드 이미지 + 정보/유효기간/CVC 자동입력(읽기전용), 비밀번호만 입력 → 약관
 * - 직접입력(addMode 'manual'): 이미지 없이 직접 입력 → '맞나요?' 확인 → 네: 약관 / 아니오: 다시 입력
 */
export default function AddInput() {
  const { state, dispatch } = useApp()
  const form = state.addForm
  const isScan = state.addMode === 'scan'
  const [touched, setTouched] = useState({})
  const [confirmOpen, setConfirmOpen] = useState(false)
  const numberRef = useRef(null)
  const pinRef = useRef(null)

  // 진입 시 커서 위치: 스캔은 비밀번호(나머지 자동입력), 직접입력은 카드번호부터.
  useEffect(() => {
    if (isScan) pinRef.current?.focus()
    else numberRef.current?.focus()
  }, [isScan])

  const setField = (key, value) =>
    dispatch({ type: A.SET_ADD_FORM, patch: { [key]: value } })

  const touch = (key) => setTouched((prev) => ({ ...prev, [key]: true }))

  /** 입력했는데 아직 유효하지 않은 필드만 오류로 칩니다. */
  const errorOf = (key, valid, message) =>
    touched[key] && form[key] && !valid ? message : ''

  const numberError = errorOf('number', isCardNumberValid(form.number), '카드번호 16자리를 모두 입력해 주세요.')
  const expiryError = errorOf('expiry', isExpiryValid(form.expiry), '유효기간을 MM/YY로, 이번 달 이후로 입력해 주세요.')
  const cvcError = errorOf('cvc', isCvcValid(form.cvc), 'CVC 3자리를 입력해 주세요.')
  const pinError = errorOf('pin', isPinValid(form.pin), '비밀번호 앞 2자리를 입력해 주세요.')

  // 스캔은 비밀번호만, 직접입력은 네 항목 모두 유효해야 다음으로.
  const canSubmit = isScan ? isPinValid(form.pin) : isAddFormValid(form)

  function onNext() {
    if (!canSubmit) return
    if (isScan) {
      dispatch({ type: A.SET_ADD_STEP, step: 'terms' })
    } else {
      setConfirmOpen(true) // 직접입력은 '맞나요?' 확인창을 먼저 띄웁니다.
    }
  }

  function confirmYes() {
    setConfirmOpen(false)
    dispatch({ type: A.SET_ADD_STEP, step: 'terms' })
  }

  function confirmNo() {
    // 카드번호·유효기간·CVC 를 비워 다시 입력받습니다.
    setConfirmOpen(false)
    dispatch({ type: A.SET_ADD_FORM, patch: { number: '', expiry: '', cvc: '' } })
    setTouched((t) => ({ ...t, number: false, expiry: false, cvc: false }))
  }

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.header}>
        <button
          type="button"
          className={styles.backBtn}
          aria-label="뒤로"
          onClick={() => dispatch({ type: A.SET_ADD_STEP, step: 'scan' })}
        >
          ‹
        </button>
        <span className={styles.headerTitle}>카드 정보 입력</span>
        <span className={styles.spacer} />
      </div>

      {/* 스캔일 때만 카드 이미지 미리보기 (카드사·이름·칩이 이미 담긴 실물 이미지) */}
      {isScan && (
        <div className={styles.preview}>
          <img src="/assets/shinhan-card.png" alt="신한카드 Discount Plan+" className={styles.previewImg} />
        </div>
      )}

      <div className={`${styles.field} ${styles.first}`}>
        <label className={styles.label} htmlFor="card-number">카드 번호</label>
        <input
          id="card-number"
          ref={numberRef}
          className={`${styles.input} ${isScan ? styles.readonly : ''} ${numberError ? styles.invalid : ''}`}
          value={form.number}
          onChange={(e) => setField('number', formatCardNumber(e.target.value))}
          onBlur={() => touch('number')}
          placeholder="0000 0000 0000 0000"
          inputMode="numeric"
          autoComplete="off"
          readOnly={isScan}
          tabIndex={isScan ? -1 : 0}
        />
        {!isScan && numberError && <span className={styles.fieldError}>{numberError}</span>}
      </div>

      <div className={styles.fieldRow}>
        <div className={styles.field}>
          <label className={styles.label} htmlFor="card-expiry">유효 기간</label>
          <input
            id="card-expiry"
            className={`${styles.input} ${isScan ? styles.readonly : ''} ${expiryError ? styles.invalid : ''}`}
            value={form.expiry}
            onChange={(e) => setField('expiry', formatExpiry(e.target.value))}
            onBlur={() => touch('expiry')}
            placeholder="MM/YY"
            inputMode="numeric"
            autoComplete="off"
            readOnly={isScan}
            tabIndex={isScan ? -1 : 0}
          />
          {!isScan && expiryError && <span className={styles.fieldError}>{expiryError}</span>}
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="card-cvc">CVC</label>
          <input
            id="card-cvc"
            className={`${styles.input} ${isScan ? styles.readonly : ''} ${cvcError ? styles.invalid : ''}`}
            value={form.cvc}
            onChange={(e) => setField('cvc', formatCvc(e.target.value))}
            onBlur={() => touch('cvc')}
            placeholder="3자리"
            inputMode="numeric"
            type="password"
            autoComplete="off"
            readOnly={isScan}
            tabIndex={isScan ? -1 : 0}
          />
          {!isScan && cvcError && <span className={styles.fieldError}>{cvcError}</span>}
        </div>
      </div>

      <div className={styles.field}>
        <label className={styles.label} htmlFor="card-pin">비밀번호 (앞 2자리)</label>
        <input
          id="card-pin"
          ref={pinRef}
          className={`${styles.input} ${styles.pin} ${pinError ? styles.invalid : ''}`}
          value={form.pin}
          onChange={(e) => setField('pin', formatPin(e.target.value))}
          onBlur={() => touch('pin')}
          placeholder="＊＊"
          inputMode="numeric"
          type="password"
          autoComplete="off"
        />
        {pinError && <span className={styles.fieldError}>{pinError}</span>}
      </div>

      <div className={styles.secureNote}>종단간 암호화로 안전하게 보호됩니다</div>

      <button
        type="button"
        className={`${styles.primaryBtn} ${styles.pinToBottom}`}
        disabled={!canSubmit}
        onClick={onNext}
      >
        다음
      </button>

      {/* 직접입력 확인창 — 'OO카드가 맞나요?' */}
      {confirmOpen && (
        <div className={styles.addConfirmDim} onClick={() => setConfirmOpen(false)}>
          <div
            className={`${styles.addConfirm} pk-anim-pop-ease`}
            onClick={(e) => e.stopPropagation()}
          >
            <div className={styles.addConfirmImg}>
              <img src="/assets/shinhan-card.png" alt="" />
            </div>
            <div className={styles.addConfirmTitle}>
              {SCANNED_PRODUCT.card_company} {SCANNED_PRODUCT.card_name}가 맞나요?
            </div>
            <div className={styles.addConfirmSub}>
              {form.number}
            </div>
            <div className={styles.addConfirmActions}>
              <button type="button" className={styles.addConfirmNo} onClick={confirmNo}>
                아니오
              </button>
              <button type="button" className={styles.addConfirmYes} onClick={confirmYes}>
                네
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
