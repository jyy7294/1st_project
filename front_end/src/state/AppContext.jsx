import { createContext, useContext, useReducer } from 'react'
import { appReducer, initialState } from './appReducer.js'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState)

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
