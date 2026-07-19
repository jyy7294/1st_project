import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'

export default function WalletHome() {
  const { dispatch } = useApp()
  return (
    <div>
      WalletHome
      <button type="button" onClick={() => dispatch({ type: A.SET_SCREEN, screen: 'qr' })}>
        QR 열기
      </button>
    </div>
  )
}
