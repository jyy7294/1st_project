import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'

export default function Splash() {
  const { dispatch } = useApp()
  return (
    <div onClick={() => dispatch({ type: A.SET_SCREEN, screen: 'login' })}>
      Splash — 탭하면 로그인
    </div>
  )
}
