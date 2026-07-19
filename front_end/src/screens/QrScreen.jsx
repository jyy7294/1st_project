import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { MERCHANTS } from '../data/merchants.js'

export default function QrScreen() {
  const { dispatch } = useApp()

  function recognize() {
    const merchant = MERCHANTS[Math.floor(Math.random() * MERCHANTS.length)]
    dispatch({ type: A.START_PAY, transaction: merchant })
  }

  return (
    <div>
      QrScreen
      <button type="button" onClick={recognize}>매장에서 QR 인식됨 (데모)</button>
      <button type="button" onClick={() => dispatch({ type: A.SET_SCREEN, screen: 'home' })}>
        닫기
      </button>
    </div>
  )
}
