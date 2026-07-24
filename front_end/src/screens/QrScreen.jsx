import { useEffect, useRef, useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { MERCHANTS } from '../data/merchants.js'
import PickaMark from '../components/PickaMark.jsx'
import QrCode from '../components/QrCode.jsx'
import styles from './QrScreen.module.css'

const QR_LIFETIME_SEC = 180

/**
 * 스캔 라인이 바닥에 닿으면 결제정보 화면으로 넘어갑니다(애니메이션 종료 이벤트).
 * 이 값은 그 이벤트가 오지 않을 때를 대비한 안전장치입니다.
 * (스캔 애니메이션 1.2초 + 여유)
 *
 * 실제 결제서버를 붙일 때는 "QR 인식됨" 이벤트(폴링·웹소켓) 응답으로
 * recognize() 안의 setRecognizing(true) 흐름을 이어 주면 됩니다.
 */
const RECOGNIZE_FALLBACK_MS = 2000

/**
 * 일회용 QR 토큰(표시용 숫자열)을 만듭니다. 새로 발급할 때마다 매번 다른 값이 나오도록
 * 난수로 24자리를 뽑아 4자리씩 끊어 보여줍니다. 실제로는 결제서버가 발급합니다.
 */
function makeToken() {
  let out = ''
  for (let i = 0; i < 24; i += 1) {
    out += Math.floor(Math.random() * 10)
    if (i % 4 === 3 && i < 23) out += ' '
  }
  return out
}

function pickMerchant() {
  return MERCHANTS[Math.floor(Math.random() * MERCHANTS.length)]
}

export default function QrScreen() {
  const { dispatch } = useApp()
  const [seconds, setSeconds] = useState(QR_LIFETIME_SEC)
  // seed: QR 이미지 번갈아 표시(1↔2)용. token: 표시용 인식번호(새로고침마다 랜덤).
  const [seed, setSeed] = useState(1)
  const [token, setToken] = useState(makeToken)
  // QR 인식 상태. 결제정보 로딩(PayReceived) 직전의 짧은 구간입니다.
  const [recognizing, setRecognizing] = useState(false)
  // 인식 시점에 정해진 가맹점. 타이머가 끝난 뒤에도 같은 거래를 넘깁니다.
  const pendingTx = useRef(null)

  // 1초마다 카운트다운. 이 화면이 소유하는 타이머입니다.
  useEffect(() => {
    const timer = setInterval(() => {
      setSeconds((s) => Math.max(0, s - 1))
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  // 스캔 라인이 끝까지 내려오면(또는 그 이벤트가 안 오면 안전장치로) 결제로 넘어갑니다.
  const startedPay = useRef(false)
  function finishScan() {
    if (startedPay.current) return // 이벤트와 안전장치가 겹쳐도 한 번만
    startedPay.current = true
    dispatch({ type: A.START_PAY, transaction: pendingTx.current })
  }

  useEffect(() => {
    if (!recognizing) return undefined
    const timer = setTimeout(finishScan, RECOGNIZE_FALLBACK_MS)
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recognizing])

  const expired = seconds <= 0
  const mm = Math.floor(seconds / 60)
  const ss = String(seconds % 60).padStart(2, '0')

  function refresh() {
    if (recognizing) return
    setSeconds(QR_LIFETIME_SEC)
    setSeed((s) => s + 1) // QR 이미지를 다음 것으로 (1↔2 번갈아)
    setToken(makeToken()) // 인식번호는 새 난수로
  }

  // 여러 번 눌러도 인식은 한 번만 시작됩니다.
  function recognize() {
    if (recognizing || expired) return
    pendingTx.current = pickMerchant()
    setRecognizing(true)
  }

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.header}>
        <div className={styles.brand}>
          <PickaMark size={26} />
          <span className={styles.brandText}>picka</span>
        </div>
        <button
          type="button"
          className={styles.close}
          onClick={() => dispatch({ type: A.SET_SCREEN, screen: 'home' })}
        >
          ✕
        </button>
      </div>

      {/*
        결제할 카드는 QR 인식 뒤 추천 단계에서 정해집니다.
        여기서 카드명을 미리 보여주면 이미 선택된 것처럼 읽혀서 띄우지 않습니다.
      */}
      {/* 안내 문구 + QR + 유효시간·새로고침을 한 덩어리로 묶어 화면 세로 중앙에 둡니다. */}
      <div className={styles.center}>
        {/* 안내 문구를 QR 위로 */}
        <div className={styles.leadNote}>QR을 매장 리더기에 인식시켜 주세요</div>

        {/*
          QR을 탭/클릭하면 매장 인식 흐름이 시작돼 다음 화면으로 넘어갑니다.
          (기존 '매장에서 QR 인식됨' 버튼을 대신합니다.)
        */}
        <div
          className={styles.qrWrap}
          role="button"
          tabIndex={expired || recognizing ? -1 : 0}
          aria-label="QR 인식하고 다음 단계로"
          onClick={recognize}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              recognize()
            }
          }}
        >
          <QrCode
            token={token}
            expiresIn={seconds}
            expired={expired}
            onRefresh={refresh}
            seq={seed}
            scanning={recognizing}
            onScanEnd={finishScan}
          />

          {recognizing && (
            <span className={styles.srOnly} role="status" aria-live="polite">
              QR이 인식되었습니다
            </span>
          )}
        </div>

        {/* QR 바로 아래: 유효시간 + 새로고침 버튼 */}
        <div className={`${styles.timer} ${expired ? styles.expired : ''}`}>
          <button
            type="button"
            className={styles.refreshBtn}
            onClick={(e) => {
              e.stopPropagation()
              refresh()
            }}
            disabled={recognizing}
            aria-label="QR 새로고침"
            title="QR 새로고침"
          >
            ↻
          </button>
          {expired ? '유효시간 만료' : `QR 유효시간 ${mm}:${ss}`}
        </div>
      </div>

      {/* 일련번호(인식번호)는 맨 아래 유지 */}
      <div className={styles.token}>{token}</div>
    </div>
  )
}

