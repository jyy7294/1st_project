import { useRef, useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { login } from '../api/auth.js'
import {
  getRecentAccounts,
  recordLogin,
  removeRecentAccount,
  formatLastLogin,
} from '../utils/recentAccounts.js'
import PickaLogo from '../components/PickaLogo.jsx'
import styles from './Login.module.css'

// 계정별로 아바타 색을 다르게 줘 서로 다른 계정임을 한눈에 구분합니다.
const AVATAR_COLORS = ['#2F6BFF', '#0DAAA0', '#7C5CFF', '#EA8A3B', '#E5556E', '#0E245D']
function avatarColor(userId) {
  return AVATAR_COLORS[Number(userId) % AVATAR_COLORS.length]
}

export default function Login() {
  const { state, dispatch } = useApp()
  const [id, setId] = useState('')
  const [pw, setPw] = useState('')
  const [pending, setPending] = useState(false)
  // 최근 로그인 계정 (userId·email·name·lastLoginAt 만 저장, 토큰·비번은 없음)
  const [recent, setRecent] = useState(getRecentAccounts)
  const [recentOpen, setRecentOpen] = useState(false) // 기본 접힘 — 최근 1개만 표시
  const [confirmDelete, setConfirmDelete] = useState(null) // 삭제 확인 대상 계정
  const pwRef = useRef(null)

  async function submit(e) {
    // Enter 로도 제출됩니다. 폼 기본 동작(페이지 새로고침)은 막습니다.
    if (e) e.preventDefault()
    if (pending) return
    setPending(true)
    try {
      const result = await login(id, pw)
      if (result.ok) {
        // 성공한 계정만 최근 목록에 남깁니다(비번·토큰은 저장하지 않음).
        recordLogin(result.user)
        dispatch({
          type: A.LOGIN_SUCCESS,
          user: result.user,
          accessToken: result.accessToken,
          refreshToken: result.refreshToken,
        })
      } else {
        dispatch({ type: A.LOGIN_FAIL, message: result.message })
      }
    } finally {
      setPending(false)
    }
  }

  // 최근 계정 선택 → 이메일만 채우고 비밀번호로 포커스 이동(자동완성처럼).
  function pickAccount(account) {
    setId(account.email)
    if (state.loginError) dispatch({ type: A.CLEAR_LOGIN_ERROR })
    pwRef.current?.focus()
  }

  // 삭제 버튼은 곧바로 지우지 않고 확인 팝업을 띄웁니다.
  function askDelete(e, account) {
    e.stopPropagation()
    setConfirmDelete(account)
  }

  function confirmRemove() {
    if (confirmDelete) setRecent(removeRecentAccount(confirmDelete.userId))
    setConfirmDelete(null)
  }

  return (
    <div className={`${styles.screen} pk-screen`}>
      <PickaLogo height={30} className={styles.logo} />

      <div className={styles.title}>PICKA에 오신 걸 환영해요</div>
      <div className={styles.sub}>카드 혜택을 최대로 챙길 시간이에요</div>

      {recent.length > 0 && (
        <div className={styles.recent}>
          <div className={styles.recentTitle}>최근 로그인 계정</div>

          <div className={styles.recentList}>
            {(recentOpen ? recent : recent.slice(0, 1)).map((account) => (
                <div
                  key={account.userId}
                  className={styles.recentItem}
                  role="button"
                  tabIndex={0}
                  onClick={() => pickAccount(account)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      pickAccount(account)
                    }
                  }}
                >
                  <span
                    className={styles.recentAvatar}
                    style={{ background: avatarColor(account.userId) }}
                  >
                    {(account.name || account.email || '?').trim().charAt(0).toUpperCase()}
                  </span>
                  <span className={styles.recentBody}>
                    <span className={styles.recentName}>
                      {account.name || account.email}
                    </span>
                    <span className={styles.recentMeta}>
                      {account.email} · {formatLastLogin(account.lastLoginAt)}
                    </span>
                  </span>
                  <button
                    type="button"
                    className={styles.recentDel}
                    aria-label="계정 삭제"
                    onClick={(e) => askDelete(e, account)}
                  >
                    ×
                  </button>
                </div>
              ))}
          </div>

          {recent.length > 1 && (
            <button
              type="button"
              className={styles.recentToggle}
              onClick={() => setRecentOpen((o) => !o)}
              aria-expanded={recentOpen}
            >
              {recentOpen ? '접기' : `다른 계정 ${recent.length - 1}개 더보기`}
              <svg
                className={`${styles.recentChevron} ${recentOpen ? styles.recentChevronOpen : ''}`}
                width="11"
                height="7"
                viewBox="0 0 12 8"
                aria-hidden="true"
              >
                <path
                  d="M1 1l5 5 5-5"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.7"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          )}
        </div>
      )}

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
            ref={pwRef}
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

      {confirmDelete && (
        <div className={styles.confirmDim} onClick={() => setConfirmDelete(null)}>
          <div
            className={`${styles.confirm} pk-anim-pop-ease`}
            onClick={(e) => e.stopPropagation()}
          >
            <div className={styles.confirmTitle}>정말 삭제하시겠어요?</div>
            <div className={styles.confirmSub}>
              {confirmDelete.name || confirmDelete.email} 계정을
              <br />
              최근 로그인 목록에서 삭제합니다.
            </div>
            <div className={styles.confirmActions}>
              <button
                type="button"
                className={styles.confirmCancel}
                onClick={() => setConfirmDelete(null)}
              >
                취소
              </button>
              <button
                type="button"
                className={styles.confirmDelete}
                onClick={confirmRemove}
              >
                삭제
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
