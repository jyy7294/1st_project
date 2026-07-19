import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import styles from './Splash.module.css'

export default function Splash() {
  const { dispatch } = useApp()

  return (
    <div
      className={`${styles.screen} pk-screen`}
      onClick={() => dispatch({ type: A.SET_SCREEN, screen: 'login' })}
    >
      <div className={styles.icon}>
        <PickaMark size={72} />
      </div>

      <div style={{ textAlign: 'center' }}>
        <div className={styles.wordmark}>picka</div>
        <div className={styles.tagline}>내 카드 혜택, 제대로 누리기</div>
      </div>

      <div className={styles.hint}>화면을 눌러 시작하기</div>
    </div>
  )
}

/** PICKA 브랜드 마크 (인라인 SVG). 여러 화면에서 크기만 바꿔 씁니다. */
function PickaMark({ size = 26 }) {
  return (
    <svg width={size} height={size} viewBox="150 124 242 289">
      <path
        d="M150 398V168C150 143.699 169.699 124 194 124H286C344.542 124 392 171.458 392 230C392 281.568 355.159 324.569 306.36 334.07L288 268C313.688 264.031 328 248.513 328 226C328 201.699 308.301 182 284 182H232C218.745 182 208 192.745 208 206V398H150Z"
        fill="#fff"
      />
      <path
        d="M150 324L278 287C297.562 281.343 317.956 292.79 322.586 312.623L332.7 355.938C337.415 376.13 322.955 395.905 302.31 397.94L150 413V324Z"
        fill="#2F6BFF"
      />
      <path
        d="M191 315L251 251.5C261.2 240.7 279.9 244.2 285.3 258.4L304 307.6C307.4 316.5 300.8 326 291.3 326H200.2C191.3 326 184.9 319.8 191 315Z"
        fill="#19D3C5"
      />
    </svg>
  )
}
