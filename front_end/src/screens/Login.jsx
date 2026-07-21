import { useEffect, useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { fetchSocialAuthorizeUrl, login } from '../api/auth.js'
import PickaLogo from '../components/PickaLogo.jsx'
import styles from './Login.module.css'

const SOCIAL_LABEL = { kakao: '카카오', naver: '네이버' }
const SOCIAL_COLOR = { kakao: '#FEE500', naver: '#03C75A' }
/** 소셜 로그인 창을 띄운 뒤 안내를 보여주기까지의 시간. */
const SOCIAL_DELAY_MS = 1300

export default function Login() {
  const { state, dispatch } = useApp()
  const [id, setId] = useState('')
  const [pw, setPw] = useState('')
  const [pending, setPending] = useState(false)

  // 소셜 로그인: 백엔드 콜백이 프론트로 리다이렉트하지 않아 SPA 로 돌아올 방법이 없습니다.
  // 임의의 사용자로 진입시키지 않고, 스피너를 걷고 안내만 남깁니다.
  useEffect(() => {
    if (!state.social) return
    const timer = setTimeout(() => {
      dispatch({ type: A.SET_SOCIAL, provider: null })
      dispatch({
        type: A.LOGIN_FAIL,
        message: '소셜 로그인은 아직 연결되지 않았어요. 아이디로 로그인해 주세요.',
      })
    }, SOCIAL_DELAY_MS)
    return () => clearTimeout(timer)
  }, [state.social, dispatch])

  async function submit(e) {
    // Enter 로도 제출됩니다. 폼 기본 동작(페이지 새로고침)은 막습니다.
    if (e) e.preventDefault()
    if (pending) return
    setPending(true)
    try {
      const result = await login(id, pw)
      if (result.ok) dispatch({ type: A.LOGIN_SUCCESS, user: result.user })
      else dispatch({ type: A.LOGIN_FAIL, message: result.message })
    } finally {
      setPending(false)
    }
  }

  async function social(provider) {
    dispatch({ type: A.SET_SOCIAL, provider })
    try {
      // 인가 URL은 백엔드가 state 토큰까지 붙여서 만들어 줍니다.
      const url = await fetchSocialAuthorizeUrl(provider)
      if (url) window.open(url, '_blank', 'noopener')
    } catch {
      // 소셜 키가 아직 없으면 백엔드가 503 을 줍니다. 데모 흐름은 계속 진행합니다.
    }
  }

  return (
    <div className={`${styles.screen} pk-screen`}>
      <PickaLogo height={30} className={styles.logo} />

      <div className={styles.title}>PICKA에 오신 걸 환영해요</div>
      <div className={styles.sub}>카드 혜택을 최대로 챙길 시간이에요</div>

      <form className={styles.form} onSubmit={submit}>
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

        {/* 아직 연결되지 않은 링크 — 비활성 상태임이 보이도록 흐리게 표시합니다. */}
        <div className={styles.links}>
          <span className={styles.linkOff} aria-disabled="true">회원가입</span>
          <span className={styles.linkOff} aria-disabled="true">비밀번호 찾기</span>
        </div>

        <button type="submit" className={styles.submit} disabled={pending}>
          로그인
        </button>
      </form>

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
            className={`${styles.spinner} pk-anim-spin`}
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

