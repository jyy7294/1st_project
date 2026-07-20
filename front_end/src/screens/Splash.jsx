import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import PickaMark from '../components/PickaMark.jsx'
import styles from './Splash.module.css'

export default function Splash() {
  const { dispatch } = useApp()

  function start() {
    dispatch({ type: A.SET_SCREEN, screen: 'login' })
  }

  return (
    <div
      className={`${styles.screen} pk-screen`}
      role="button"
      tabIndex={0}
      onClick={start}
      onKeyDown={(e) => {
        // 키보드 사용자도 스플래시를 넘어갈 수 있어야 합니다.
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          start()
        }
      }}
    >
      <div className={`${styles.icon} pk-anim-pop-ease`}>
        <PickaMark size={72} />
      </div>

      <div style={{ textAlign: 'center' }}>
        <div className={styles.wordmark}>picka</div>
        <div className={styles.tagline}>내 카드 혜택, 제대로 누리기</div>
      </div>

      <div className={`${styles.hint} pk-anim-pulse`}>화면을 눌러 시작하기</div>
    </div>
  )
}

