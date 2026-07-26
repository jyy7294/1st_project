import { createContext, useContext, useEffect, useReducer } from 'react'
import { appReducer, initialState, A } from './appReducer.js'
import { restoreSession } from '../api/auth.js'
import { onAuthFailure, hasRefreshToken } from '../api/client.js'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState)

  // 앱 시작(및 새로고침) 시: sessionStorage 에 refresh_token 이 있으면 보유카드·추천
  // API 보다 먼저 세션을 복구합니다. 없으면 초기화만 끝내고 스플래시/로그인으로 둡니다.
  // authInitializing 이 끝나기 전에는 화면들이 보호 API 를 호출하지 않습니다.
  useEffect(() => {
    let cancelled = false

    if (!hasRefreshToken()) {
      dispatch({ type: A.AUTH_INIT_DONE })
      return
    }

    restoreSession().then((res) => {
      if (cancelled) return
      if (res.ok) {
        dispatch({
          type: A.AUTH_RESTORED,
          user: res.user,
          accessToken: res.accessToken,
          refreshToken: res.refreshToken,
        })
      } else {
        // 복구 실패 → 인증정보는 restoreSession 이 이미 비웠고, 로그인 화면으로.
        dispatch({ type: A.SESSION_EXPIRED })
      }
    })

    return () => {
      cancelled = true
    }
  }, [])

  // 보호 API 가 refresh 까지 실패(401)하면 API 계층이 이 콜백으로 알립니다.
  // 세션을 만료 처리하고 로그인 화면으로 되돌립니다.
  useEffect(() => {
    onAuthFailure(() => dispatch({ type: A.SESSION_EXPIRED }))
    return () => onAuthFailure(null)
  }, [])

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  )
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp()은 AppProvider 안에서만 쓸 수 있습니다.')
  return ctx
}
