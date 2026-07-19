import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'

export default function PayFaceId() {
  const { dispatch } = useApp()
  return (
    <div>
      PayFaceId
      <button type="button" onClick={() => dispatch({ type: A.SET_PAY_STEP, payStep: 'approving' })}>
        다음
      </button>
    </div>
  )
}
