import { useState, useEffect } from 'react'
import { MERCHANTS } from './data/merchants.js'
import { fetchRecommendation } from './api/picka.js'
import WalletHome from './components/WalletHome.jsx'
import PickaQrHome from './components/PickaQrHome.jsx'
import QrScreen from './components/QrScreen.jsx'
import Loading from './components/Loading.jsx'
import Recommendation from './components/Recommendation.jsx'
import styles from './App.module.css'

// 화면 단계
// HOME: 월렛(지갑) 홈 화면 - 카드 스택 + QR 결제하기
// PAY_QR: QR만 있는 결제 시작 화면
// LOADING_PAYMENT: "결제 정보 불러오는 중..." (3초)
// PICKA_QR: 결제정보(가맹점·업종·금액) + QR 화면
// LOADING_COMPARE: "카드 혜택 비교중입니다..." (3초 + 백엔드 호출)
// RESULT: 추천 결과
const STEP = {
  HOME: 'home',
  PAY_QR: 'pay_qr',
  LOADING_PAYMENT: 'loading_payment',
  PICKA_QR: 'picka_qr',
  LOADING_COMPARE: 'loading_compare',
  RESULT: 'result',
}

const LOADING_MS = 3000

function pickRandomMerchant() {
  const index = Math.floor(Math.random() * MERCHANTS.length)
  return MERCHANTS[index]
}

export default function App() {
  const [step, setStep] = useState(STEP.HOME)
  const [transaction, setTransaction] = useState(null) // 불러온 결제정보
  const [result, setResult] = useState(null) // 백엔드 추천 응답
  const [error, setError] = useState(null)
  const [logoBroken, setLogoBroken] = useState(false) // 로고 파일 없으면 텍스트로 대체

  // "결제 정보 불러오는 중" 3초 후 -> Picka QR 화면
  useEffect(() => {
    if (step !== STEP.LOADING_PAYMENT) return
    const timer = setTimeout(() => setStep(STEP.PICKA_QR), LOADING_MS)
    return () => clearTimeout(timer)
  }, [step])

  // "카드 혜택 비교중" (최소 3초 + 백엔드 호출) 후 -> 추천 결과
  useEffect(() => {
    if (step !== STEP.LOADING_COMPARE) return

    let cancelled = false
    const run = async () => {
      setError(null)
      const minDelay = new Promise((resolve) => setTimeout(resolve, LOADING_MS))

      let data = null
      let failure = null
      try {
        data = await fetchRecommendation(transaction)
      } catch (err) {
        failure = err
      }

      await minDelay // 최소 3초는 로딩을 보여줌
      if (cancelled) return

      if (failure) setError(failure.message || '오류가 발생했습니다.')
      else setResult(data)
      setStep(STEP.RESULT)
    }

    run()
    return () => {
      cancelled = true
    }
  }, [step, transaction])

  // 월렛 홈에서 "QR 결제하기" -> QR만 있는 결제 시작 화면으로
  function openPayQr() {
    setStep(STEP.PAY_QR)
  }

  // QR만 있는 화면에서 QR 클릭 -> 결제정보(가상) 준비 후 로딩
  function startPayment() {
    setTransaction(pickRandomMerchant())
    setStep(STEP.LOADING_PAYMENT)
  }

  // Picka QR에서 QR 클릭 -> 카드 혜택 비교 로딩
  function startCompare() {
    setStep(STEP.LOADING_COMPARE)
  }

  function reset() {
    setTransaction(null)
    setResult(null)
    setError(null)
    setStep(STEP.HOME)
  }

  return (
    <div className={styles.app}>
      <div className={styles.phone}>
        <header className={styles.header}>
          {logoBroken ? (
            <span className={styles.logoText}>PICKA</span>
          ) : (
            <img
              className={styles.logo}
              src="/picka-logo.png"
              alt="PICKA"
              onError={() => setLogoBroken(true)}
            />
          )}

          {step === STEP.HOME && (
            <div className={styles.headerActions}>
              <button type="button" className={styles.iconBtn} aria-label="카드 추가">
                +
              </button>
              <button type="button" className={styles.iconBtn} aria-label="더보기">
                ⋯
              </button>
            </div>
          )}
        </header>

        <main className={styles.screen}>
          {step === STEP.HOME && <WalletHome onScan={openPayQr} />}

          {step === STEP.PAY_QR && (
            <PickaQrHome onScan={startPayment} onBack={reset} />
          )}

          {step === STEP.LOADING_PAYMENT && (
            <Loading message="결제 정보 불러오는 중..." />
          )}

          {step === STEP.PICKA_QR && (
            <QrScreen
              transaction={transaction}
              onScan={startCompare}
              onBack={reset}
            />
          )}

          {step === STEP.LOADING_COMPARE && (
            <Loading message="카드 혜택 비교중입니다..." />
          )}

          {step === STEP.RESULT && (
            <Recommendation
              result={result}
              error={error}
              onRetry={startCompare}
              onReset={reset}
            />
          )}
        </main>
      </div>
    </div>
  )
}
