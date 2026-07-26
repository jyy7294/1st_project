// 카드 등록 폼의 입력 포맷과 검증. 화면(AddInput)에서만 쓰지만
// 로직을 분리해 두면 규칙을 한곳에서 고칠 수 있습니다.

/** 숫자만 남깁니다. */
function digits(value) {
  return String(value || '').replace(/\D/g, '')
}

/** '1234567812345678' → '1234 5678 1234 5678' (최대 16자리) */
export function formatCardNumber(value) {
  const d = digits(value).slice(0, 16)
  return d.replace(/(\d{4})(?=\d)/g, '$1 ')
}

/** '1227' → '12/27' (최대 4자리) */
export function formatExpiry(value) {
  const d = digits(value).slice(0, 4)
  if (d.length <= 2) return d
  return `${d.slice(0, 2)}/${d.slice(2)}`
}

export function formatCvc(value) {
  return digits(value).slice(0, 3)
}

export function formatPin(value) {
  return digits(value).slice(0, 2)
}

/** 카드번호 16자리를 다 채웠는지. (데모라 Luhn 체크섬까지는 보지 않습니다.) */
export function isCardNumberValid(value) {
  return digits(value).length === 16
}

/**
 * 유효기간이 MM/YY 형식이고 이번 달 이후인지 확인합니다.
 * @param {string} value 'MM/YY'
 * @param {Date} [now] 테스트용 기준 시각
 */
export function isExpiryValid(value, now = new Date()) {
  const d = digits(value)
  if (d.length !== 4) return false

  const month = Number(d.slice(0, 2))
  if (month < 1 || month > 12) return false

  const year = 2000 + Number(d.slice(2))
  const thisYear = now.getFullYear()
  const thisMonth = now.getMonth() + 1

  if (year < thisYear) return false
  if (year === thisYear && month < thisMonth) return false
  return true
}

export function isCvcValid(value) {
  return digits(value).length === 3
}

export function isPinValid(value) {
  return digits(value).length === 2
}

/** 네 항목이 모두 유효해야 다음 단계로 넘어갑니다. */
export function isAddFormValid(form) {
  return (
    isCardNumberValid(form.number) &&
    isExpiryValid(form.expiry) &&
    isCvcValid(form.cvc) &&
    isPinValid(form.pin)
  )
}

/** 카드번호 끝 4자리. 아직 덜 채웠으면 빈 문자열. */
export function lastFourOf(value) {
  const d = digits(value)
  return d.length >= 4 ? d.slice(-4) : ''
}
