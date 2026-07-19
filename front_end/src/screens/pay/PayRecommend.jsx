import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'

export default function PayRecommend() {
  const { dispatch } = useApp()
  return (
    <div>
      PayRecommend
      <button type="button" onClick={() => dispatch({ type: A.SET_PAY_STEP, payStep: 'confirm' })}>
        다음
      </button>
    </div>
  )
}
