import { QRCodeSVG } from 'qrcode.react'
import styles from './PickaQrHome.module.css'

// 첫 화면: 결제정보 없이 사용자 Picka QR만 표시. QR을 누르면 결제 시작.
const USER_QR_PAYLOAD = 'PICKA://user/one-time-qr'

export default function PickaQrHome({ onScan }) {
  return (
    <div className={styles.wrap}>
      <h1 className={styles.title}>결제하기</h1>
      <p className={styles.subtitle}>아래 QR을 스캔해서 결제를 시작하세요.</p>

      <button type="button" className={styles.qrButton} onClick={onScan}>
        <QRCodeSVG value={USER_QR_PAYLOAD} size={200} level="M" />
      </button>
    </div>
  )
}
