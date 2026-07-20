import { useState } from 'react'
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
 * 2단계 · 카드 정보 직접 입력.
 * 입력은 포맷팅(공백/슬래시)하며 받고, 네 항목이 모두 유효해야 '다음'이 열립니다.
 * 오류 문구는 한 번 입력했다가 비운 필드에만 보여줍니다(처음부터 빨갛지 않게).
 */
export default function AddInput() {
  const { state, dispatch } = useApp()
  const form = state.addForm
  const [touched, setTouched] = useState({})

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

  const canSubmit = isAddFormValid(form)

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

      <div className={styles.preview}>
        <div>
          <div className={styles.previewCompany}>{SCANNED_PRODUCT.card_company}</div>
          <div className={styles.previewProduct}>{SCANNED_PRODUCT.card_name}</div>
        </div>
        <div className={styles.previewNumber}>
          {form.number || '**** **** **** ****'}
        </div>
        <div className={styles.previewFoot}>
          <div>
            <div className={styles.cap}>EXP</div>
            <div className={styles.val}>{form.expiry || 'MM/YY'}</div>
          </div>
          <div className={styles.right}>
            <div className={styles.cap}>CVC</div>
            <div className={styles.val}>{form.cvc ? '•'.repeat(form.cvc.length) : '***'}</div>
          </div>
        </div>
      </div>

      <div className={`${styles.field} ${styles.first}`}>
        <label className={styles.label} htmlFor="card-number">카드 번호</label>
        <input
          id="card-number"
          className={`${styles.input} ${numberError ? styles.invalid : ''}`}
          value={form.number}
          onChange={(e) => setField('number', formatCardNumber(e.target.value))}
          onBlur={() => touch('number')}
          placeholder="0000 0000 0000 0000"
          inputMode="numeric"
          autoComplete="off"
        />
        {numberError && <span className={styles.fieldError}>{numberError}</span>}
      </div>

      <div className={styles.fieldRow}>
        <div className={styles.field}>
          <label className={styles.label} htmlFor="card-expiry">유효 기간</label>
          <input
            id="card-expiry"
            className={`${styles.input} ${expiryError ? styles.invalid : ''}`}
            value={form.expiry}
            onChange={(e) => setField('expiry', formatExpiry(e.target.value))}
            onBlur={() => touch('expiry')}
            placeholder="MM/YY"
            inputMode="numeric"
            autoComplete="off"
          />
          {expiryError && <span className={styles.fieldError}>{expiryError}</span>}
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="card-cvc">CVC</label>
          <input
            id="card-cvc"
            className={`${styles.input} ${cvcError ? styles.invalid : ''}`}
            value={form.cvc}
            onChange={(e) => setField('cvc', formatCvc(e.target.value))}
            onBlur={() => touch('cvc')}
            placeholder="3자리"
            inputMode="numeric"
            type="password"
            autoComplete="off"
          />
          {cvcError && <span className={styles.fieldError}>{cvcError}</span>}
        </div>
      </div>

      <div className={styles.field}>
        <label className={styles.label} htmlFor="card-pin">비밀번호 (앞 2자리)</label>
        <input
          id="card-pin"
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

      <div className={styles.secureNote}>🔒 종단간 암호화로 안전하게 보호됩니다</div>

      <button
        type="button"
        className={`${styles.primaryBtn} ${styles.pinToBottom}`}
        disabled={!canSubmit}
        onClick={() => dispatch({ type: A.SET_ADD_STEP, step: 'terms' })}
      >
        다음
      </button>
    </div>
  )
}
