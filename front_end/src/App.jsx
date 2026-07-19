import { AppProvider, useApp } from './state/AppContext.jsx'
import PhoneFrame from './components/PhoneFrame.jsx'
import Splash from './screens/Splash.jsx'
import Login from './screens/Login.jsx'
import WalletHome from './screens/WalletHome.jsx'
import QrScreen from './screens/QrScreen.jsx'
import PayReceived from './screens/pay/PayReceived.jsx'
import PayAnalyzing from './screens/pay/PayAnalyzing.jsx'
import PayRecommend from './screens/pay/PayRecommend.jsx'
import PayConfirm from './screens/pay/PayConfirm.jsx'
import PayFaceId from './screens/pay/PayFaceId.jsx'
import PayApproving from './screens/pay/PayApproving.jsx'
import PayDone from './screens/pay/PayDone.jsx'

const SCREENS = {
  splash: Splash,
  login: Login,
  home: WalletHome,
  qr: QrScreen,
}

const PAY_SCREENS = {
  received: PayReceived,
  analyzing: PayAnalyzing,
  recommend: PayRecommend,
  confirm: PayConfirm,
  faceid: PayFaceId,
  approving: PayApproving,
  done: PayDone,
}

// 어두운 배경 화면 — 상태바/홈인디케이터를 흰색으로 바꿉니다.
const DARK_SCREENS = new Set(['qr'])

function Router() {
  const { state } = useApp()
  const Screen = SCREENS[state.screen] ?? Splash
  const Pay = state.payStep === 'none' ? null : PAY_SCREENS[state.payStep]

  // 결제 화면은 항상 어둡습니다. faceid는 아래 화면 위에 덮이는 오버레이이므로
  // 바로 이전 단계(confirm) 화면을 함께 렌더합니다.
  const dark = Pay !== null || DARK_SCREENS.has(state.screen)

  return (
    <PhoneFrame dark={dark}>
      <Screen />
      {Pay && state.payStep === 'faceid' && <PayConfirm />}
      {Pay && <Pay />}
    </PhoneFrame>
  )
}

export default function App() {
  return (
    <AppProvider>
      <Router />
    </AppProvider>
  )
}
