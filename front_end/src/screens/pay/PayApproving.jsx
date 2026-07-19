import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'

export default function PayApproving() {
  const { dispatch } = useApp()
  return (
    <div>
      PayApproving
      <button type="button" onClick={() => dispatch({ type: A.SET_PAY_STEP, payStep: 'done' })}>
        다음
      </button>
    </div>
  )
}
