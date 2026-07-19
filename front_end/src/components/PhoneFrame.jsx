import styles from './PhoneFrame.module.css'

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

  return (
    <div className={styles.stage}>
      <div className={styles.bezel}>
        <div className={styles.bezelInner} />
        <div className={styles.viewport}>
          <div className={`${styles.statusBar} ${tone}`}>
            <span className={styles.clock}>9:41</span>
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
