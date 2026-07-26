import { useEffect, useState } from 'react'
import styles from './PhoneFrame.module.css'

/** 상태바 시계 표기. 분까지만 보여줍니다. 예: `9:41`, `15:24` */
function currentTime() {
  const now = new Date()
  // iOS 상태바처럼 시(時)에는 앞자리 0을 붙이지 않습니다.
  return `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`
}

/**
 * 상태바 시계. 실제 현재 시각을 보여주고 분이 바뀌면 따라 갱신됩니다.
 * 분 경계에 맞춰 한 번 맞춘 뒤 1분 간격으로 도므로 표시가 최대 1초만 늦습니다.
 */
function useClock() {
  const [time, setTime] = useState(currentTime)

  useEffect(() => {
    let interval
    const msToNextMinute = 60000 - (Date.now() % 60000)

    const align = setTimeout(() => {
      setTime(currentTime())
      interval = setInterval(() => setTime(currentTime()), 60000)
    }, msToNextMinute)

    return () => {
      clearTimeout(align)
      clearInterval(interval)
    }
  }, [])

  return time
}

/**
 * iPhone 17 Pro 목업 프레임 (404 × 876 뷰포트).
 * 상태바·다이나믹아일랜드·홈인디케이터를 그리고, 안쪽에 화면을 렌더합니다.
 *
 * @param {object} props
 * @param {React.ReactNode} props.children 화면 컴포넌트
 * @param {boolean} [props.dark] 어두운 화면이면 true — 상태바/인디케이터가 흰색이 됩니다
 */
export default function PhoneFrame({ children, dark = false }) {
  const tone = dark ? styles.dark : ''
  const clock = useClock()

  return (
    <div className={styles.stage}>
      <div className={styles.bezel}>
        <div className={styles.bezelInner} />
        <div className={styles.viewport}>
          <div className={`${styles.statusBar} ${tone}`}>
            <span className={styles.clock}>{clock}</span>
            <span className={styles.statusRight}>
              <span className={styles.net}>5G</span>
              <span className={styles.battery}>
                <i className={styles.batteryFill} />
              </span>
            </span>
          </div>
          <div className={styles.island} />

          {children}

          <div className={`${styles.homeIndicator} ${tone}`} />
        </div>
      </div>
    </div>
  )
}
