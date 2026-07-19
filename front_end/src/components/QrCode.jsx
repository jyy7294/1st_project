import styles from './QrCode.module.css'

/**
 * 일회용 결제 QR.
 *
 * 지금은 디자인 핸드오프의 정적 이미지를 씁니다.
 * 결제서버가 QR을 발급하게 되면 <img src>를 서버 응답 이미지로 바꾸면 됩니다.
 * data-qr-* 속성은 그때 연동 지점을 찾기 쉽도록 남겨둡니다.
 *
 * @param {object} props
 * @param {string} props.token 일회용 토큰 (표시용 숫자열)
 * @param {number} props.expiresIn 남은 초
 * @param {boolean} props.expired 만료 여부
 * @param {() => void} props.onRefresh 새로고침 핸들러
 */
export default function QrCode({ token, expiresIn, expired, onRefresh }) {
  return (
    <div
      id="picka-qr"
      className={styles.frame}
      data-qr-token={token}
      data-qr-expires-in={expiresIn}
    >
      <img
        className={styles.image}
        src="/assets/qr-tight.png"
        alt="결제 QR 코드"
        style={{ opacity: expired ? 0.1 : 1 }}
      />

      {expired && (
        <div className={styles.expiredOverlay}>
          <div className={styles.expiredText}>QR이 만료되었어요</div>
          <button type="button" className={styles.refresh} onClick={onRefresh}>
            ↻
          </button>
          <div className={styles.refreshHint}>새로고침을 눌러 새 QR 발급</div>
        </div>
      )}
    </div>
  )
}
