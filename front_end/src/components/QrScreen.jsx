import { QRCodeSVG } from 'qrcode.react'
import { won } from '../utils/format.js'
import styles from './QrScreen.module.css'

// 결제정보를 불러온 뒤의 Picka QR 화면. QR을 누르면 카드 혜택 비교 시작.
export default function QrScreen({ transaction, onScan, onBack }) {
  // QR 안에 실제 결제정보 JSON을 담아 "QR 속 데이터"를 시각적으로 재현
  const qrPayload = JSON.stringify({
    merchant_name: transaction.merchant_name,
    payment_category: transaction.payment_category,
    payment_amount: transaction.payment_amount,
  })

  return (
    <div className={styles.wrap}>
      <button type="button" className={styles.back} onClick={onBack}>
        ← 처음으로
      </button>

      <h1 className={styles.title}>Picka QR</h1>

      <button type="button" className={styles.qrButton} onClick={onScan}>
        <QRCodeSVG value={qrPayload} size={180} level="M" />
      </button>

      <dl className={styles.summary}>
        <div className={styles.row}>
          <dt>가맹점</dt>
          <dd>{transaction.merchant_name}</dd>
        </div>
        <div className={styles.row}>
          <dt>업종</dt>
          <dd>{transaction.payment_category}</dd>
        </div>
        <div className={styles.row}>
          <dt>결제 금액</dt>
          <dd className={styles.amount}>{won(transaction.payment_amount)}</dd>
        </div>
      </dl>
    </div>
  )
}
