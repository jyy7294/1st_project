import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'

export default function Login() {
  const { dispatch } = useApp()
  return (
    <div>
      Login
      <button type="button" onClick={() => dispatch({ type: A.LOGIN_SUCCESS })}>
        홈으로
      </button>
    </div>
  )
}
