import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'

export default function PayConfirm() {
  const { dispatch } = useApp()
  return (
    <div>
      PayConfirm
      <button type="button" onClick={() => dispatch({ type: A.SET_PAY_STEP, payStep: 'faceid' })}>
        다음
      </button>
    </div>
  )
}
