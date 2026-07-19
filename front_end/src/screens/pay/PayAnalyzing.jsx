import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'

export default function PayAnalyzing() {
  const { dispatch } = useApp()
  return (
    <div>
      PayAnalyzing
      <button type="button" onClick={() => dispatch({ type: A.SET_PAY_STEP, payStep: 'recommend' })}>
        다음
      </button>
    </div>
  )
}
