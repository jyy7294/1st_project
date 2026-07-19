import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'

export default function PayDone() {
  const { dispatch } = useApp()
  return (
    <div>
      PayDone
      <button type="button" onClick={() => dispatch({ type: A.RESET_PAY })}>
        홈으로
      </button>
    </div>
  )
}
