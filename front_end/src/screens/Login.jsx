import { useEffect, useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { verifyLogin, SOCIAL_URL } from '../api/auth.js'
import styles from './Login.module.css'

const SOCIAL_LABEL = { kakao: '카카오', naver: '네이버' }
const SOCIAL_COLOR = { kakao: '#FEE500', naver: '#03C75A' }
const SOCIAL_DELAY_MS = 1300

export default function Login() {
  const { state, dispatch } = useApp()
  const [id, setId] = useState('')
  const [pw, setPw] = useState('')

  // 소셜 로그인: OAuth 페이지를 새 탭으로 띄우고 스피너를 보여준 뒤 홈으로.
  useEffect(() => {
    if (!state.social) return
    const timer = setTimeout(() => dispatch({ type: A.LOGIN_SUCCESS }), SOCIAL_DELAY_MS)
    return () => clearTimeout(timer)
  }, [state.social, dispatch])

  function submit() {
    const result = verifyLogin(id, pw)
    if (result.ok) dispatch({ type: A.LOGIN_SUCCESS })
    else dispatch({ type: A.LOGIN_FAIL, message: result.message })
  }

  function social(provider) {
    try {
      window.open(SOCIAL_URL[provider], '_blank', 'noopener')
    } catch {
      // 팝업이 막혀도 데모 흐름은 계속 진행합니다.
    }
    dispatch({ type: A.SET_SOCIAL, provider })
  }

  return (
    <div className={`${styles.screen} pk-screen`}>
      <Wordmark />

      <div className={styles.title}>PICKA에 오신 걸 환영해요</div>
      <div className={styles.sub}>카드 혜택을 최대로 챙길 시간이에요</div>

      <div className={styles.fields}>
        <input
          className={styles.input}
          value={id}
          onChange={(e) => {
            setId(e.target.value)
            if (state.loginError) dispatch({ type: A.CLEAR_LOGIN_ERROR })
          }}
          placeholder="아이디 입력"
          autoComplete="off"
        />
        <input
          className={styles.input}
          type="password"
          value={pw}
          onChange={(e) => {
            setPw(e.target.value)
            if (state.loginError) dispatch({ type: A.CLEAR_LOGIN_ERROR })
          }}
          placeholder="비밀번호"
          autoComplete="new-password"
        />
      </div>

      {state.loginError && <div className={styles.error}>{state.loginError}</div>}

      <div className={styles.links}>
        <span>회원가입</span>
        <span>비밀번호 찾기</span>
      </div>

      <button type="button" className={styles.submit} onClick={submit}>
        로그인
      </button>

      <div className={styles.divider}>
        <i />간편 로그인<i />
      </div>

      <button
        type="button"
        className={`${styles.social} ${styles.kakao}`}
        onClick={() => social('kakao')}
      >
        <img
          className={styles.kakaoIcon}
          src="/assets/kakao-bubble-cut.png"
          alt=""
          onError={(e) => { e.currentTarget.style.display = 'none' }}
        />
        카카오로 시작하기
      </button>

      <button
        type="button"
        className={`${styles.social} ${styles.naver}`}
        onClick={() => social('naver')}
      >
        <span style={{ fontWeight: 900 }}>N</span>네이버로 시작하기
      </button>

      {state.social && (
        <div className={styles.overlay}>
          <div
            className={styles.spinner}
            style={{ borderTopColor: SOCIAL_COLOR[state.social] }}
          />
          <div className={styles.overlayText}>
            {SOCIAL_LABEL[state.social]} 계정으로 로그인 중…
          </div>
        </div>
      )}
    </div>
  )
}

/** 로그인 화면 상단의 가로형 로고. */
function Wordmark() {
  return (
    <svg width="120" height="35" viewBox="0 0 1100 320" style={{ marginBottom: 6 }}>
      <g transform="translate(28 20)">
        <path
          d="M34 250V62C34 42.1177 50.1177 26 70 26H145C192.496 26 231 64.5035 231 112C231 153.862 201.077 188.75 161.45 196.45L146 142C167.014 138.72 179 126.42 179 108C179 88.1177 162.882 72 143 72H101C89.9543 72 81 80.9543 81 92V250H34Z"
          fill="#0E245D"
        />
        <path
          d="M34 187L135.5 157.5C151.188 152.94 167.53 162.128 171.25 178.038L179.38 212.808C183.168 229.009 171.57 244.876 155 246.5L34 258V187Z"
          fill="#2F6BFF"
        />
        <path
          d="M65.3 181.2L113.8 130.1C122.2 121.2 137.2 124.1 141.7 135.8L156.6 174.9C159.3 182 154 189.6 146.4 189.6H72.8C65.6 189.6 60.4 185.1 65.3 181.2Z"
          fill="#19D3C5"
        />
      </g>
      <text
        x="330" y="220" fill="#0A1D4F" fontFamily="Pretendard,sans-serif"
        fontSize="180" fontWeight="800" letterSpacing="-7"
      >
        picka
      </text>
    </svg>
  )
}
