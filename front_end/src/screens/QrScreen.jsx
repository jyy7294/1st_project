import { useEffect, useRef, useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { MERCHANTS } from '../data/merchants.js'
import PickaMark from '../components/PickaMark.jsx'
import QrCode from '../components/QrCode.jsx'
import styles from './QrScreen.module.css'

const QR_LIFETIME_SEC = 180

/**
 * QR이 리더기에 인식된 뒤 결제정보 화면으로 넘어가기까지의 시간.
 * 실제 결제서버를 붙일 때는 이 타이머 대신 "QR 인식됨" 이벤트(폴링·웹소켓) 응답으로
 * startRecognize() 안의 setRecognizing(true) → dispatch 흐름을 이어 주면 됩니다.
 */
const RECOGNIZE_MS = 1700

/** 일회용 QR 토큰(표시용 숫자열)을 만듭니다. 실제로는 결제서버가 발급합니다. */
function makeToken(seed) {
  let x = seed * 9301 + 49297
  let out = ''
  for (let i = 0; i < 24; i += 1) {
    x = (x * 1103515245 + 12345) & 0x7fffffff
    out += x % 10
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
  const [seed, setSeed] = useState(1)
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

  // 인식 연출이 끝나면 기존과 동일하게 결제 플로우를 시작합니다.
  useEffect(() => {
    if (!recognizing) return undefined
    const timer = setTimeout(() => {
      dispatch({ type: A.START_PAY, transaction: pendingTx.current })
    }, RECOGNIZE_MS)
    return () => clearTimeout(timer)
  }, [recognizing, dispatch])

  const expired = seconds <= 0
  const mm = Math.floor(seconds / 60)
  const ss = String(seconds % 60).padStart(2, '0')

  function refresh() {
    if (recognizing) return
    setSeconds(QR_LIFETIME_SEC)
    setSeed((s) => s + 1)
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
      <div className={styles.qrWrap}>
        <QrCode
          token={makeToken(seed)}
          expiresIn={seconds}
          expired={expired}
          onRefresh={refresh}
        />

        {/* QR 인식 중: 문구 없이 회전 링과 퍼지는 원으로만 진행 상태를 보여줍니다. */}
        {recognizing && (
          <div className={`${styles.recognizeVeil} pk-anim-fade`} role="status" aria-live="polite">
            <span className={`${styles.recognizePulse} pk-anim-ring`} />
            <span className={`${styles.recognizeRing} pk-anim-spin pk-reduced-loading`} />
          </div>
        )}
      </div>

      <div className={styles.token}>{makeToken(seed)}</div>

      <div className={`${styles.timer} ${expired ? styles.expired : ''}`}>
        <span>⏱</span>
        {expired ? '유효시간 만료' : `QR 유효시간 ${mm}:${ss}`}
      </div>

      <button
        type="button"
        className={`${styles.demoBtn} ${expired || recognizing ? styles.demoBtnOff : ''}`}
        disabled={expired || recognizing}
        onClick={recognize}
      >
        🏪 매장에서 QR 인식됨 (데모)
      </button>
      <div className={styles.footNote}>화면을 매장 리더기에 인식시켜 주세요</div>
    </div>
  )
}

