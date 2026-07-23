import { useEffect, useState } from 'react'
import styles from './QrCode.module.css'

/**
 * 새로고침할 때마다 번갈아 쓰는 QR 이미지.
 * 1번 → 2번 → 1번 … 순서로 돌아갑니다.
 */
const QR_IMAGES = ['/assets/qr-code.png', '/assets/qr-code2.png']

/**
 * 일회용 결제 QR.
 *
 * 지금은 정적 이미지를 씁니다. 결제서버가 QR을 발급하게 되면
 * <img src>만 서버 응답 이미지로 바꾸면 됩니다.
 * data-qr-* 속성은 그때 연동 지점을 찾기 쉽도록 남겨둡니다.
 *
 * @param {object} props
 * @param {string} props.token 일회용 토큰 (표시용 숫자열)
 * @param {number} props.expiresIn 남은 초
 * @param {boolean} props.expired 만료 여부
 * @param {() => void} props.onRefresh 새로고침 핸들러
 * @param {number} [props.seq] 발급 횟수. 이 값이 바뀌면 다음 QR 이미지로 넘어갑니다.
 * @param {boolean} [props.scanning] 인식 중이면 스캔 라인을 한 번 훑어 내립니다.
 * @param {() => void} [props.onScanEnd] 스캔 라인이 바닥에 닿았을 때
 */
export default function QrCode({
  token,
  expiresIn,
  expired,
  onRefresh,
  seq = 0,
  scanning = false,
  onScanEnd,
}) {
  // 이미지를 못 불러왔는지. 그때만 'QR' 글자로 대체합니다.
  const [broken, setBroken] = useState(false)

  // QR 이 새로 발급되면 이미지 로딩을 다시 시도합니다.
  useEffect(() => {
    setBroken(false)
  }, [seq])

  const src = QR_IMAGES[seq % QR_IMAGES.length]

  return (
    <div
      id="picka-qr"
      className={styles.frame}
      data-qr-token={token}
      data-qr-expires-in={expiresIn}
    >
      {broken ? (
        <div
          style={{
            width: '100%', height: '100%', display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            background: '#0A1D4F', color: '#fff', borderRadius: 8,
            fontSize: 20, fontWeight: 800, letterSpacing: 2,
          }}
        >
          QR
        </div>
      ) : (
        <div className={styles.scanner}>
          <img
            className={styles.image}
            src={src}
            alt="결제 QR 코드"
            style={{ opacity: expired ? 0.1 : 1 }}
            onError={() => setBroken(true)}
          />

          {/* 인식 중일 때만, 위에서 아래로 한 번 훑고 끝냅니다. */}
          {scanning && !expired && (
            <div
              className={`${styles.scanLine} pk-anim-qrscan`}
              aria-hidden="true"
              onAnimationEnd={onScanEnd}
            />
          )}
        </div>
      )}

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
