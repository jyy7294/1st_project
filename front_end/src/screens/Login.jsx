import { useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { login } from '../api/auth.js'
import PickaLogo from '../components/PickaLogo.jsx'
import styles from './Login.module.css'

export default function Login() {
  const { state, dispatch } = useApp()
  const [id, setId] = useState('')
  const [pw, setPw] = useState('')
  const [pending, setPending] = useState(false)

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
    </div>
  )
}

