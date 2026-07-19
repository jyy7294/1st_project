import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'

export default function PayReceived() {
  const { dispatch } = useApp()
  return (
    <div>
      PayReceived
      <button type="button" onClick={() => dispatch({ type: A.SET_PAY_STEP, payStep: 'analyzing' })}>
        다음
      </button>
    </div>
  )
}
