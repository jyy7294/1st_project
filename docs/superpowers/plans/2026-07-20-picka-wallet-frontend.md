# PICKA 지갑 UI 프론트엔드 재구현 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 디자인 핸드오프(`Picka Wallet.dc.html`)의 Splash·Login·Home·QR·결제 7화면을 기존 `front_end`에 React로 재구현한다.

**Architecture:** 라우터 없이 `Context + useReducer`로 `screen`/`payStep` 두 축의 상태 머신을 돌린다. `payStep !== 'none'`이면 결제 화면이 기존 화면 위를 덮는다. 스타일은 CSS Modules이고 색·라디우스·그림자는 `styles/tokens.css`의 CSS 변수를 쓴다. 타이머는 리듀서가 아니라 각 화면의 `useEffect`가 소유한다.

**Tech Stack:** React 18.3, Vite 5.4, CSS Modules (모두 이미 설치됨). **새 의존성 없음** — `npm install`을 실행할 일이 없다.

## Global Constraints

- 작업 디렉터리는 `c:\Picka_Front\1st_project`. 프론트 명령은 `front_end/`에서 실행한다.
- **`backend/` 디렉터리는 절대 수정하지 않는다.** 다른 팀원 담당이다.
- 핸드오프 폴더(`~/Desktop/1차 플젝/PICKA 웹앱 디자인_0719_rev/design_handoff_picka_wallet/`)에서 저장소로 복사하는 파일은 `assets/` 이미지 4개뿐이다. `Picka Wallet.dc.html`, `support.js`, `PICKA_공유용.html`은 복사하지 않는다.
- **테스트 러너를 추가하지 않는다.** 스펙에서 명시적으로 배제했다. 따라서 이 계획의 검증 단계는 자동화 테스트가 아니라 `npm run dev` 브라우저 확인이며, 각 단계에 **정확히 무엇이 보여야 하는지**를 적어둔다. 로직은 순수 함수로 분리해 나중에 러너를 붙일 수 있게 한다.
- 백엔드 CORS가 `localhost:5173`에만 열려 있다. `vite.config.js`의 포트 고정을 바꾸지 않는다.
- 백엔드 API 베이스는 `http://127.0.0.1:8000`이다.
- 보유카드 목업 3장은 백엔드 `user_cards.py`와 값이 일치해야 한다. 정확한 값:

  | card_id | card_company | card_name | last_four | nickname |
  |---|---|---|---|---|
  | 13 | 신한카드 | 신한카드 Mr.Life | 1234 | 생활비 카드 |
  | 2262 | 롯데카드 | LOCA LIKIT Eat | 5678 | 카페·외식 카드 |
  | 2261 | 롯데카드 | LOCA LIKIT 1.2 | 9012 | 기본 할인 카드 |

- 모든 사용자 노출 문구는 한국어다. 디자인 원문 문구를 그대로 쓴다.
- 커밋 메시지는 한국어 한 줄 요약 + 필요시 본문. 각 태스크 끝에 커밋한다.

---

## File Structure

| 파일 | 책임 |
|---|---|
| `front_end/public/assets/*.png` | 디자인 핸드오프 이미지 4개 |
| `src/styles/tokens.css` | 디자인 토큰 CSS 변수 + 공유 `@keyframes` |
| `src/components/PhoneFrame.jsx` | 폰 베젤·다이나믹아일랜드·상태바·홈인디케이터 |
| `src/components/CardFace.jsx` | 카드 앞면. `variant`로 크기 3종 |
| `src/components/QrCode.jsx` | QR 이미지 + `data-qr-*` 속성 |
| `src/state/appReducer.js` | 순수 상태 전이 함수 + 초기 상태 + 액션 생성자 |
| `src/state/AppContext.jsx` | Provider + `useApp()` 훅 |
| `src/App.jsx` | `screen`/`payStep` → 화면 매핑만 |
| `src/screens/Splash.jsx` | 스플래시 |
| `src/screens/Login.jsx` | 로그인 |
| `src/screens/WalletHome.jsx` | 지갑 홈 (카드 스택) |
| `src/screens/QrScreen.jsx` | QR 전체화면 + 카운트다운 |
| `src/screens/pay/PayReceived.jsx` | 거래정보 확인 |
| `src/screens/pay/PayAnalyzing.jsx` | AI 분석 + 추천 API 호출 |
| `src/screens/pay/PayRecommend.jsx` | 추천 카드 + 바텀시트 |
| `src/screens/pay/PayConfirm.jsx` | 결제 확인 |
| `src/screens/pay/PayFaceId.jsx` | Face ID 오버레이 |
| `src/screens/pay/PayApproving.jsx` | 승인 중 |
| `src/screens/pay/PayDone.jsx` | 결제 완료 |
| `src/data/cards.js` | 목업 보유카드 + 카드사→그라데이션 매핑 |
| `src/data/merchants.js` | 가맹점 목업 (기존 유지) |
| `src/api/picka.js` | `fetchRecommendation`, `fetchMyCards` |
| `src/api/auth.js` | 목업 로그인 검증 |
| `src/utils/format.js` | 금액 포맷 (기존 유지) |
| `src/utils/compare.js` | `sortByBenefit` — 순수 함수 |

각 `.jsx` 옆에 같은 이름의 `.module.css`를 둔다.

**삭제 대상:** `src/components/WalletHome.jsx(.module.css)`, `src/components/PickaQrHome.jsx(.module.css)`, `src/components/QrScreen.jsx(.module.css)`, `src/components/Loading.jsx(.module.css)`, `src/components/Recommendation.jsx(.module.css)`, `src/App.module.css`.

---

## Task 1: 에셋 · 디자인 토큰 · 폰 프레임

**Files:**
- Create: `front_end/public/assets/qr-code.png`, `qr-tight.png`, `kakao-bubble-cut.png`, `kakao-bubble.png`
- Create: `front_end/src/styles/tokens.css`
- Create: `front_end/src/components/PhoneFrame.jsx`, `front_end/src/components/PhoneFrame.module.css`
- Modify: `front_end/index.html`
- Modify: `front_end/src/index.css`

**Interfaces:**
- Consumes: 없음 (첫 태스크)
- Produces:
  - `PhoneFrame({ children, dark = false })` — 기본 export. `dark`가 true면 상태바·홈인디케이터가 흰색.
  - `tokens.css`의 CSS 변수 (아래 Step 2 참조)와 `@keyframes` 이름: `pk-fade`, `pk-pop`, `pk-up`, `pk-spin`, `pk-ring`, `pk-grow`, `pk-float`, `pk-islandgrow`, `pk-facespin`, `pk-facepop`, `pk-pulse`

- [ ] **Step 1: 에셋 4개 복사**

```bash
cd "c:/Picka_Front/1st_project/front_end"
mkdir -p public/assets
cp "/c/Users/KDA 31/Desktop/1차 플젝/PICKA 웹앱 디자인_0719_rev/design_handoff_picka_wallet/assets/qr-code.png" public/assets/
cp "/c/Users/KDA 31/Desktop/1차 플젝/PICKA 웹앱 디자인_0719_rev/design_handoff_picka_wallet/assets/qr-tight.png" public/assets/
cp "/c/Users/KDA 31/Desktop/1차 플젝/PICKA 웹앱 디자인_0719_rev/design_handoff_picka_wallet/assets/kakao-bubble.png" public/assets/
cp "/c/Users/KDA 31/Desktop/1차 플젝/PICKA 웹앱 디자인_0719_rev/design_handoff_picka_wallet/assets/kakao-bubble-cut.png" public/assets/
ls -la public/assets/
```

기대: 4개 파일이 나열된다. 하나라도 없으면 경로를 확인하고 멈춘다 (임의로 대체 이미지를 만들지 않는다).

- [ ] **Step 2: `src/styles/tokens.css` 작성**

```css
/* PICKA 디자인 토큰. 출처: design_handoff README의 Design Tokens 절. */
:root {
  /* Navy — 브랜드 */
  --navy: #0E245D;
  --navy-text: #0A1D4F;
  --navy-grad: linear-gradient(145deg, #10275F, #071844);

  /* Blue — 액센트 */
  --blue: #2F6BFF;
  --blue-hover: #1846D8;
  --blue-light: #6ea6ff;

  /* Teal — 혜택 */
  --teal: #19D3C5;
  --teal-deep: #0DAAA0;

  /* Gold — 혜택 금액 */
  --gold: #FFCE45;

  /* 상태 */
  --green-chart: #2F8F3E;
  --green-pay: #4ADE80;
  --danger: #e5484d;

  /* 배경 */
  --bg-app: #f4f5f8;
  --bg-card: #ffffff;
  --pay-dark: linear-gradient(180deg, #0a1224, #060b18);
  --add-dark: linear-gradient(175deg, #0a1a41, #050f2b);

  /* 텍스트 보조 */
  --text-2: #7a8299;
  --text-3: #9aa1b3;
  --text-4: #a8aec0;
  --line: #f1f2f6;
  --line-strong: #e4e7ee;

  /* 소셜 */
  --kakao: #FEE500;
  --kakao-ink: #191600;
  --naver: #03C75A;

  /* 라디우스 */
  --r-card: 20px;
  --r-btn: 14px;
  --r-chip: 10px;

  /* 그림자 */
  --sh-card: 0 4px 14px rgba(14, 36, 93, .05);
  --sh-raise: 0 16px 30px -14px rgba(14, 36, 93, .6);
}

@keyframes pk-fade { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pk-pop { from { opacity: 0; transform: scale(.96); } to { opacity: 1; transform: scale(1); } }
@keyframes pk-pulse { 0%, 100% { opacity: .5; } 50% { opacity: 1; } }
@keyframes pk-up { from { opacity: 0; transform: translateY(100%); } to { opacity: 1; transform: translateY(0); } }
@keyframes pk-spin { to { transform: rotate(360deg); } }
@keyframes pk-grow { from { width: 0; } to { width: 100%; } }
@keyframes pk-ring { 0%, 100% { transform: scale(1); opacity: .45; } 50% { transform: scale(1.18); opacity: .12; } }
@keyframes pk-float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
@keyframes pk-islandgrow {
  0% { opacity: .4; transform: translateX(-50%) translateY(-8px) scale(.32); }
  60% { opacity: 1; transform: translateX(-50%) translateY(0) scale(1.06); }
  100% { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); }
}
@keyframes pk-facespin {
  0% { transform: rotate3d(1, -1, .15, 0deg) scale(.6); opacity: 0; }
  20% { opacity: 1; }
  100% { transform: rotate3d(1, -1, .15, 360deg) scale(1); opacity: 1; }
}
@keyframes pk-facepop {
  0% { opacity: 0; transform: translateX(-50%) scale(.2); }
  60% { transform: translateX(-50%) scale(1.08); }
  100% { opacity: 1; transform: translateX(-50%) scale(1); }
}

/* 화면 진입 공통 애니메이션 */
.pk-screen { animation: pk-fade .32s cubic-bezier(.22, .61, .36, 1); }
```

- [ ] **Step 3: `src/index.css` 전체 교체**

기존 팔레트(`--picka-blue` 등)는 새 토큰으로 대체된다. 파일 내용을 아래로 통째 바꾼다.

```css
@import './styles/tokens.css';

* {
  box-sizing: border-box;
  -webkit-tap-highlight-color: transparent;
}

html, body {
  margin: 0;
  height: 100%;
}

body {
  background: radial-gradient(120% 120% at 50% 0%, #f3f4f8 0%, #e2e5ec 100%);
  font-family: 'Pretendard', 'Pretendard Variable', -apple-system, BlinkMacSystemFont,
    'Segoe UI', 'Apple SD Gothic Neo', 'Malgun Gothic', 'Noto Sans KR', system-ui, sans-serif;
  color: var(--navy-text);
  -webkit-font-smoothing: antialiased;
}

button {
  font-family: inherit;
  cursor: pointer;
}

/* 디자인 원본과 동일하게 스크롤바를 숨긴다 */
::-webkit-scrollbar { width: 0; height: 0; }
```

- [ ] **Step 4: `index.html`에 Pretendard 폰트 추가**

`<head>` 안, `<title>` 위에 두 줄을 넣는다.

```html
    <link rel="preconnect" href="https://fastly.jsdelivr.net" />
    <link
      rel="stylesheet"
      href="https://fastly.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css"
    />
```

- [ ] **Step 5: `src/components/PhoneFrame.module.css` 작성**

```css
.stage {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.bezel {
  position: relative;
  width: 430px;
  height: 902px;
  border-radius: 56px;
  background: #0a0d16;
  padding: 13px;
  box-shadow: 0 40px 90px -20px rgba(7, 25, 68, .45),
              0 0 0 2px rgba(255, 255, 255, .06) inset;
}

.bezelInner {
  position: absolute;
  inset: 6px;
  border-radius: 52px;
  background: linear-gradient(145deg, #2a2f3d, #0a0d16);
  z-index: 0;
}

.viewport {
  position: relative;
  z-index: 1;
  width: 404px;
  height: 876px;
  border-radius: 46px;
  overflow: hidden;
}

.statusBar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 54px;
  z-index: 40;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 30px 0;
  pointer-events: none;
  color: var(--navy-text);
}

.statusBar.dark { color: #fff; }

.clock {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: .3px;
}

.statusRight {
  display: flex;
  gap: 6px;
  align-items: center;
}

.net {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
}

.battery {
  width: 24px;
  height: 12px;
  border: 1.5px solid currentColor;
  border-radius: 3px;
  display: inline-block;
  position: relative;
  opacity: .9;
}

.batteryFill {
  position: absolute;
  inset: 1.5px;
  right: 5px;
  background: currentColor;
  border-radius: 1px;
  display: block;
}

.island {
  position: absolute;
  top: 14px;
  left: 50%;
  transform: translateX(-50%);
  width: 118px;
  height: 34px;
  background: #05060a;
  border-radius: 20px;
  z-index: 41;
}

.homeIndicator {
  position: absolute;
  bottom: 9px;
  left: 50%;
  transform: translateX(-50%);
  width: 132px;
  height: 5px;
  border-radius: 3px;
  background: rgba(10, 29, 79, .25);
  z-index: 50;
  pointer-events: none;
}

.homeIndicator.dark { background: rgba(255, 255, 255, .5); }
```

- [ ] **Step 6: `src/components/PhoneFrame.jsx` 작성**

```jsx
import styles from './PhoneFrame.module.css'

/**
 * iPhone 17 Pro 목업 프레임 (404 × 876 뷰포트).
 * 상태바·다이나믹아일랜드·홈인디케이터를 그리고, 안쪽에 화면을 렌더합니다.
 *
 * @param {object} props
 * @param {React.ReactNode} props.children 화면 컴포넌트
 * @param {boolean} [props.dark] 어두운 화면이면 true — 상태바/인디케이터가 흰색이 됩니다
 */
export default function PhoneFrame({ children, dark = false }) {
  const tone = dark ? styles.dark : ''

  return (
    <div className={styles.stage}>
      <div className={styles.bezel}>
        <div className={styles.bezelInner} />
        <div className={styles.viewport}>
          <div className={`${styles.statusBar} ${tone}`}>
            <span className={styles.clock}>9:41</span>
            <span className={styles.statusRight}>
              <span className={styles.net}>5G</span>
              <span className={styles.battery}>
                <i className={styles.batteryFill} />
              </span>
            </span>
          </div>
          <div className={styles.island} />

          {children}

          <div className={`${styles.homeIndicator} ${tone}`} />
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 7: 개발 서버로 확인**

```bash
cd "c:/Picka_Front/1st_project/front_end"
npm run dev
```

브라우저에서 `http://localhost:5173`을 연다.

기대: 아직 `App.jsx`가 옛 코드이므로 **기존 지갑 화면이 그대로 뜬다**. 단 폰트가 Pretendard로 바뀌고 배경이 회색 그라데이션으로 바뀐다. 콘솔에 에러가 없어야 한다. `PhoneFrame`은 아직 아무도 안 쓰므로 화면에 안 보이는 게 정상이다.

확인 후 `Ctrl+C`로 서버를 멈춘다.

- [ ] **Step 8: 커밋**

```bash
cd "c:/Picka_Front/1st_project"
git add front_end/public/assets front_end/src/styles front_end/src/components/PhoneFrame.jsx front_end/src/components/PhoneFrame.module.css front_end/src/index.css front_end/index.html
git commit -m "디자인 토큰·폰 프레임·핸드오프 에셋 추가"
```

---

## Task 2: 상태 머신 · App 배선 · 화면 스텁

이 태스크가 끝나면 앱이 새 구조 위에서 돌아간다. 화면 내용은 아직 자리표시자이고, Task 4부터 하나씩 채운다. 자리표시자를 두는 이유는 **매 커밋마다 앱이 실행 가능한 상태를 유지**하기 위해서다.

**Files:**
- Create: `front_end/src/state/appReducer.js`, `front_end/src/state/AppContext.jsx`
- Create: `front_end/src/utils/compare.js`
- Create: 화면 스텁 11개 (아래 Step 4)
- Modify: `front_end/src/App.jsx` (전체 교체)
- Delete: `src/components/WalletHome.jsx`, `WalletHome.module.css`, `PickaQrHome.jsx`, `PickaQrHome.module.css`, `QrScreen.jsx`, `QrScreen.module.css`, `Loading.jsx`, `Loading.module.css`, `Recommendation.jsx`, `Recommendation.module.css`, `src/App.module.css`

**Interfaces:**
- Consumes: `PhoneFrame` (Task 1)
- Produces:
  - `appReducer(state, action)` — 순수 함수
  - `initialState` — 아래 Step 1의 객체
  - `AppProvider({ children })`, `useApp()` → `{ state, dispatch }`
  - 액션 타입 상수 `A` (객체). 키: `SET_SCREEN`, `LOGIN_SUCCESS`, `LOGIN_FAIL`, `SET_SOCIAL`, `SET_CARDS`, `TOGGLE_EXPANDED`, `SELECT_CARD`, `START_PAY`, `SET_PAY_STEP`, `SET_RESULT`, `SET_ERROR`, `SET_NO_ELIGIBLE`, `SELECT_PAY_CARD`, `RESET_PAY`
  - `sortByBenefit(comparison)` → 새 배열. `expected_benefit` 내림차순

- [ ] **Step 1: `src/state/appReducer.js` 작성**

```js
// 앱 전체 상태 전이. 순수 함수 — 타이머·fetch 같은 부수효과는 화면 컴포넌트가 가집니다.

export const A = {
  SET_SCREEN: 'SET_SCREEN',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAIL: 'LOGIN_FAIL',
  SET_SOCIAL: 'SET_SOCIAL',
  SET_CARDS: 'SET_CARDS',
  TOGGLE_EXPANDED: 'TOGGLE_EXPANDED',
  SELECT_CARD: 'SELECT_CARD',
  START_PAY: 'START_PAY',
  SET_PAY_STEP: 'SET_PAY_STEP',
  SET_RESULT: 'SET_RESULT',
  SET_ERROR: 'SET_ERROR',
  SET_NO_ELIGIBLE: 'SET_NO_ELIGIBLE',
  SELECT_PAY_CARD: 'SELECT_PAY_CARD',
  RESET_PAY: 'RESET_PAY',
}

export const initialState = {
  screen: 'splash', // 'splash' | 'login' | 'home' | 'qr'
  payStep: 'none', // 'none' | 'received' | 'analyzing' | 'recommend'
  //                  | 'confirm' | 'faceid' | 'approving' | 'done'
  cards: [], // fetchMyCards() 결과
  expanded: false, // 홈 카드 스택 펼침 여부
  active: 0, // 홈에서 선택된 카드 index
  transaction: null, // QR로 읽은 결제정보
  payIdx: 0, // 정렬된 comparison 배열에서 결제에 쓸 카드 index
  result: null, // 백엔드 추천 응답
  error: null, // 추천 호출 실패 메시지
  noEligibleCard: false, // 404 — 이 업종에 혜택 카드가 없음
  loginError: '',
  social: null, // 'kakao' | 'naver' | null
}

export function appReducer(state, action) {
  switch (action.type) {
    case A.SET_SCREEN:
      return { ...state, screen: action.screen }

    case A.LOGIN_SUCCESS:
      return { ...state, screen: 'home', loginError: '', social: null }

    case A.LOGIN_FAIL:
      return { ...state, loginError: action.message }

    case A.SET_SOCIAL:
      return { ...state, social: action.provider }

    case A.SET_CARDS:
      return { ...state, cards: action.cards }

    case A.TOGGLE_EXPANDED:
      return { ...state, expanded: !state.expanded }

    case A.SELECT_CARD: {
      // 접힌 상태에서 카드를 누르면 펼치고 선택,
      // 펼친 상태에서 다른 카드를 누르면 선택만 옮깁니다.
      if (!state.expanded) {
        return { ...state, expanded: true, active: action.index }
      }
      return { ...state, active: action.index }
    }

    case A.START_PAY:
      return {
        ...state,
        transaction: action.transaction,
        payStep: 'received',
        result: null,
        error: null,
        noEligibleCard: false,
        payIdx: 0,
      }

    case A.SET_PAY_STEP:
      return { ...state, payStep: action.payStep }

    case A.SET_RESULT:
      return { ...state, result: action.result, error: null, noEligibleCard: false }

    case A.SET_ERROR:
      return { ...state, error: action.message, result: null }

    case A.SET_NO_ELIGIBLE:
      return { ...state, noEligibleCard: true, error: null, result: null }

    case A.SELECT_PAY_CARD:
      return { ...state, payIdx: action.index }

    case A.RESET_PAY:
      return {
        ...state,
        payStep: 'none',
        screen: 'home',
        transaction: null,
        result: null,
        error: null,
        noEligibleCard: false,
        payIdx: 0,
      }

    default:
      return state
  }
}
```

- [ ] **Step 2: `src/utils/compare.js` 작성**

```js
// 백엔드 comparison[] 을 화면 표시 순서로 정렬합니다.
// 혜택 금액 내림차순, 같으면 혜택 적용 가능한 카드가 먼저.
export function sortByBenefit(comparison) {
  if (!Array.isArray(comparison)) return []

  return [...comparison].sort((a, b) => {
    const diff = (b.expected_benefit || 0) - (a.expected_benefit || 0)
    if (diff !== 0) return diff
    return Number(b.eligible) - Number(a.eligible)
  })
}
```

- [ ] **Step 3: `src/state/AppContext.jsx` 작성**

```jsx
import { createContext, useContext, useReducer } from 'react'
import { appReducer, initialState } from './appReducer.js'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState)

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  )
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp()은 AppProvider 안에서만 쓸 수 있습니다.')
  return ctx
}
```

- [ ] **Step 4: 화면 스텁 11개 생성**

각 파일은 이 태스크에서 **자리표시자**다. Task 4~10에서 실제 화면으로 교체된다.

`src/screens/Splash.jsx`:

```jsx
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'

export default function Splash() {
  const { dispatch } = useApp()
  return (
    <div onClick={() => dispatch({ type: A.SET_SCREEN, screen: 'login' })}>
      Splash — 탭하면 로그인
    </div>
  )
}
```

`src/screens/Login.jsx`:

```jsx
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'

export default function Login() {
  const { dispatch } = useApp()
  return (
    <div>
      Login
      <button type="button" onClick={() => dispatch({ type: A.LOGIN_SUCCESS })}>
        홈으로
      </button>
    </div>
  )
}
```

`src/screens/WalletHome.jsx`:

```jsx
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
```

`src/screens/QrScreen.jsx`:

```jsx
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
```

`src/screens/pay/PayReceived.jsx` — 아래 7개는 같은 모양이다. `NAME`과 `NEXT`만 다르다.

```jsx
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
```

나머지 6개도 동일한 형태로 만든다. 컴포넌트명과 다음 단계만 바꾼다:

| 파일 | 컴포넌트명 | "다음" 버튼의 payStep |
|---|---|---|
| `pay/PayAnalyzing.jsx` | `PayAnalyzing` | `'recommend'` |
| `pay/PayRecommend.jsx` | `PayRecommend` | `'confirm'` |
| `pay/PayConfirm.jsx` | `PayConfirm` | `'faceid'` |
| `pay/PayFaceId.jsx` | `PayFaceId` | `'approving'` |
| `pay/PayApproving.jsx` | `PayApproving` | `'done'` |
| `pay/PayDone.jsx` | `PayDone` | — 대신 `{ type: A.RESET_PAY }`를 보내고 버튼 문구는 "홈으로" |

- [ ] **Step 5: `src/App.jsx` 전체 교체**

```jsx
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
```

- [ ] **Step 6: 옛 컴포넌트 삭제**

```bash
cd "c:/Picka_Front/1st_project/front_end"
git rm src/components/WalletHome.jsx src/components/WalletHome.module.css \
       src/components/PickaQrHome.jsx src/components/PickaQrHome.module.css \
       src/components/QrScreen.jsx src/components/QrScreen.module.css \
       src/components/Loading.jsx src/components/Loading.module.css \
       src/components/Recommendation.jsx src/components/Recommendation.module.css \
       src/App.module.css
```

- [ ] **Step 7: 남은 참조가 없는지 확인**

```bash
cd "c:/Picka_Front/1st_project/front_end"
grep -rn "Loading\|Recommendation\|PickaQrHome\|App.module" src/ || echo "참조 없음 — OK"
```

기대: `참조 없음 — OK`가 출력된다. 무언가 걸리면 그 파일의 import를 고친다.

- [ ] **Step 8: 개발 서버로 전체 전이 확인**

```bash
npm run dev
```

브라우저에서 순서대로 누른다: `Splash` → `홈으로` → `QR 열기` → `매장에서 QR 인식됨 (데모)` → `다음`을 6번 → `홈으로`.

기대: 폰 프레임 안에서 화면 이름이 순서대로 바뀌고 마지막에 `WalletHome`으로 돌아온다. 콘솔 에러 없음. `qr`과 결제 단계에서는 상태바 글씨(`9:41`, `5G`)가 **흰색**이다.

- [ ] **Step 9: 커밋**

```bash
cd "c:/Picka_Front/1st_project"
git add -A front_end/src
git commit -m "상태 머신·화면 라우팅 도입, 옛 컴포넌트 제거

화면 스텁 11개로 전이만 먼저 연결. 화면 내용은 후속 태스크에서 채움."
```

---

## Task 3: 데이터 · API 레이어

**Files:**
- Modify: `front_end/src/data/cards.js` (전체 교체)
- Modify: `front_end/src/api/picka.js`
- Create: `front_end/src/api/auth.js`

**Interfaces:**
- Consumes: 없음
- Produces:
  - `WALLET_CARDS` — 배열. 각 원소: `{ card_id, card_company, card_name, last_four, nickname, gradient }`
  - `gradientFor(cardCompany)` → CSS 그라데이션 문자열. 모르는 카드사면 기본 네이비
  - `fetchMyCards()` → `Promise<Array>` — `WALLET_CARDS` 반환
  - `fetchRecommendation(transaction)` → `Promise<object>` (기존 시그니처 유지)
  - `ApiError` 클래스 — `status` 속성 보유 (기존 유지)
  - `verifyLogin(id, pw)` → `{ ok: true } | { ok: false, message: string }`
  - `SOCIAL_URL` — `{ kakao: string, naver: string }`

- [ ] **Step 1: `src/data/cards.js` 전체 교체**

값은 백엔드 `user_cards.py` + `card_database.json`과 일치시킨다 (Global Constraints의 표 참조).

```js
// 지갑에 표시할 사용자 보유 카드 (프론트 목업).
// 백엔드에 보유카드 조회 API가 아직 없어서 프론트 상수로 시뮬레이션합니다.
// card_id / card_company / card_name / last_four / nickname 은
// backend/user_cards.py 의 USER_CARD_IDS(13, 2262, 2261)와 값이 일치해야
// 홈 화면 카드와 결제 추천 결과가 같은 카드로 보입니다.

// 카드사별 그라데이션. 실제 카드사 카드 이미지는 저작권 문제로 쓰지 않고
// 브랜드 컬러 기반 오리지널 디자인을 씁니다.
const GRADIENTS = {
  신한카드: 'linear-gradient(140deg,#2F6BFF,#1846D8)',
  롯데카드: 'linear-gradient(140deg,#19D3C5,#0DAFA8)',
  현대카드: 'linear-gradient(140deg,#10275F,#071844)',
  삼성카드: 'linear-gradient(140deg,#3a3f4a,#1c1f26)',
  KB국민카드: 'linear-gradient(140deg,#5A5A5A,#2e2e2e)',
}

const DEFAULT_GRADIENT = 'linear-gradient(140deg,#10275F,#071844)'

/** 카드사 이름으로 카드 앞면 그라데이션을 찾습니다. */
export function gradientFor(cardCompany) {
  return GRADIENTS[cardCompany] || DEFAULT_GRADIENT
}

export const WALLET_CARDS = [
  {
    card_id: 13,
    card_company: '신한카드',
    card_name: '신한카드 Mr.Life',
    last_four: '1234',
    nickname: '생활비 카드',
    gradient: GRADIENTS['신한카드'],
  },
  {
    card_id: 2262,
    card_company: '롯데카드',
    card_name: 'LOCA LIKIT Eat',
    last_four: '5678',
    nickname: '카페·외식 카드',
    gradient: GRADIENTS['롯데카드'],
  },
  {
    card_id: 2261,
    card_company: '롯데카드',
    card_name: 'LOCA LIKIT 1.2',
    last_four: '9012',
    nickname: '기본 할인 카드',
    gradient: DEFAULT_GRADIENT,
  },
]
```

- [ ] **Step 2: `src/api/picka.js`에 `fetchMyCards` 추가**

파일 맨 끝에 붙인다. 기존 `fetchRecommendation`과 `ApiError`는 그대로 둔다.

```js
import { WALLET_CARDS } from '../data/cards.js'

/**
 * 사용자의 보유카드 목록을 가져옵니다.
 *
 * 지금은 프론트 목업(data/cards.js)을 반환합니다.
 * 백엔드에 GET /api/v1/cards 가 생기면 이 함수 안쪽만 아래처럼 바꾸면 됩니다:
 *
 *   const res = await fetch(`${API_BASE}/api/v1/cards`)
 *   if (!res.ok) throw new ApiError('보유카드를 불러오지 못했습니다.', res.status)
 *   return res.json()
 *
 * @returns {Promise<Array>} 보유카드 배열
 */
export async function fetchMyCards() {
  return WALLET_CARDS
}
```

`import` 문은 파일 최상단(`const API_BASE = ...` 위)으로 옮겨야 한다. 최종적으로 `src/api/picka.js` 첫 줄은 다음과 같아야 한다:

```js
import { WALLET_CARDS } from '../data/cards.js'

// PICKA 백엔드(FastAPI) 연동.
const API_BASE = 'http://127.0.0.1:8000'
```

- [ ] **Step 3: `src/api/auth.js` 작성**

```js
// 목업 로그인. 백엔드에 인증 API가 없어서 프론트에서 검증합니다.
// 실제 인증 API가 생기면 verifyLogin() 안쪽만 교체하면 됩니다.

const DEMO_ID = 'KDA4'
const DEMO_PW = '1234'

/** 소셜 로그인 버튼이 새 탭으로 여는 주소. */
export const SOCIAL_URL = {
  kakao: 'https://accounts.kakao.com/login/?continue=https%3A%2F%2Fwww.kakao.com',
  naver: 'https://nid.naver.com/nidlogin.login',
}

/**
 * 아이디·비밀번호를 검증합니다.
 * @returns {{ok: true} | {ok: false, message: string}}
 */
export function verifyLogin(id, pw) {
  if (id.trim() === DEMO_ID && pw === DEMO_PW) return { ok: true }
  return { ok: false, message: '아이디 또는 비밀번호가 올바르지 않아요.' }
}
```

- [ ] **Step 4: import 경로가 깨지지 않았는지 확인**

```bash
cd "c:/Picka_Front/1st_project/front_end"
grep -rn "WALLET_CARDS" src/
npm run build
```

기대: `npm run build`가 성공하고 `dist/`가 생성된다. 실패하면 출력된 파일·줄 번호의 import를 고친다.

- [ ] **Step 5: 커밋**

```bash
cd "c:/Picka_Front/1st_project"
git add front_end/src/data front_end/src/api
git commit -m "보유카드 목업을 백엔드 카드와 일치시키고 API 어댑터 추가

fetchMyCards()는 지금 목업을 반환하며 GET /api/v1/cards 도입 시 내부만 교체.
로그인 검증은 api/auth.js 로 분리."
```

---

## Task 4: Splash · Login 화면

**Files:**
- Modify: `front_end/src/screens/Splash.jsx` (스텁 → 실제)
- Create: `front_end/src/screens/Splash.module.css`
- Modify: `front_end/src/screens/Login.jsx` (스텁 → 실제)
- Create: `front_end/src/screens/Login.module.css`

**Interfaces:**
- Consumes: `useApp()`, `A` (Task 2), `verifyLogin`, `SOCIAL_URL` (Task 3)
- Produces: 없음 (말단 화면)

- [ ] **Step 1: `src/screens/Splash.module.css` 작성**

```css
.screen {
  position: absolute;
  inset: 0;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 28px;
  cursor: pointer;
}

.icon {
  width: 118px;
  height: 118px;
  border-radius: 30px;
  background: linear-gradient(150deg, #10275F, #071844);
  box-shadow: 0 24px 50px -12px rgba(0, 0, 0, .6),
              0 0 0 1px rgba(255, 255, 255, .08) inset;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: pk-pop .5s ease;
}

.wordmark {
  font-size: 40px;
  font-weight: 800;
  letter-spacing: -1.5px;
  color: var(--navy-text);
}

.tagline {
  margin-top: 10px;
  font-size: 14px;
  color: var(--text-2);
  font-weight: 500;
}

.hint {
  position: absolute;
  bottom: 60px;
  font-size: 12.5px;
  color: var(--text-4);
  animation: pk-pulse 2s infinite;
}
```

- [ ] **Step 2: `src/screens/Splash.jsx` 작성**

```jsx
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import styles from './Splash.module.css'

export default function Splash() {
  const { dispatch } = useApp()

  return (
    <div
      className={`${styles.screen} pk-screen`}
      onClick={() => dispatch({ type: A.SET_SCREEN, screen: 'login' })}
    >
      <div className={styles.icon}>
        <PickaMark size={72} />
      </div>

      <div style={{ textAlign: 'center' }}>
        <div className={styles.wordmark}>picka</div>
        <div className={styles.tagline}>내 카드 혜택, 제대로 누리기</div>
      </div>

      <div className={styles.hint}>화면을 눌러 시작하기</div>
    </div>
  )
}

/** PICKA 브랜드 마크 (인라인 SVG). 여러 화면에서 크기만 바꿔 씁니다. */
export function PickaMark({ size = 26 }) {
  return (
    <svg width={size} height={size} viewBox="150 124 242 289">
      <path
        d="M150 398V168C150 143.699 169.699 124 194 124H286C344.542 124 392 171.458 392 230C392 281.568 355.159 324.569 306.36 334.07L288 268C313.688 264.031 328 248.513 328 226C328 201.699 308.301 182 284 182H232C218.745 182 208 192.745 208 206V398H150Z"
        fill="#fff"
      />
      <path
        d="M150 324L278 287C297.562 281.343 317.956 292.79 322.586 312.623L332.7 355.938C337.415 376.13 322.955 395.905 302.31 397.94L150 413V324Z"
        fill="#2F6BFF"
      />
      <path
        d="M191 315L251 251.5C261.2 240.7 279.9 244.2 285.3 258.4L304 307.6C307.4 316.5 300.8 326 291.3 326H200.2C191.3 326 184.9 319.8 191 315Z"
        fill="#19D3C5"
      />
    </svg>
  )
}
```

- [ ] **Step 3: `src/screens/Login.module.css` 작성**

```css
.screen {
  position: absolute;
  inset: 0;
  background: #fff;
  display: flex;
  flex-direction: column;
  padding: 74px 30px 40px;
  overflow-y: auto;
}

.title {
  font-size: 24px;
  font-weight: 700;
  color: var(--navy-text);
  letter-spacing: -.5px;
  margin-top: 18px;
}

.sub {
  font-size: 14px;
  color: var(--text-2);
  margin-top: 6px;
}

.fields {
  margin-top: 34px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input {
  height: 54px;
  padding: 0 16px;
  border: 1.5px solid var(--line-strong);
  border-radius: var(--r-btn);
  background: #fafbfc;
  font-size: 15px;
  color: var(--navy-text);
  font-family: inherit;
  outline: none;
}

.input:focus { border-color: var(--blue); }

.error {
  margin-top: 10px;
  font-size: 12.5px;
  color: var(--danger);
  font-weight: 500;
}

.links {
  display: flex;
  justify-content: flex-end;
  gap: 18px;
  margin-top: 14px;
  padding: 0 4px;
  font-size: 12.5px;
  color: var(--text-3);
}

.submit {
  margin-top: 22px;
  height: 54px;
  border: none;
  border-radius: var(--r-btn);
  background: linear-gradient(150deg, #10275F, #071844);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  box-shadow: 0 12px 24px -8px rgba(14, 36, 93, .5);
}

.divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 26px 0 18px;
  color: #c3c8d4;
  font-size: 12px;
}

.divider i { flex: 1; height: 1px; background: #eceef3; }

.social {
  height: 52px;
  border: none;
  border-radius: var(--r-btn);
  font-size: 15px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.kakao { background: var(--kakao); color: var(--kakao-ink); }
.naver { margin-top: 10px; background: var(--naver); color: #fff; }
.kakaoIcon { width: 20px; height: 20px; display: block; }

.overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, .86);
  backdrop-filter: blur(2px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18px;
  z-index: 20;
}

.spinner {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 3px solid var(--line-strong);
  animation: pk-spin .8s linear infinite;
}

.overlayText {
  font-size: 14px;
  color: var(--navy-text);
  font-weight: 600;
}
```

- [ ] **Step 4: `src/screens/Login.jsx` 작성**

```jsx
import { useEffect, useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { verifyLogin, SOCIAL_URL } from '../api/auth.js'
import styles from './Login.module.css'

const SOCIAL_LABEL = { kakao: '카카오', naver: '네이버' }
const SOCIAL_COLOR = { kakao: '#FEE500', naver: '#03C75A' }
const SOCIAL_DELAY_MS = 1300

export default function Login() {
  const { state, dispatch } = useApp()
  const [id, setId] = useState('')
  const [pw, setPw] = useState('')

  // 소셜 로그인: OAuth 페이지를 새 탭으로 띄우고 스피너를 보여준 뒤 홈으로.
  useEffect(() => {
    if (!state.social) return
    const timer = setTimeout(() => dispatch({ type: A.LOGIN_SUCCESS }), SOCIAL_DELAY_MS)
    return () => clearTimeout(timer)
  }, [state.social, dispatch])

  function submit() {
    const result = verifyLogin(id, pw)
    if (result.ok) dispatch({ type: A.LOGIN_SUCCESS })
    else dispatch({ type: A.LOGIN_FAIL, message: result.message })
  }

  function social(provider) {
    try {
      window.open(SOCIAL_URL[provider], '_blank', 'noopener')
    } catch {
      // 팝업이 막혀도 데모 흐름은 계속 진행합니다.
    }
    dispatch({ type: A.SET_SOCIAL, provider })
  }

  return (
    <div className={`${styles.screen} pk-screen`}>
      <Wordmark />

      <div className={styles.title}>PICKA에 오신 걸 환영해요</div>
      <div className={styles.sub}>카드 혜택을 최대로 챙길 시간이에요</div>

      <div className={styles.fields}>
        <input
          className={styles.input}
          value={id}
          onChange={(e) => setId(e.target.value)}
          placeholder="아이디 입력"
          autoComplete="off"
        />
        <input
          className={styles.input}
          type="password"
          value={pw}
          onChange={(e) => setPw(e.target.value)}
          placeholder="비밀번호"
          autoComplete="new-password"
        />
      </div>

      {state.loginError && <div className={styles.error}>{state.loginError}</div>}

      <div className={styles.links}>
        <span>회원가입</span>
        <span>비밀번호 찾기</span>
      </div>

      <button type="button" className={styles.submit} onClick={submit}>
        로그인
      </button>

      <div className={styles.divider}>
        <i />간편 로그인<i />
      </div>

      <button
        type="button"
        className={`${styles.social} ${styles.kakao}`}
        onClick={() => social('kakao')}
      >
        <img className={styles.kakaoIcon} src="/assets/kakao-bubble-cut.png" alt="" />
        카카오로 시작하기
      </button>

      <button
        type="button"
        className={`${styles.social} ${styles.naver}`}
        onClick={() => social('naver')}
      >
        <span style={{ fontWeight: 900 }}>N</span>네이버로 시작하기
      </button>

      {state.social && (
        <div className={styles.overlay}>
          <div
            className={styles.spinner}
            style={{ borderTopColor: SOCIAL_COLOR[state.social] }}
          />
          <div className={styles.overlayText}>
            {SOCIAL_LABEL[state.social]} 계정으로 로그인 중…
          </div>
        </div>
      )}
    </div>
  )
}

/** 로그인 화면 상단의 가로형 로고. */
function Wordmark() {
  return (
    <svg width="120" height="35" viewBox="0 0 1100 320" style={{ marginBottom: 6 }}>
      <g transform="translate(28 20)">
        <path
          d="M34 250V62C34 42.1177 50.1177 26 70 26H145C192.496 26 231 64.5035 231 112C231 153.862 201.077 188.75 161.45 196.45L146 142C167.014 138.72 179 126.42 179 108C179 88.1177 162.882 72 143 72H101C89.9543 72 81 80.9543 81 92V250H34Z"
          fill="#0E245D"
        />
        <path
          d="M34 187L135.5 157.5C151.188 152.94 167.53 162.128 171.25 178.038L179.38 212.808C183.168 229.009 171.57 244.876 155 246.5L34 258V187Z"
          fill="#2F6BFF"
        />
        <path
          d="M65.3 181.2L113.8 130.1C122.2 121.2 137.2 124.1 141.7 135.8L156.6 174.9C159.3 182 154 189.6 146.4 189.6H72.8C65.6 189.6 60.4 185.1 65.3 181.2Z"
          fill="#19D3C5"
        />
      </g>
      <text
        x="330" y="220" fill="#0A1D4F" fontFamily="Pretendard,sans-serif"
        fontSize="180" fontWeight="800" letterSpacing="-7"
      >
        picka
      </text>
    </svg>
  )
}
```

- [ ] **Step 5: 브라우저 확인**

```bash
cd "c:/Picka_Front/1st_project/front_end"
npm run dev
```

확인 항목:
1. 스플래시에 네이비 라운드 아이콘 + `picka` + "내 카드 혜택, 제대로 누리기"가 보이고 하단 문구가 깜빡인다.
2. 탭하면 로그인 화면. 가로형 로고와 입력 2개가 보인다.
3. 아무 값이나 넣고 로그인 → **빨간색** "아이디 또는 비밀번호가 올바르지 않아요."
4. `KDA4` / `1234` → `WalletHome` 스텁으로 이동.
5. 뒤로 돌아가 카카오 버튼 → 새 탭이 열리고 노란 스피너 오버레이 후 홈으로. **카카오 버튼에 말풍선 이미지가 보인다** (깨진 이미지 아이콘이면 `public/assets/kakao-bubble-cut.png` 경로를 확인한다).

- [ ] **Step 6: 커밋**

```bash
cd "c:/Picka_Front/1st_project"
git add front_end/src/screens/Splash.jsx front_end/src/screens/Splash.module.css front_end/src/screens/Login.jsx front_end/src/screens/Login.module.css
git commit -m "스플래시·로그인 화면 구현"
```

---

## Task 5: 카드 앞면 컴포넌트 · 지갑 홈

**Files:**
- Create: `front_end/src/components/CardFace.jsx`, `front_end/src/components/CardFace.module.css`
- Modify: `front_end/src/screens/WalletHome.jsx` (스텁 → 실제)
- Create: `front_end/src/screens/WalletHome.module.css`

**Interfaces:**
- Consumes: `useApp()`, `A`, `fetchMyCards`, `gradientFor`, `PickaMark` (Task 4의 `Splash.jsx`에서 named export)
- Produces:
  - `CardFace({ card, variant, spent, benefit, expiry })` — `variant`는 `'stack' | 'detail' | 'row'`. `card`는 `{ card_company, card_name, last_four, nickname, gradient }` 형태

- [ ] **Step 1: `src/components/CardFace.module.css` 작성**

```css
.card {
  position: relative;
  border-radius: var(--r-card);
  color: #fff;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 14px 26px -12px rgba(10, 29, 79, .5);
  overflow: hidden;
}

.stack { height: 186px; }

.detail {
  height: 200px;
  border-radius: 22px;
  padding: 22px 24px;
  box-shadow: 0 22px 40px -18px rgba(10, 29, 79, .6);
  animation: pk-pop .35s ease;
}

.row {
  height: 36px;
  width: 56px;
  border-radius: 8px;
  padding: 0;
  box-shadow: none;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.company { font-size: 11px; color: rgba(255, 255, 255, .6); font-weight: 500; }
.detail .company { font-size: 12px; }

.product { font-size: 15.5px; font-weight: 700; letter-spacing: -.2px; margin-top: 1px; }
.detail .product { font-size: 18px; margin-top: 2px; }

.chip {
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  background: rgba(255, 255, 255, .2);
  padding: 3px 10px;
  border-radius: 8px;
  flex: none;
}

.number {
  font-size: 16px;
  letter-spacing: 2.5px;
  color: rgba(255, 255, 255, .82);
  font-weight: 500;
}

.detail .number { font-size: 18px; letter-spacing: 3px; color: rgba(255, 255, 255, .85); }

.foot {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
}

.stats { display: flex; gap: 18px; }
.detail .stats { gap: 22px; }

.statLabel { font-size: 10.5px; color: rgba(255, 255, 255, .55); }
.detail .statLabel { font-size: 11px; }

.statValue {
  font-size: 16px;
  font-weight: 800;
  letter-spacing: -.4px;
  margin-top: 1px;
}

.detail .statValue { font-size: 19px; }
.statValue.gold { color: var(--gold); }
.statUnit { font-size: 11px; font-weight: 600; }
.detail .statUnit { font-size: 12px; }

.expiry { font-size: 11px; color: rgba(255, 255, 255, .7); }
.detail .expiry { font-size: 12px; }
```

- [ ] **Step 2: `src/components/CardFace.jsx` 작성**

```jsx
import { gradientFor } from '../data/cards.js'
import styles from './CardFace.module.css'

/**
 * 카드 앞면.
 *
 * @param {object} props
 * @param {object} props.card `{ card_company, card_name, last_four, nickname, gradient? }`
 * @param {'stack'|'detail'|'row'} [props.variant] 크기. row는 목록용 작은 색 블록
 * @param {string} [props.spent] 이번 달 사용액 (포맷된 문자열)
 * @param {string} [props.benefit] 받은 혜택 (포맷된 문자열)
 * @param {string} [props.expiry] 만료일 `MM/YY`
 */
export default function CardFace({
  card,
  variant = 'stack',
  spent,
  benefit,
  expiry,
}) {
  const background = card.gradient || gradientFor(card.card_company)

  if (variant === 'row') {
    return <div className={`${styles.card} ${styles.row}`} style={{ background }} />
  }

  return (
    <div className={`${styles.card} ${styles[variant]}`} style={{ background }}>
      <div className={styles.head}>
        <div>
          <div className={styles.company}>{card.card_company}</div>
          <div className={styles.product}>{card.card_name}</div>
        </div>
        {card.nickname && <span className={styles.chip}>{card.nickname}</span>}
      </div>

      <div className={styles.number}>•••• •••• •••• {card.last_four}</div>

      <div className={styles.foot}>
        <div className={styles.stats}>
          <div>
            <div className={styles.statLabel}>이번 달 사용</div>
            <div className={styles.statValue}>
              {spent}
              <span className={styles.statUnit}>원</span>
            </div>
          </div>
          <div>
            <div className={styles.statLabel}>받은 혜택</div>
            <div className={`${styles.statValue} ${styles.gold}`}>
              {benefit}
              <span className={styles.statUnit}>원</span>
            </div>
          </div>
        </div>
        {expiry && <div className={styles.expiry}>EXP {expiry}</div>}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: `src/data/cards.js`에 표시용 목업 수치 추가**

카드 앞면의 "이번 달 사용 / 받은 혜택 / EXP"는 백엔드에 없는 값이다. 목업으로 채운다.
`WALLET_CARDS`의 각 원소에 세 필드를 추가한다:

```js
// 13번 신한카드 Mr.Life 에 추가
    spent: '318,000',
    benefit: '22,400',
    expiry: '12/27',

// 2262번 LOCA LIKIT Eat 에 추가
    spent: '506,000',
    benefit: '31,200',
    expiry: '03/28',

// 2261번 LOCA LIKIT 1.2 에 추가
    spent: '152,000',
    benefit: '9,800',
    expiry: '09/26',
```

- [ ] **Step 4: `src/screens/WalletHome.module.css` 작성**

```css
.screen {
  position: absolute;
  inset: 0;
  background: var(--bg-app);
  overflow-y: auto;
}

.header {
  padding: 62px 22px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand { display: flex; align-items: center; gap: 9px; }

.brandText {
  font-size: 22px;
  font-weight: 800;
  color: var(--navy-text);
  letter-spacing: -.6px;
}

.headerActions { display: flex; gap: 10px; }

.iconBtn {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  border: none;
  font-size: 22px;
  font-weight: 300;
  line-height: 1;
  background: var(--navy);
  color: #fff;
}

.iconBtn.light {
  background: #fff;
  color: var(--navy-text);
  box-shadow: 0 2px 8px rgba(14, 36, 93, .08);
  font-size: 17px;
}

.qrBar {
  margin: 4px 22px 8px;
  padding: 16px 18px;
  border-radius: 18px;
  background: var(--navy-grad);
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  border: none;
  width: calc(100% - 44px);
  box-shadow: var(--sh-raise);
  text-align: left;
}

.qrBarLabel { font-size: 13px; color: rgba(255, 255, 255, .6); font-weight: 500; }
.qrBarTitle { font-size: 17px; color: #fff; font-weight: 700; margin-top: 3px; }

.qrBarIcon {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex: none;
}

.qrBarIcon img { width: 38px; height: 38px; display: block; }

.stack { position: relative; margin: 14px 22px 0; }

.stackItem {
  position: absolute;
  left: 0;
  right: 0;
  cursor: pointer;
  transform-origin: center;
  transition: top .4s cubic-bezier(.22, .61, .36, 1),
              transform .28s ease,
              filter .28s ease;
}

.stackItem.selected {
  transform: scale(1.05) translateY(-6px);
  filter: drop-shadow(0 22px 34px rgba(10, 29, 79, .5));
}

.hint {
  text-align: center;
  padding: 22px 0 34px;
  font-size: 12.5px;
  color: var(--text-4);
  cursor: pointer;
}
```

- [ ] **Step 5: `src/screens/WalletHome.jsx` 작성**

```jsx
import { useEffect } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { fetchMyCards } from '../api/picka.js'
import CardFace from '../components/CardFace.jsx'
import { PickaMark } from './Splash.jsx'
import styles from './WalletHome.module.css'

const CARD_HEIGHT = 186
const OFFSET_COLLAPSED = 54 // 접힌 카드 간격
const OFFSET_EXPANDED = 176 // 펼친 카드 간격

export default function WalletHome() {
  const { state, dispatch } = useApp()
  const { cards, expanded, active } = state

  // 보유카드는 화면 진입 시 한 번만 불러옵니다.
  useEffect(() => {
    if (cards.length > 0) return
    let cancelled = false
    fetchMyCards().then((list) => {
      if (!cancelled) dispatch({ type: A.SET_CARDS, cards: list })
    })
    return () => {
      cancelled = true
    }
  }, [cards.length, dispatch])

  const offset = expanded ? OFFSET_EXPANDED : OFFSET_COLLAPSED
  const stackHeight = cards.length
    ? (cards.length - 1) * offset + CARD_HEIGHT + 8
    : 0

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.header}>
        <div className={styles.brand}>
          <PickaAppIcon />
          <span className={styles.brandText}>지갑</span>
        </div>
        <div className={styles.headerActions}>
          <button type="button" className={styles.iconBtn} aria-label="카드 등록">
            +
          </button>
          <button
            type="button"
            className={`${styles.iconBtn} ${styles.light}`}
            aria-label="결제수단 관리"
          >
            ☰
          </button>
        </div>
      </div>

      <button
        type="button"
        className={styles.qrBar}
        onClick={() => dispatch({ type: A.SET_SCREEN, screen: 'qr' })}
      >
        <div>
          <div className={styles.qrBarLabel}>바로 결제</div>
          <div className={styles.qrBarTitle}>QR 열기</div>
        </div>
        <div className={styles.qrBarIcon}>
          <img src="/assets/qr-code.png" alt="QR" />
        </div>
      </button>

      <div className={styles.stack} style={{ height: stackHeight }}>
        {cards.map((card, i) => {
          const selected = expanded && i === active
          return (
            <div
              key={card.card_id}
              className={`${styles.stackItem} ${selected ? styles.selected : ''}`}
              style={{ top: i * offset, zIndex: selected ? 20 : i }}
              onClick={() => dispatch({ type: A.SELECT_CARD, index: i })}
            >
              <CardFace
                card={card}
                variant="stack"
                spent={card.spent}
                benefit={card.benefit}
                expiry={card.expiry}
              />
            </div>
          )
        })}
      </div>

      <div
        className={styles.hint}
        onClick={() => dispatch({ type: A.TOGGLE_EXPANDED })}
      >
        {expanded ? '여기를 눌러 접기' : '카드를 탭해 펼쳐보세요'}
      </div>
    </div>
  )
}

/** 헤더용 앱 아이콘 (네이비 사각 배경 + 마크). */
function PickaAppIcon() {
  return (
    <svg width="26" height="26" viewBox="24 24 464 464">
      <rect x="24" y="24" width="464" height="464" rx="108" fill="#0E245D" />
      <g>
        <PickaMarkPaths />
      </g>
    </svg>
  )
}

function PickaMarkPaths() {
  return (
    <>
      <path
        d="M150 398V168C150 143.699 169.699 124 194 124H286C344.542 124 392 171.458 392 230C392 281.568 355.159 324.569 306.36 334.07L288 268C313.688 264.031 328 248.513 328 226C328 201.699 308.301 182 284 182H232C218.745 182 208 192.745 208 206V398H150Z"
        fill="#fff"
      />
      <path
        d="M150 324L278 287C297.562 281.343 317.956 292.79 322.586 312.623L332.7 355.938C337.415 376.13 322.955 395.905 302.31 397.94L150 413V324Z"
        fill="#2F6BFF"
      />
      <path
        d="M191 315L251 251.5C261.2 240.7 279.9 244.2 285.3 258.4L304 307.6C307.4 316.5 300.8 326 291.3 326H200.2C191.3 326 184.9 319.8 191 315Z"
        fill="#19D3C5"
      />
    </>
  )
}
```

`PickaMark` import가 이 파일에서 실제로 안 쓰이면 lint 경고가 날 수 있다. 위 코드는 `PickaMarkPaths`를 자체 정의하므로 **`import { PickaMark }` 줄을 삭제**한다.

- [ ] **Step 6: 브라우저 확인**

```bash
npm run dev
```

확인 항목:
1. 홈 헤더에 네이비 앱 아이콘 + "지갑", 오른쪽에 `+`(네이비)와 `☰`(흰색) 버튼.
2. "바로 결제 / QR 열기" 네이비 바 우측에 **QR 이미지**가 보인다 (깨진 아이콘이면 `public/assets/qr-code.png` 확인).
3. 카드 3장이 54px 간격으로 겹쳐 있다. 카드사·카드명·별칭 칩·`•••• •••• •••• 1234`·사용액/혜택/EXP가 보인다.
4. 카드를 탭하면 176px 간격으로 **펼쳐지고**, 누른 카드가 살짝 커지며 위로 뜬다.
5. 하단 문구가 "여기를 눌러 접기"로 바뀌고, 누르면 다시 접힌다.
6. "QR 열기"를 누르면 `QrScreen` 스텁으로 간다.

- [ ] **Step 7: 커밋**

```bash
cd "c:/Picka_Front/1st_project"
git add front_end/src/components/CardFace.jsx front_end/src/components/CardFace.module.css front_end/src/screens/WalletHome.jsx front_end/src/screens/WalletHome.module.css front_end/src/data/cards.js
git commit -m "카드 앞면 컴포넌트와 지갑 홈 카드 스택 구현"
```

---

## Task 6: QR 화면

**Files:**
- Create: `front_end/src/components/QrCode.jsx`, `front_end/src/components/QrCode.module.css`
- Modify: `front_end/src/screens/QrScreen.jsx` (스텁 → 실제)
- Create: `front_end/src/screens/QrScreen.module.css`

**Interfaces:**
- Consumes: `useApp()`, `A`, `MERCHANTS`, `CardFace`
- Produces:
  - `QrCode({ token, expiresIn, expired, onRefresh })` — 만료 시 오버레이와 새로고침 버튼을 자체 렌더

- [ ] **Step 1: `src/components/QrCode.module.css` 작성**

```css
.frame {
  position: relative;
  width: 262px;
  height: 262px;
  border-radius: 24px;
  background: #fff;
  padding: 18px;
  box-shadow: 0 30px 60px -20px rgba(0, 0, 0, .5);
}

.image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  transition: opacity .3s ease;
}

.expiredOverlay {
  position: absolute;
  inset: 0;
  border-radius: 24px;
  background: rgba(255, 255, 255, .94);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
}

.expiredText { font-size: 13.5px; font-weight: 600; color: var(--navy-text); }

.refresh {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(140deg, #10275F, #071844);
  color: #fff;
  font-size: 26px;
  box-shadow: 0 12px 26px -8px rgba(14, 36, 93, .5);
}

.refreshHint { font-size: 12px; color: var(--text-2); }
```

- [ ] **Step 2: `src/components/QrCode.jsx` 작성**

```jsx
import styles from './QrCode.module.css'

/**
 * 일회용 결제 QR.
 *
 * 지금은 디자인 핸드오프의 정적 이미지를 씁니다.
 * 결제서버가 QR을 발급하게 되면 <img src>를 서버 응답 이미지로 바꾸면 됩니다.
 * data-qr-* 속성은 그때 연동 지점을 찾기 쉽도록 남겨둡니다.
 *
 * @param {object} props
 * @param {string} props.token 일회용 토큰 (표시용 숫자열)
 * @param {number} props.expiresIn 남은 초
 * @param {boolean} props.expired 만료 여부
 * @param {() => void} props.onRefresh 새로고침 핸들러
 */
export default function QrCode({ token, expiresIn, expired, onRefresh }) {
  return (
    <div
      id="picka-qr"
      className={styles.frame}
      data-qr-token={token}
      data-qr-expires-in={expiresIn}
    >
      <img
        className={styles.image}
        src="/assets/qr-tight.png"
        alt="결제 QR 코드"
        style={{ opacity: expired ? 0.1 : 1 }}
      />

      {expired && (
        <div className={styles.expiredOverlay}>
          <div className={styles.expiredText}>QR이 만료되었어요</div>
          <button type="button" className={styles.refresh} onClick={onRefresh}>
            ↻
          </button>
          <div className={styles.refreshHint}>새로고침을 눌러 새 QR 발급</div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 3: `src/screens/QrScreen.module.css` 작성**

```css
.screen {
  position: absolute;
  inset: 0;
  background: linear-gradient(165deg, #10275F 0%, #071844 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.header {
  width: 100%;
  padding: 60px 24px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand { display: flex; align-items: center; gap: 8px; }

.brandText {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -1px;
  color: #fff;
}

.close {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, .14);
  color: #fff;
  font-size: 17px;
}

.cardChip {
  margin-top: 16px;
  padding: 8px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, .12);
  color: #fff;
  font-size: 13.5px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.cardSwatch {
  width: 26px;
  height: 16px;
  border-radius: 3px;
  display: inline-block;
  flex: none;
}

.qrWrap { margin-top: 22px; }

.token {
  margin-top: 22px;
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, .85);
  letter-spacing: 2px;
  font-variant-numeric: tabular-nums;
  text-align: center;
  padding: 0 24px;
}

.timer {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--gold);
}

.timer.expired { color: rgba(255, 255, 255, .45); }

.demoBtn {
  margin-top: auto;
  margin-bottom: 16px;
  height: 48px;
  padding: 0 22px;
  border: 1px solid rgba(255, 255, 255, .25);
  border-radius: var(--r-btn);
  background: rgba(255, 255, 255, .08);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

.footNote {
  margin-bottom: 40px;
  font-size: 12.5px;
  color: rgba(255, 255, 255, .4);
}
```

- [ ] **Step 4: `src/screens/QrScreen.jsx` 작성**

```jsx
import { useEffect, useState } from 'react'
import { useApp } from '../state/AppContext.jsx'
import { A } from '../state/appReducer.js'
import { MERCHANTS } from '../data/merchants.js'
import { gradientFor } from '../data/cards.js'
import QrCode from '../components/QrCode.jsx'
import styles from './QrScreen.module.css'

const QR_LIFETIME_SEC = 180

/** 일회용 QR 토큰(표시용 숫자열)을 만듭니다. 실제로는 결제서버가 발급합니다. */
function makeToken(seed) {
  let x = seed * 9301 + 49297
  let out = ''
  for (let i = 0; i < 24; i += 1) {
    x = (x * 1103515245 + 12345) & 0x7fffffff
    out += x % 10
    if (i % 4 === 3 && i < 23) out += ' '
  }
  return out
}

function pickMerchant() {
  return MERCHANTS[Math.floor(Math.random() * MERCHANTS.length)]
}

export default function QrScreen() {
  const { state, dispatch } = useApp()
  const [seconds, setSeconds] = useState(QR_LIFETIME_SEC)
  const [seed, setSeed] = useState(1)

  // 1초마다 카운트다운. 이 화면이 소유하는 타이머입니다.
  useEffect(() => {
    const timer = setInterval(() => {
      setSeconds((s) => Math.max(0, s - 1))
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  const expired = seconds <= 0
  const mm = Math.floor(seconds / 60)
  const ss = String(seconds % 60).padStart(2, '0')

  const card = state.cards[state.active] || state.cards[0]

  function refresh() {
    setSeconds(QR_LIFETIME_SEC)
    setSeed((s) => s + 1)
  }

  function recognize() {
    dispatch({ type: A.START_PAY, transaction: pickMerchant() })
  }

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.header}>
        <div className={styles.brand}>
          <QrMark />
          <span className={styles.brandText}>picka</span>
        </div>
        <button
          type="button"
          className={styles.close}
          onClick={() => dispatch({ type: A.SET_SCREEN, screen: 'home' })}
        >
          ✕
        </button>
      </div>

      {card && (
        <div className={styles.cardChip}>
          <span
            className={styles.cardSwatch}
            style={{ background: card.gradient || gradientFor(card.card_company) }}
          />
          {card.card_company} {card.card_name}
        </div>
      )}

      <div className={styles.qrWrap}>
        <QrCode
          token={makeToken(seed)}
          expiresIn={seconds}
          expired={expired}
          onRefresh={refresh}
        />
      </div>

      <div className={styles.token}>{makeToken(seed)}</div>

      <div className={`${styles.timer} ${expired ? styles.expired : ''}`}>
        <span>⏱</span>
        {expired ? '유효시간 만료' : `QR 유효시간 ${mm}:${ss}`}
      </div>

      <button type="button" className={styles.demoBtn} onClick={recognize}>
        🏪 매장에서 QR 인식됨 (데모)
      </button>
      <div className={styles.footNote}>화면을 매장 리더기에 인식시켜 주세요</div>
    </div>
  )
}

/** QR 화면 헤더용 흰색 마크. */
function QrMark() {
  return (
    <svg width="26" height="26" viewBox="150 124 242 289">
      <path
        d="M150 398V168C150 143.699 169.699 124 194 124H286C344.542 124 392 171.458 392 230C392 281.568 355.159 324.569 306.36 334.07L288 268C313.688 264.031 328 248.513 328 226C328 201.699 308.301 182 284 182H232C218.745 182 208 192.745 208 206V398H150Z"
        fill="#fff"
      />
      <path
        d="M150 324L278 287C297.562 281.343 317.956 292.79 322.586 312.623L332.7 355.938C337.415 376.13 322.955 395.905 302.31 397.94L150 413V324Z"
        fill="#2F6BFF"
      />
      <path
        d="M191 315L251 251.5C261.2 240.7 279.9 244.2 285.3 258.4L304 307.6C307.4 316.5 300.8 326 291.3 326H200.2C191.3 326 184.9 319.8 191 315Z"
        fill="#19D3C5"
      />
    </svg>
  )
}
```

- [ ] **Step 5: 브라우저 확인**

```bash
npm run dev
```

확인 항목:
1. 홈에서 "QR 열기" → 네이비 전체화면. 상단에 `picka` + 닫기 버튼.
2. 선택된 카드 칩("신한카드 신한카드 Mr.Life")이 색 스와치와 함께 보인다.
3. **흰 카드 안에 QR 이미지**가 262px로 보인다.
4. 그 아래 24자리 숫자 토큰, 그 아래 금색 "QR 유효시간 3:00"이 **1초마다 줄어든다**.
5. 개발자도구 Elements에서 `#picka-qr`에 `data-qr-token`, `data-qr-expires-in` 속성이 붙어 있다.
6. 만료 확인: `QR_LIFETIME_SEC`을 잠시 `3`으로 바꿔 저장 → 3초 뒤 QR이 흐려지고 "QR이 만료되었어요" + 새로고침 버튼. 누르면 복구. **확인 후 값을 180으로 되돌린다.**
7. "매장에서 QR 인식됨 (데모)" → `PayReceived` 스텁으로 간다.

- [ ] **Step 6: 커밋**

```bash
cd "c:/Picka_Front/1st_project"
git add front_end/src/components/QrCode.jsx front_end/src/components/QrCode.module.css front_end/src/screens/QrScreen.jsx front_end/src/screens/QrScreen.module.css
git commit -m "QR 전체화면과 일회용 QR 컴포넌트 구현

180초 카운트다운·만료 오버레이·새로고침 포함.
data-qr-token / data-qr-expires-in 은 결제서버 연동 지점으로 남겨둠."
```

---

## Task 7: 거래정보 확인 · AI 분석 (추천 API 호출)

**Files:**
- Modify: `front_end/src/screens/pay/PayReceived.jsx` (스텁 → 실제)
- Create: `front_end/src/screens/pay/PayReceived.module.css`
- Modify: `front_end/src/screens/pay/PayAnalyzing.jsx` (스텁 → 실제)
- Create: `front_end/src/screens/pay/PayAnalyzing.module.css`
- Create: `front_end/src/screens/pay/payShared.module.css`

**Interfaces:**
- Consumes: `useApp()`, `A`, `fetchRecommendation`, `ApiError`, `won`
- Produces: `payShared.module.css`의 클래스 `.screen`, `.brandRow`, `.panel` — Task 8~10이 재사용

- [ ] **Step 1: `src/screens/pay/payShared.module.css` 작성**

결제 화면 7개가 공유하는 껍데기다.

```css
.screen {
  position: absolute;
  inset: 0;
  z-index: 44;
  background: var(--pay-dark);
  overflow-y: auto;
  padding: 0 22px;
}

.brandRow {
  padding: 60px 0 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 800;
  color: #fff;
}

.brandRow.end { justify-content: flex-end; }

.panel {
  background: rgba(255, 255, 255, .05);
  border: 1px solid rgba(255, 255, 255, .08);
  border-radius: 16px;
  padding: 16px 18px;
}

.rowBetween {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.muted { color: rgba(255, 255, 255, .5); font-size: 13px; }

.primaryBtn {
  width: 100%;
  height: 54px;
  border: none;
  border-radius: 15px;
  background: linear-gradient(90deg, #2F6BFF, #6ea6ff);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  box-shadow: 0 14px 28px -10px rgba(47, 107, 255, .6);
}

.ghostBtn {
  width: 100%;
  height: 52px;
  border: 1px solid rgba(255, 255, 255, .15);
  border-radius: 15px;
  background: transparent;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
}
```

- [ ] **Step 2: `src/screens/pay/PayReceived.module.css` 작성**

```css
.title {
  margin-top: 20px;
  font-size: 22px;
  font-weight: 800;
  color: #fff;
  letter-spacing: -.5px;
}

.sub { margin-top: 8px; font-size: 13.5px; color: rgba(255, 255, 255, .5); }

.panelWrap { margin-top: 22px; }

.meta {
  display: flex;
  justify-content: space-between;
  font-size: 10.5px;
  letter-spacing: 1px;
  color: rgba(255, 255, 255, .4);
}

.merchant {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, .08);
}

.merchantIcon {
  width: 40px;
  height: 40px;
  border-radius: 11px;
  background: rgba(47, 107, 255, .15);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex: none;
}

.merchantName { font-size: 15px; font-weight: 700; color: #fff; }
.merchantLoc { font-size: 11.5px; color: rgba(255, 255, 255, .45); }

.line { margin-top: 14px; }
.lineValue { font-size: 13.5px; color: #fff; }

.amount { font-size: 20px; font-weight: 800; color: #fff; }
.amountUnit { font-size: 13px; font-weight: 600; }

.loadingWrap {
  margin-top: 34px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}

.spinner {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  border-top: 2px solid var(--blue-light);
  border-right: 2px solid transparent;
  border-bottom: 2px solid transparent;
  border-left: 2px solid transparent;
  animation: pk-spin 1s linear infinite;
}

.loadingText { font-size: 13px; color: rgba(255, 255, 255, .55); }
```

- [ ] **Step 3: `src/screens/pay/PayReceived.jsx` 작성**

```jsx
import { useEffect } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import shared from './payShared.module.css'
import styles from './PayReceived.module.css'

const HOLD_MS = 1900

export default function PayReceived() {
  const { state, dispatch } = useApp()
  const tx = state.transaction

  // 거래정보를 잠깐 보여준 뒤 분석 화면으로 넘깁니다.
  useEffect(() => {
    const timer = setTimeout(
      () => dispatch({ type: A.SET_PAY_STEP, payStep: 'analyzing' }),
      HOLD_MS,
    )
    return () => clearTimeout(timer)
  }, [dispatch])

  if (!tx) return null

  return (
    <div className={`${shared.screen} pk-screen`}>
      <div className={shared.brandRow}>picka</div>

      <div className={styles.title}>거래 정보를 확인했습니다.</div>
      <div className={styles.sub}>결제 내용을 확인하고 잠시만 기다려주세요.</div>

      <div className={styles.panelWrap}>
        <div className={shared.panel}>
          <div className={styles.meta}>
            <span>MERCHANT</span>
            <span>ID · 482910</span>
          </div>

          <div className={styles.merchant}>
            <div className={styles.merchantIcon}>{tx.emoji}</div>
            <div>
              <div className={styles.merchantName}>{tx.merchant_name}</div>
              <div className={styles.merchantLoc}>Seoul, Republic of Korea</div>
            </div>
          </div>

          <div className={`${shared.rowBetween} ${styles.line}`}>
            <span className={shared.muted}>업종</span>
            <span className={styles.lineValue}>{tx.payment_category}</span>
          </div>

          <div className={`${shared.rowBetween} ${styles.line}`}>
            <span className={shared.muted}>결제 금액</span>
            <span className={styles.amount}>
              {tx.payment_amount.toLocaleString('ko-KR')}
              <span className={styles.amountUnit}>원</span>
            </span>
          </div>
        </div>
      </div>

      <div className={styles.loadingWrap}>
        <div className={styles.spinner} />
        <div className={styles.loadingText}>결제 정보를 불러오는 중…</div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: `src/screens/pay/PayAnalyzing.module.css` 작성**

```css
.orbWrap { margin-top: 26px; display: flex; justify-content: center; }

.orb {
  position: relative;
  width: 150px;
  height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ring1 { position: absolute; inset: 0; border-radius: 50%; border: 1px solid rgba(110, 166, 255, .25); }
.ring2 { position: absolute; inset: 18px; border-radius: 50%; border: 1px solid rgba(110, 166, 255, .2); }

.spin {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border-top: 2px solid var(--blue-light);
  border-right: 2px solid transparent;
  border-bottom: 2px solid transparent;
  border-left: 2px solid transparent;
  animation: pk-spin 1.2s linear infinite;
}

.core {
  width: 74px;
  height: 74px;
  border-radius: 50%;
  background: linear-gradient(140deg, #16294f, #0c1a3a);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  animation: pk-float 2.4s ease-in-out infinite;
}

.head { text-align: center; margin-top: 22px; }
.headTitle { font-size: 22px; font-weight: 800; color: #fff; }
.headSub { font-size: 13px; color: rgba(255, 255, 255, .5); margin-top: 8px; line-height: 1.5; }

.list {
  margin-top: 26px;
  background: rgba(255, 255, 255, .05);
  border: 1px solid rgba(255, 255, 255, .08);
  border-radius: 16px;
  padding: 8px 18px;
}

.item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 0;
  border-bottom: 1px solid rgba(255, 255, 255, .05);
}

.item:last-child { border-bottom: none; }

.mark { font-size: 16px; }
.itemName { flex: 1; font-size: 13.5px; color: rgba(255, 255, 255, .82); }
.itemStatus { font-size: 12px; font-weight: 600; }

.barWrap { margin-top: 26px; padding-top: 22px; padding-bottom: 40px; }

.barTrack {
  height: 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, .1);
  overflow: hidden;
}

.barFill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #2F6BFF, #6ea6ff);
  transition: width .5s ease;
}

.barNote {
  margin-top: 12px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 11.5px;
  color: rgba(255, 255, 255, .45);
  line-height: 1.5;
}
```

- [ ] **Step 5: `src/screens/pay/PayAnalyzing.jsx` 작성**

여기서 백엔드 추천을 호출한다. 최소 표시 시간과 API 응답 중 **늦은 쪽**을 기다린 뒤 다음 화면으로 간다.

```jsx
import { useEffect, useState } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { fetchRecommendation } from '../../api/picka.js'
import shared from './payShared.module.css'
import styles from './PayAnalyzing.module.css'

const STEP_LABELS = ['카드 혜택 조회', '할인 계산', '적립 계산', '최적 카드 선택']
const STEP_INTERVAL_MS = 620
const MIN_DURATION_MS = 2900

export default function PayAnalyzing() {
  const { state, dispatch } = useApp()
  const [step, setStep] = useState(0)

  // 체크리스트 진행 애니메이션
  useEffect(() => {
    const timer = setInterval(() => {
      setStep((s) => {
        if (s >= STEP_LABELS.length) {
          clearInterval(timer)
          return s
        }
        return s + 1
      })
    }, STEP_INTERVAL_MS)
    return () => clearInterval(timer)
  }, [])

  // 추천 API 호출. 최소 표시 시간을 함께 기다립니다.
  useEffect(() => {
    if (!state.transaction) return
    let cancelled = false

    async function run() {
      const minDelay = new Promise((resolve) => setTimeout(resolve, MIN_DURATION_MS))

      let data = null
      let failure = null
      try {
        data = await fetchRecommendation(state.transaction)
      } catch (err) {
        failure = err
      }

      await minDelay
      if (cancelled) return

      if (failure) {
        // 404는 "혜택 카드 없음" 안내로 구분합니다. 오류가 아닙니다.
        if (failure.status === 404) dispatch({ type: A.SET_NO_ELIGIBLE })
        else {
          dispatch({
            type: A.SET_ERROR,
            message: failure.message || '추천 결과를 불러오지 못했습니다.',
          })
        }
      } else {
        dispatch({ type: A.SET_RESULT, result: data })
      }

      dispatch({ type: A.SET_PAY_STEP, payStep: 'recommend' })
    }

    run()
    return () => {
      cancelled = true
    }
  }, [state.transaction, dispatch])

  const cardCount = state.cards.length

  return (
    <div className={`${shared.screen} pk-screen`}>
      <div className={`${shared.brandRow} ${shared.end}`}>picka</div>

      <div className={styles.orbWrap}>
        <div className={styles.orb}>
          <div className={styles.ring1} />
          <div className={styles.ring2} />
          <div className={styles.spin} />
          <div className={styles.core}>🧠</div>
        </div>
      </div>

      <div className={styles.head}>
        <div className={styles.headTitle}>AI 분석 중</div>
        <div className={styles.headSub}>
          현재 고객님께 가장 유리한 혜택을
          <br />
          계산하고 있습니다.
        </div>
      </div>

      <div className={styles.list}>
        {STEP_LABELS.map((label, i) => {
          const done = i < step
          const active = i === step
          const mark = done ? '✓' : active ? '◐' : '○'
          const markColor = done
            ? 'var(--green-pay)'
            : active
              ? 'var(--blue-light)'
              : 'rgba(255,255,255,.3)'
          const status = done ? '완료' : active ? '진행중' : '대기'
          const statusColor = done ? 'var(--green-pay)' : 'rgba(255,255,255,.4)'

          return (
            <div className={styles.item} key={label}>
              <span className={styles.mark} style={{ color: markColor }}>
                {mark}
              </span>
              <span className={styles.itemName}>{label}</span>
              <span className={styles.itemStatus} style={{ color: statusColor }}>
                {status}
              </span>
            </div>
          )
        })}
      </div>

      <div className={styles.barWrap}>
        <div className={styles.barTrack}>
          <div
            className={styles.barFill}
            style={{ width: `${(step / STEP_LABELS.length) * 100}%` }}
          />
        </div>
        <div className={styles.barNote}>
          <span>✦</span>
          <span>등록한 카드 {cardCount}장의 혜택을 비교하고 있어요.</span>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 6: 백엔드를 켠 상태로 확인**

터미널 두 개가 필요하다.

```bash
# 터미널 1 — 백엔드 (1st_project 상위에서 실행)
cd "c:/Picka_Front/1st_project"
python -m uvicorn backend.main:app --reload --port 8000
```

```bash
# 터미널 2 — 프론트
cd "c:/Picka_Front/1st_project/front_end"
npm run dev
```

확인 항목:
1. 로그인 → 홈 → QR 열기 → "매장에서 QR 인식됨".
2. **거래정보 화면**에 랜덤 가맹점(이모지·이름·업종·금액)이 뜨고 약 1.9초 유지된다.
3. **AI 분석 화면**으로 넘어가 체크리스트 4개가 620ms 간격으로 `대기 → 진행중 → 완료`로 바뀌고 하단 바가 0→100%로 찬다.
4. 약 2.9초 후 `PayRecommend` 스텁으로 넘어간다.
5. 브라우저 Network 탭에 `POST /api/v1/recommendations`가 **200**으로 찍힌다.
6. React DevTools가 없다면, `PayRecommend` 스텁에 `console.log`를 잠시 넣어 `state.result.recommended_card`가 채워졌는지 확인한다.

- [ ] **Step 7: 백엔드를 끈 상태로 오류 경로 확인**

터미널 1의 uvicorn을 `Ctrl+C`로 끄고 결제를 다시 시도한다.

기대: 분석 화면이 **멈추지 않고** 2.9초 후 `PayRecommend` 스텁으로 넘어간다. `state.error`에 메시지가 들어 있다. 확인 후 백엔드를 다시 켠다.

- [ ] **Step 8: 커밋**

```bash
cd "c:/Picka_Front/1st_project"
git add front_end/src/screens/pay/
git commit -m "거래정보 확인·AI 분석 화면 구현 및 추천 API 연동

분석 화면에서 POST /api/v1/recommendations 호출.
최소 2.9초 표시를 보장하고 404는 혜택없음 안내로 분기."
```

---

## Task 8: 추천 결과 화면 (바텀시트 포함)

**Files:**
- Modify: `front_end/src/screens/pay/PayRecommend.jsx` (스텁 → 실제)
- Create: `front_end/src/screens/pay/PayRecommend.module.css`

**Interfaces:**
- Consumes: `useApp()`, `A`, `sortByBenefit`, `gradientFor`, `shared` CSS
- Produces: 없음

- [ ] **Step 1: `src/screens/pay/PayRecommend.module.css` 작성**

```css
.screen {
  position: absolute;
  inset: 0;
  z-index: 44;
  background: var(--pay-dark);
}

.scroll {
  position: absolute;
  inset: 0;
  overflow-y: auto;
  padding: 0 22px 340px;
}

.badgeRow { text-align: center; margin-top: 8px; }

.badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--blue-light);
  background: rgba(47, 107, 255, .15);
  border: 1px solid rgba(47, 107, 255, .3);
  padding: 5px 12px;
  border-radius: 20px;
}

.title { text-align: center; margin-top: 16px; font-size: 22px; font-weight: 800; color: #fff; }

.lead {
  text-align: center;
  margin-top: 8px;
  font-size: 13px;
  color: rgba(255, 255, 255, .55);
  line-height: 1.5;
}

.bigCard {
  margin-top: 20px;
  height: 180px;
  border-radius: 18px;
  box-shadow: 0 22px 40px -18px rgba(10, 29, 79, .7);
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: #fff;
}

.bigCardHead { display: flex; justify-content: space-between; align-items: flex-start; }
.bigCardCompany { font-size: 11px; color: rgba(255, 255, 255, .6); }
.bigCardName { font-size: 16px; font-weight: 700; margin-top: 1px; }
.bigCardBrand { font-size: 13px; font-weight: 700; letter-spacing: 1px; color: rgba(255, 255, 255, .8); }
.bigCardNumber { font-size: 16px; letter-spacing: 3px; color: rgba(255, 255, 255, .8); }

.stats { display: flex; gap: 10px; margin-top: 14px; }

.stat {
  flex: 1;
  background: rgba(255, 255, 255, .05);
  border: 1px solid rgba(255, 255, 255, .08);
  border-radius: var(--r-btn);
  padding: 13px 14px;
}

.statLabel { font-size: 11px; color: rgba(255, 255, 255, .5); }
.statValue { font-size: 18px; font-weight: 800; margin-top: 4px; }
.statValue.good { color: var(--green-pay); }
.statValue.plain { color: #fff; }
.statNote { font-size: 10.5px; color: rgba(255, 255, 255, .4); margin-top: 2px; }

.reason {
  margin-top: 12px;
  background: rgba(255, 255, 255, .04);
  border-radius: var(--r-btn);
  padding: 13px 14px;
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.reasonText { font-size: 12px; color: rgba(255, 255, 255, .6); line-height: 1.5; }

/* 오류·혜택없음 안내 */
.notice {
  margin-top: 20px;
  background: rgba(255, 255, 255, .05);
  border: 1px solid rgba(255, 255, 255, .1);
  border-radius: 18px;
  padding: 24px 20px;
  text-align: center;
}

.noticeIcon { font-size: 30px; }
.noticeTitle { margin-top: 12px; font-size: 16px; font-weight: 700; color: #fff; }
.noticeBody { margin-top: 8px; font-size: 13px; color: rgba(255, 255, 255, .55); line-height: 1.5; }

.retry {
  margin-top: 16px;
  height: 44px;
  padding: 0 22px;
  border: 1px solid rgba(255, 255, 255, .2);
  border-radius: var(--r-btn);
  background: rgba(255, 255, 255, .08);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

/* 바텀시트 */
.scrim {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  top: 38%;
  pointer-events: none;
  background: linear-gradient(180deg, transparent, rgba(6, 11, 24, .55) 40%);
}

.sheet {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  max-height: 62%;
  display: flex;
  flex-direction: column;
  background: rgba(16, 23, 44, .86);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, .1);
  border-bottom: none;
  border-radius: 24px 24px 0 0;
  box-shadow: 0 -12px 40px -8px rgba(0, 0, 0, .55);
  animation: pk-up .35s cubic-bezier(.22, .61, .36, 1);
}

.sheetHead { padding: 14px 20px 6px; flex: none; }

.grabber {
  width: 40px;
  height: 4px;
  border-radius: 3px;
  background: rgba(255, 255, 255, .25);
  margin: 0 auto 14px;
}

.sheetTitle { font-size: 16px; font-weight: 800; color: #fff; }
.sheetSub { margin-top: 4px; font-size: 12.5px; color: rgba(255, 255, 255, .5); }

.sheetList {
  flex: 1;
  overflow-y: auto;
  padding: 8px 20px 4px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: var(--r-btn);
  cursor: pointer;
  background: rgba(255, 255, 255, .05);
  border: 1px solid rgba(255, 255, 255, .08);
}

.row.selected {
  background: rgba(47, 107, 255, .16);
  border-color: rgba(110, 166, 255, .6);
}

.row.dim { opacity: .55; }

.rank {
  width: 24px;
  height: 24px;
  flex: none;
  border-radius: 50%;
  background: rgba(47, 107, 255, .2);
  color: var(--blue-light);
  font-size: 12px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.swatch { width: 42px; height: 28px; border-radius: 6px; flex: none; }

.rowMain { flex: 1; min-width: 0; }

.rowName {
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rowSub { font-size: 11.5px; color: rgba(255, 255, 255, .45); margin-top: 1px; }
.rowRight { text-align: right; flex: none; }
.rowAmount { font-size: 15px; font-weight: 800; color: var(--blue-light); }
.rowNote { font-size: 10px; color: rgba(255, 255, 255, .4); }

.sheetFoot {
  flex: none;
  padding: 12px 20px 26px;
  border-top: 1px solid rgba(255, 255, 255, .08);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
```

- [ ] **Step 2: `src/screens/pay/PayRecommend.jsx` 작성**

```jsx
import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { sortByBenefit } from '../../utils/compare.js'
import { gradientFor } from '../../data/cards.js'
import shared from './payShared.module.css'
import styles from './PayRecommend.module.css'

const KRW = (n) => Number(n || 0).toLocaleString('ko-KR')

export default function PayRecommend() {
  const { state, dispatch } = useApp()
  const { transaction, result, error, noEligibleCard, payIdx } = state

  const ranked = sortByBenefit(result?.comparison)
  const chosen = ranked[payIdx] || ranked[0] || null
  const amount = transaction?.payment_amount || 0
  const discount = chosen?.expected_benefit || 0

  function retry() {
    // 분석 화면으로 되돌리면 추천 API가 다시 호출됩니다.
    dispatch({ type: A.SET_PAY_STEP, payStep: 'analyzing' })
  }

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.scroll}>
        <div className={`${shared.brandRow} ${shared.end}`}>picka</div>

        {error && <ErrorNotice message={error} onRetry={retry} />}

        {noEligibleCard && (
          <div className={styles.notice}>
            <div className={styles.noticeIcon}>💡</div>
            <div className={styles.noticeTitle}>이 업종엔 혜택 카드가 없어요</div>
            <div className={styles.noticeBody}>
              {transaction?.payment_category} 업종에 적용되는 혜택이 없습니다.
              <br />
              아래에서 아무 카드로나 결제하세요.
            </div>
          </div>
        )}

        {chosen && !error && (
          <>
            <div className={styles.badgeRow}>
              <span className={styles.badge}>✦ SMART SUGGESTION</span>
            </div>

            <div className={styles.title}>AI 추천 카드</div>

            <div className={styles.lead}>
              {chosen.card_company}가 {transaction?.payment_category}에서
              {' '}
              {chosen.benefit_rate ? `${chosen.benefit_rate}% 할인` : '가장 큰 혜택'}으로
              <br />
              혜택이 가장 좋아요. 이 카드로 결제할까요?
            </div>

            <div
              className={styles.bigCard}
              style={{ background: gradientFor(chosen.card_company) }}
            >
              <div className={styles.bigCardHead}>
                <div>
                  <div className={styles.bigCardCompany}>{chosen.card_company}</div>
                  <div className={styles.bigCardName}>{chosen.card_name}</div>
                </div>
                <span className={styles.bigCardBrand}>VISA</span>
              </div>
              <div className={styles.bigCardNumber}>
                •••• •••• •••• {chosen.last_four}
              </div>
            </div>

            <div className={styles.stats}>
              <div className={styles.stat}>
                <div className={styles.statLabel}>🏷 할인 혜택</div>
                <div className={`${styles.statValue} ${styles.good}`}>
                  -{KRW(discount)}원
                </div>
                <div className={styles.statNote}>{transaction?.payment_category}</div>
              </div>
              <div className={styles.stat}>
                <div className={styles.statLabel}>최종 승인 금액</div>
                <div className={`${styles.statValue} ${styles.plain}`}>
                  {KRW(amount - discount)}원
                </div>
                <div className={styles.statNote}>정가 {KRW(amount)}원</div>
              </div>
            </div>

            <div className={styles.reason}>
              <span style={{ fontSize: 15 }}>💡</span>
              <span className={styles.reasonText}>추천 이유 · {chosen.reason}</span>
            </div>
          </>
        )}
      </div>

      <div className={styles.scrim} />

      <div className={styles.sheet}>
        <div className={styles.sheetHead}>
          <div className={styles.grabber} />
          <div className={styles.sheetTitle}>다른 카드로 결제하기</div>
          <div className={styles.sheetSub}>
            혜택 순서대로 정렬했어요. 원하는 카드를 선택하세요.
          </div>
        </div>

        <div className={styles.sheetList}>
          {ranked.map((card, i) => (
            <div
              key={card.card_id}
              className={[
                styles.row,
                i === payIdx ? styles.selected : '',
                card.eligible ? '' : styles.dim,
              ].join(' ')}
              onClick={() => dispatch({ type: A.SELECT_PAY_CARD, index: i })}
            >
              <span className={styles.rank}>{i + 1}</span>
              <div
                className={styles.swatch}
                style={{ background: gradientFor(card.card_company) }}
              />
              <div className={styles.rowMain}>
                <div className={styles.rowName}>
                  {card.card_company} {card.card_name}
                </div>
                <div className={styles.rowSub}>
                  {card.eligible
                    ? `할인 -${KRW(card.expected_benefit)}원`
                    : '적용 가능한 혜택 없음'}
                </div>
              </div>
              <div className={styles.rowRight}>
                <div className={styles.rowAmount}>
                  {KRW(amount - (card.expected_benefit || 0))}원
                </div>
                <div className={styles.rowNote}>결제 예상</div>
              </div>
            </div>
          ))}
        </div>

        <div className={styles.sheetFoot}>
          <button
            type="button"
            className={shared.primaryBtn}
            disabled={!chosen}
            onClick={() => dispatch({ type: A.SET_PAY_STEP, payStep: 'confirm' })}
          >
            이 카드로 결제
          </button>
          <button
            type="button"
            className={shared.ghostBtn}
            onClick={() => dispatch({ type: A.RESET_PAY })}
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    </div>
  )
}

function ErrorNotice({ message, onRetry }) {
  return (
    <div className={styles.notice}>
      <div className={styles.noticeIcon}>⚠️</div>
      <div className={styles.noticeTitle}>추천을 불러오지 못했어요</div>
      <div className={styles.noticeBody}>{message}</div>
      <button type="button" className={styles.retry} onClick={onRetry}>
        다시 시도
      </button>
    </div>
  )
}
```

- [ ] **Step 3: 백엔드 켠 상태로 확인**

```bash
npm run dev   # 백엔드도 켜둔 상태
```

확인 항목:
1. 분석 후 추천 화면 진입. `✦ SMART SUGGESTION` 배지 + "AI 추천 카드".
2. 추천 카드의 카드사·카드명·`•••• 1234`가 백엔드 응답과 같다.
3. "할인 혜택 -N원", "최종 승인 금액"이 계산되어 보인다.
4. 하단 바텀시트가 아래에서 올라오고, 카드가 **혜택 큰 순서**로 1·2·3 랭크와 함께 정렬돼 있다.
5. 혜택이 0원인 카드는 흐리게 표시되고 "적용 가능한 혜택 없음"이 뜬다.
6. 다른 카드를 누르면 그 행이 파랗게 선택되고, **위쪽 추천 카드/할인/최종금액이 그 카드로 바뀐다**.
7. "이 카드로 결제" → `PayConfirm` 스텁.
8. "홈으로 돌아가기" → 홈.

- [ ] **Step 4: 백엔드 끈 상태로 오류 표시 확인**

uvicorn을 끄고 결제를 다시 시도한다.

기대: 추천 화면 위쪽에 ⚠️ "추천을 불러오지 못했어요" + 메시지 + "다시 시도" 버튼. 바텀시트는 비어 있고 "이 카드로 결제"가 비활성화된다. 백엔드를 켠 뒤 "다시 시도"를 누르면 분석 화면을 거쳐 정상 결과가 나온다.

- [ ] **Step 5: 커밋**

```bash
cd "c:/Picka_Front/1st_project"
git add front_end/src/screens/pay/PayRecommend.jsx front_end/src/screens/pay/PayRecommend.module.css
git commit -m "AI 추천 결과 화면과 카드 선택 바텀시트 구현

comparison[]을 혜택순으로 정렬해 표시하고 선택 시 최종금액을 재계산.
호출 실패와 혜택없음(404)을 각각 다른 안내로 표시."
```

---

## Task 9: 결제 확인 · Face ID

**Files:**
- Modify: `front_end/src/screens/pay/PayConfirm.jsx` (스텁 → 실제)
- Create: `front_end/src/screens/pay/PayConfirm.module.css`
- Modify: `front_end/src/screens/pay/PayFaceId.jsx` (스텁 → 실제)
- Create: `front_end/src/screens/pay/PayFaceId.module.css`

**Interfaces:**
- Consumes: `useApp()`, `A`, `sortByBenefit`, `gradientFor`, `shared` CSS
- Produces: 없음

`App.jsx`(Task 2)는 `payStep === 'faceid'`일 때 `PayConfirm`을 함께 렌더한다. `PayFaceId`는 그 위를 덮는 반투명 오버레이다.

- [ ] **Step 1: `src/screens/pay/PayConfirm.module.css` 작성**

```css
.shieldWrap {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}

.shield {
  position: relative;
  width: 96px;
  height: 96px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.shieldRing { position: absolute; inset: 0; border-radius: 50%; border: 1px solid rgba(110, 166, 255, .25); }

.shieldGlow {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(47, 107, 255, .3), transparent 70%);
  animation: pk-ring 2s ease-in-out infinite;
}

.shieldCore {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(140deg, #16294f, #0c1a3a);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.shieldTitle { font-size: 17px; font-weight: 800; color: #fff; text-align: center; }
.shieldSub { font-size: 12px; color: rgba(255, 255, 255, .45); margin-top: 4px; text-align: center; }

.panelWrap { margin-top: 24px; }

.cardRow {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, .08);
}

.swatch { width: 42px; height: 28px; border-radius: 6px; flex: none; }
.cardLabel { font-size: 10.5px; color: rgba(255, 255, 255, .45); }
.cardName { font-size: 14.5px; font-weight: 700; color: #fff; }
.check { color: var(--green-pay); font-size: 16px; }

.line { margin-top: 14px; font-size: 13px; }
.lineValue { color: #fff; font-weight: 600; }
.lineGood { color: var(--green-pay); font-weight: 700; }

.total {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, .08);
}

.totalLabel { font-size: 14px; font-weight: 700; color: #fff; }
.totalValue { font-size: 26px; font-weight: 800; color: var(--blue-light); }
.totalUnit { font-size: 14px; }

.reason {
  margin-top: 14px;
  background: rgba(47, 107, 255, .1);
  border-radius: 12px;
  padding: 11px 13px;
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.reasonText { font-size: 11.5px; color: rgba(255, 255, 255, .55); line-height: 1.5; }

.actions { margin-top: 20px; padding-bottom: 40px; display: flex; flex-direction: column; gap: 10px; }
```

- [ ] **Step 2: `src/screens/pay/PayConfirm.jsx` 작성**

```jsx
import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { sortByBenefit } from '../../utils/compare.js'
import { gradientFor } from '../../data/cards.js'
import shared from './payShared.module.css'
import styles from './PayConfirm.module.css'

const KRW = (n) => Number(n || 0).toLocaleString('ko-KR')

export default function PayConfirm() {
  const { state, dispatch } = useApp()
  const { transaction, result, payIdx, payStep } = state

  const ranked = sortByBenefit(result?.comparison)
  const chosen = ranked[payIdx] || ranked[0]
  const amount = transaction?.payment_amount || 0
  const discount = chosen?.expected_benefit || 0

  // faceid 단계에서는 이 화면이 배경으로만 깔립니다. 버튼을 못 누르게 막습니다.
  const asBackdrop = payStep === 'faceid'

  if (!chosen) return null

  return (
    <div
      className={`${shared.screen} pk-screen`}
      style={asBackdrop ? { pointerEvents: 'none' } : undefined}
    >
      <div className={shared.brandRow} style={{ justifyContent: 'space-between' }}>
        <span>picka</span>
        <span
          style={{
            fontSize: 11,
            fontWeight: 400,
            color: 'rgba(255,255,255,.5)',
            background: 'rgba(255,255,255,.08)',
            padding: '4px 10px',
            borderRadius: 8,
          }}
        >
          결제 확인
        </span>
      </div>

      <div className={styles.shieldWrap}>
        <div className={styles.shield}>
          <div className={styles.shieldRing} />
          <div className={styles.shieldGlow} />
          <div className={styles.shieldCore}>🛡️</div>
        </div>
        <div>
          <div className={styles.shieldTitle}>안전한 결제 환경</div>
          <div className={styles.shieldSub}>실시간 보안 프로토콜 활성화됨</div>
        </div>
      </div>

      <div className={styles.panelWrap}>
        <div className={shared.panel}>
          <div className={styles.cardRow}>
            <div
              className={styles.swatch}
              style={{ background: gradientFor(chosen.card_company) }}
            />
            <div style={{ flex: 1 }}>
              <div className={styles.cardLabel}>선택된 카드</div>
              <div className={styles.cardName}>
                {chosen.card_company} {chosen.card_name}
              </div>
            </div>
            <span className={styles.check}>✓</span>
          </div>

          <div className={`${shared.rowBetween} ${styles.line}`}>
            <span className={shared.muted}>결제 금액</span>
            <span className={styles.lineValue}>{KRW(amount)}원</span>
          </div>

          <div className={`${shared.rowBetween} ${styles.line}`}>
            <span className={shared.muted}>할인 혜택</span>
            <span className={styles.lineGood}>-{KRW(discount)}원</span>
          </div>

          <div className={styles.total}>
            <span className={styles.totalLabel}>최종 결제 금액</span>
            <span className={styles.totalValue}>
              {KRW(amount - discount)}
              <span className={styles.totalUnit}>원</span>
            </span>
          </div>

          <div className={styles.reason}>
            <span style={{ fontSize: 13 }}>✦</span>
            <span className={styles.reasonText}>{chosen.reason}</span>
          </div>
        </div>
      </div>

      <div className={styles.actions}>
        <button
          type="button"
          className={shared.primaryBtn}
          onClick={() => dispatch({ type: A.SET_PAY_STEP, payStep: 'faceid' })}
        >
          🔒 결제하기
        </button>
        <button
          type="button"
          className={shared.ghostBtn}
          onClick={() => dispatch({ type: A.SET_PAY_STEP, payStep: 'recommend' })}
        >
          다른 카드 선택
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: `src/screens/pay/PayFaceId.module.css` 작성**

```css
.overlay {
  position: absolute;
  inset: 0;
  z-index: 60;
  background: rgba(4, 7, 16, .82);
  backdrop-filter: blur(6px);
  overflow: hidden;
}

.island {
  position: absolute;
  top: 14px;
  left: 50%;
  transform: translateX(-50%);
  width: 108px;
  height: 108px;
  border-radius: 30px;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 18px 40px -8px rgba(0, 0, 0, .85);
  animation: pk-islandgrow .55s cubic-bezier(.34, 1.56, .64, 1);
}

.island.ok {
  box-shadow: 0 0 30px 0 rgba(52, 199, 89, .55),
              0 18px 40px -8px rgba(0, 0, 0, .85);
  animation: pk-facepop .3s cubic-bezier(.34, 1.56, .64, 1);
}

.faceIcon {
  transform-origin: center;
  animation: pk-facespin .42s cubic-bezier(.33, 0, .15, 1) .1s both;
}

.caption { position: absolute; top: 138px; left: 0; right: 0; text-align: center; }
.hint { font-size: 14px; font-weight: 700; }
.hint.scanning { color: rgba(255, 255, 255, .6); }
.hint.ok { color: #34C759; }
.detail { margin-top: 5px; font-size: 12.5px; color: rgba(255, 255, 255, .45); }
```

- [ ] **Step 4: `src/screens/pay/PayFaceId.jsx` 작성**

```jsx
import { useEffect, useState } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { sortByBenefit } from '../../utils/compare.js'
import styles from './PayFaceId.module.css'

const OK_AT_MS = 1200 // 인증 성공 표시
const NEXT_AT_MS = 2100 // 승인 화면으로 이동

const KRW = (n) => Number(n || 0).toLocaleString('ko-KR')

export default function PayFaceId() {
  const { state, dispatch } = useApp()
  const [ok, setOk] = useState(false)

  useEffect(() => {
    const okTimer = setTimeout(() => setOk(true), OK_AT_MS)
    const nextTimer = setTimeout(
      () => dispatch({ type: A.SET_PAY_STEP, payStep: 'approving' }),
      NEXT_AT_MS,
    )
    return () => {
      clearTimeout(okTimer)
      clearTimeout(nextTimer)
    }
  }, [dispatch])

  const ranked = sortByBenefit(state.result?.comparison)
  const chosen = ranked[state.payIdx] || ranked[0]
  const amount = state.transaction?.payment_amount || 0
  const final = amount - (chosen?.expected_benefit || 0)

  return (
    <div className={styles.overlay}>
      <div className={`${styles.island} ${ok ? styles.ok : ''}`}>
        {ok ? (
          <svg
            width="62" height="62" viewBox="0 0 44 44" fill="none"
            stroke="#34C759" strokeWidth="3.4"
            strokeLinecap="round" strokeLinejoin="round"
          >
            <path d="M34 15 19 31l-8-8" />
          </svg>
        ) : (
          <svg
            className={styles.faceIcon}
            width="74" height="74" viewBox="0 0 44 44" fill="none"
            stroke="#34C759" strokeWidth="3"
            strokeLinecap="round" strokeLinejoin="round"
          >
            <circle cx="22" cy="22" r="18" />
            <path d="M16 17v3" />
            <path d="M28 17v3" />
            <path d="M15 26a10 10 0 0 0 14 0" />
          </svg>
        )}
      </div>

      <div className={styles.caption}>
        <div className={`${styles.hint} ${ok ? styles.ok : styles.scanning}`}>
          {ok ? '인증되었습니다' : 'Face ID로 인증하는 중…'}
        </div>
        <div className={styles.detail}>
          {chosen?.card_company} · {KRW(final)}원
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 5: 브라우저 확인**

확인 항목:
1. 추천 화면 → "이 카드로 결제" → 결제 확인 화면. 방패 아이콘이 은은하게 맥동한다.
2. 선택 카드·결제금액·할인·최종금액·추천이유가 보이고, 금액이 추천 화면과 **일치**한다.
3. "다른 카드 선택" → 추천 화면으로 돌아간다.
4. "🔒 결제하기" → 상단 다이나믹 아일랜드가 **커지면서 초록 얼굴 아이콘이 회전**하고, 뒤로 결제확인 화면이 어둡게 비친다.
5. 약 1.2초 후 체크 표시 + "인증되었습니다"로 바뀐다.
6. 약 2.1초 후 `PayApproving` 스텁으로 넘어간다.

- [ ] **Step 6: 커밋**

```bash
cd "c:/Picka_Front/1st_project"
git add front_end/src/screens/pay/PayConfirm.jsx front_end/src/screens/pay/PayConfirm.module.css front_end/src/screens/pay/PayFaceId.jsx front_end/src/screens/pay/PayFaceId.module.css
git commit -m "결제 확인 화면과 Face ID 오버레이 구현"
```

---

## Task 10: 승인 중 · 결제 완료

**Files:**
- Modify: `front_end/src/screens/pay/PayApproving.jsx` (스텁 → 실제)
- Create: `front_end/src/screens/pay/PayApproving.module.css`
- Modify: `front_end/src/screens/pay/PayDone.jsx` (스텁 → 실제)
- Create: `front_end/src/screens/pay/PayDone.module.css`

**Interfaces:**
- Consumes: `useApp()`, `A`, `sortByBenefit`, `gradientFor`, `shared` CSS
- Produces: 없음

- [ ] **Step 1: `src/screens/pay/PayApproving.module.css` 작성**

```css
.screen {
  position: absolute;
  inset: 0;
  z-index: 44;
  background: var(--pay-dark);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 22px;
}

.brand { width: 100%; padding: 60px 0 8px; font-size: 14px; font-weight: 800; color: #fff; }

.orb {
  margin-top: 54px;
  position: relative;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ring { position: absolute; inset: 0; border-radius: 50%; border: 1px solid rgba(110, 166, 255, .25); }

.glow {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(47, 107, 255, .3), transparent 70%);
  animation: pk-ring 1.8s ease-in-out infinite;
}

.spin {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border-top: 2px solid var(--blue-light);
  border-right: 2px solid transparent;
  border-bottom: 2px solid transparent;
  border-left: 2px solid transparent;
  animation: pk-spin 1s linear infinite;
}

.core {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(140deg, #16294f, #0c1a3a);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
}

.head { text-align: center; margin-top: 26px; }
.headTitle { font-size: 20px; font-weight: 800; color: #fff; }
.headSub { font-size: 13px; color: rgba(255, 255, 255, .5); margin-top: 8px; line-height: 1.5; }

.panel {
  margin-top: 30px;
  width: 100%;
  background: rgba(255, 255, 255, .05);
  border: 1px solid rgba(255, 255, 255, .08);
  border-radius: 16px;
  padding: 16px 18px;
}

.row { display: flex; justify-content: space-between; font-size: 13px; }
.row + .row { margin-top: 12px; }
.rowLabel { color: rgba(255, 255, 255, .5); }
.rowValue { color: #fff; font-weight: 600; }

.barTrack {
  margin-top: 14px;
  height: 5px;
  border-radius: 4px;
  background: rgba(255, 255, 255, .1);
  overflow: hidden;
}

.barFill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #2F6BFF, #6ea6ff);
  animation: pk-grow 2.2s ease-in-out forwards;
}

.foot {
  margin-top: auto;
  margin-bottom: 44px;
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 11.5px;
  color: rgba(255, 255, 255, .4);
  border: 1px solid rgba(255, 255, 255, .1);
  padding: 8px 14px;
  border-radius: 20px;
}
```

- [ ] **Step 2: `src/screens/pay/PayApproving.jsx` 작성**

```jsx
import { useEffect } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { sortByBenefit } from '../../utils/compare.js'
import styles from './PayApproving.module.css'

const APPROVE_MS = 4000
const KRW = (n) => Number(n || 0).toLocaleString('ko-KR')

export default function PayApproving() {
  const { state, dispatch } = useApp()

  // 실제 결제 승인 API가 생기면 이 타이머를 호출로 바꿉니다.
  useEffect(() => {
    const timer = setTimeout(
      () => dispatch({ type: A.SET_PAY_STEP, payStep: 'done' }),
      APPROVE_MS,
    )
    return () => clearTimeout(timer)
  }, [dispatch])

  const ranked = sortByBenefit(state.result?.comparison)
  const chosen = ranked[state.payIdx] || ranked[0]
  const amount = state.transaction?.payment_amount || 0
  const final = amount - (chosen?.expected_benefit || 0)

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.brand}>picka</div>

      <div className={styles.orb}>
        <div className={styles.ring} />
        <div className={styles.glow} />
        <div className={styles.spin} />
        <div className={styles.core}>🔐</div>
      </div>

      <div className={styles.head}>
        <div className={styles.headTitle}>카드 승인 중</div>
        <div className={styles.headSub}>
          은행 서버와 안전하게 연결하여
          <br />
          결제 승인을 요청하고 있습니다.
        </div>
      </div>

      <div className={styles.panel}>
        <div className={styles.row}>
          <span className={styles.rowLabel}>Merchant</span>
          <span className={styles.rowValue}>{state.transaction?.merchant_name}</span>
        </div>
        <div className={styles.row}>
          <span className={styles.rowLabel}>Amount</span>
          <span className={styles.rowValue}>₩{KRW(final)}</span>
        </div>
        <div className={styles.barTrack}>
          <div className={styles.barFill} />
        </div>
      </div>

      <div className={styles.foot}>
        <span>✦</span>
        AI is verifying transaction safety…
      </div>
    </div>
  )
}
```

- [ ] **Step 3: `src/screens/pay/PayDone.module.css` 작성**

```css
.screen {
  position: absolute;
  inset: 0;
  z-index: 44;
  background: var(--pay-dark);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 22px;
}

.brand { width: 100%; padding: 60px 0 8px; font-size: 14px; font-weight: 800; color: #fff; }

.badge {
  margin-top: 40px;
  position: relative;
  width: 96px;
  height: 96px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.badgeGlow {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(47, 107, 255, .35), transparent 70%);
}

.badgeCore {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2F6BFF, #5b9dff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  color: #fff;
  animation: pk-pop .4s ease;
}

.head { text-align: center; margin-top: 18px; }
.headTitle { font-size: 24px; font-weight: 800; color: #fff; }
.headSub { font-size: 13px; color: rgba(255, 255, 255, .5); margin-top: 6px; }

.panel {
  margin-top: 24px;
  width: 100%;
  background: rgba(255, 255, 255, .05);
  border: 1px solid rgba(255, 255, 255, .08);
  border-radius: 16px;
  padding: 16px 18px;
}

.cardRow {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, .08);
}

.swatch { width: 42px; height: 28px; border-radius: 6px; flex: none; }
.cardName { font-size: 14.5px; font-weight: 700; color: #fff; }
.cardNumber { font-size: 11.5px; color: rgba(255, 255, 255, .45); letter-spacing: 1px; }

.row { display: flex; justify-content: space-between; margin-top: 14px; font-size: 13px; }
.rowLabel { color: rgba(255, 255, 255, .5); }
.rowValue { color: #fff; font-weight: 600; }
.rowGood { color: var(--green-pay); font-weight: 700; }

.total {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, .08);
}

.totalLabel { font-size: 13px; color: rgba(255, 255, 255, .6); }
.totalValue { font-size: 22px; font-weight: 800; color: var(--blue-light); }

.homeBtn {
  margin-top: 22px;
  margin-bottom: 40px;
  width: 100%;
  height: 54px;
  border: none;
  border-radius: 15px;
  background: linear-gradient(90deg, #2F6BFF, #6ea6ff);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
}
```

- [ ] **Step 4: `src/screens/pay/PayDone.jsx` 작성**

```jsx
import { useApp } from '../../state/AppContext.jsx'
import { A } from '../../state/appReducer.js'
import { sortByBenefit } from '../../utils/compare.js'
import { gradientFor } from '../../data/cards.js'
import styles from './PayDone.module.css'

const KRW = (n) => Number(n || 0).toLocaleString('ko-KR')

export default function PayDone() {
  const { state, dispatch } = useApp()

  const ranked = sortByBenefit(state.result?.comparison)
  const chosen = ranked[state.payIdx] || ranked[0]
  const amount = state.transaction?.payment_amount || 0
  const discount = chosen?.expected_benefit || 0

  if (!chosen) return null

  return (
    <div className={`${styles.screen} pk-screen`}>
      <div className={styles.brand}>picka</div>

      <div className={styles.badge}>
        <div className={styles.badgeGlow} />
        <div className={styles.badgeCore}>✓</div>
      </div>

      <div className={styles.head}>
        <div className={styles.headTitle}>결제 완료</div>
        <div className={styles.headSub}>성공적으로 처리되었습니다.</div>
      </div>

      <div className={styles.panel}>
        <div className={styles.cardRow}>
          <div
            className={styles.swatch}
            style={{ background: gradientFor(chosen.card_company) }}
          />
          <div style={{ flex: 1 }}>
            <div className={styles.cardName}>
              {chosen.card_company} {chosen.card_name}
            </div>
            <div className={styles.cardNumber}>
              **** **** **** {chosen.last_four}
            </div>
          </div>
        </div>

        <div className={styles.row}>
          <span className={styles.rowLabel}>결제 금액</span>
          <span className={styles.rowValue}>{KRW(amount)}원</span>
        </div>

        <div className={styles.row}>
          <span className={styles.rowLabel}>✦ 절약 혜택</span>
          <span className={styles.rowGood}>-{KRW(discount)}원</span>
        </div>

        <div className={styles.total}>
          <span className={styles.totalLabel}>최종 승인 금액</span>
          <span className={styles.totalValue}>{KRW(amount - discount)}원</span>
        </div>
      </div>

      <button
        type="button"
        className={styles.homeBtn}
        onClick={() => dispatch({ type: A.RESET_PAY })}
      >
        홈으로
      </button>
    </div>
  )
}
```

- [ ] **Step 5: 브라우저 확인**

확인 항목:
1. Face ID 후 승인 화면. 자물쇠 아이콘 + 회전 링, 하단 진행바가 0→100%로 약 2.2초에 걸쳐 찬다.
2. Merchant/Amount가 앞 화면과 일치한다.
3. 약 4초 후 결제 완료 화면. 파란 체크 배지가 팝 애니메이션으로 뜬다.
4. 카드·결제금액·절약혜택·최종승인금액이 앞 화면과 일치한다.
5. "홈으로" → 지갑 홈으로 돌아가고, 카드 스택이 그대로 남아 있다.

- [ ] **Step 6: 커밋**

```bash
cd "c:/Picka_Front/1st_project"
git add front_end/src/screens/pay/PayApproving.jsx front_end/src/screens/pay/PayApproving.module.css front_end/src/screens/pay/PayDone.jsx front_end/src/screens/pay/PayDone.module.css
git commit -m "결제 승인 중·완료 화면 구현"
```

---

## Task 11: 통합 점검 · 정리

**Files:**
- Modify: 앞 태스크에서 발견된 문제 파일들
- Modify: `front_end/README` 성격의 문서가 없으므로 생성하지 않는다. 대신 스펙 문서에 진행 상황을 반영한다.
- Modify: `docs/superpowers/specs/2026-07-20-picka-wallet-frontend-design.md`

**Interfaces:**
- Consumes: 전체
- Produces: 없음

- [ ] **Step 1: 빌드 통과 확인**

```bash
cd "c:/Picka_Front/1st_project/front_end"
npm run build
```

기대: 에러 없이 `dist/`가 생성된다. 실패하면 출력된 파일·줄을 고치고 다시 실행한다.

- [ ] **Step 2: 죽은 코드 검사**

```bash
cd "c:/Picka_Front/1st_project/front_end"
grep -rn "PickaMark" src/ || echo "PickaMark 미사용"
grep -rn "won(" src/ || echo "won() 미사용"
grep -rn "variant=\"row\"\|variant='row'" src/ || echo "CardFace row variant 미사용"
```

`Splash.jsx`의 `PickaMark`가 `Splash.jsx` 안에서만 쓰인다면 `export`를 떼고 지역 함수로 만든다.
`utils/format.js`의 `won()`이 아무 데서도 안 쓰인다면 **파일을 삭제한다** (YAGNI — 각 화면이 `toLocaleString`을 직접 쓰고 있다).
`CardFace`의 `row` variant가 안 쓰인다면 **해당 분기와 `.row` CSS를 삭제한다** (Cards 관리 화면은 이번 범위 밖이라 소비자가 없다).

- [ ] **Step 3: 전체 플로우 수동 검증 (백엔드 켠 상태)**

```bash
# 터미널 1
cd "c:/Picka_Front/1st_project"
python -m uvicorn backend.main:app --reload --port 8000
# 터미널 2
cd "c:/Picka_Front/1st_project/front_end"
npm run dev
```

스펙의 검증 목록을 그대로 따른다. 각 항목을 눌러보고 통과 여부를 기록한다.

1. 스플래시 탭 → 로그인
2. `KDA4`/`1234` → 홈. 틀린 값 → 빨간 오류 문구
3. 홈 카드 탭 → 스택 펼침 / 하단 문구 탭 → 접힘
4. "QR 열기" → QR 화면. 180초 카운트다운 감소
5. "매장에서 QR 인식됨" → received → analyzing → recommend
6. 바텀시트에서 다른 카드 선택 → 최종금액 갱신
7. 결제 → faceid → approving → done → 홈
8. **결제를 3회 반복** — 랜덤 가맹점이 바뀌고 그에 따라 추천 카드가 달라지는지 확인

8번이 중요하다. 항상 같은 카드만 추천된다면 `payment_category` 전달이나 정렬에 문제가 있는 것이다.

- [ ] **Step 4: 오류 경로 검증 (백엔드 끈 상태)**

터미널 1의 uvicorn을 끄고 5번을 다시 실행한다.

기대: 추천 화면에 ⚠️ 오류 카드 + "다시 시도" 버튼. 앱이 멈추거나 흰 화면이 되지 않는다.

- [ ] **Step 5: 스펙 문서에 완료 표시 추가**

`docs/superpowers/specs/2026-07-20-picka-wallet-frontend-design.md` 맨 아래에 추가한다.

```markdown
## 구현 현황

- 2026-07-20: 이번 범위(Splash·Login·Home·QR·결제 7화면) 구현 완료.
  구현 계획: `docs/superpowers/plans/2026-07-20-picka-wallet-frontend.md`
- 남은 화면(Card Detail·Benefits·Cards 관리·소비 리포트·카드 등록)은 별도 스펙 필요.
```

- [ ] **Step 6: 커밋**

```bash
cd "c:/Picka_Front/1st_project"
git add -A front_end docs
git commit -m "통합 점검 및 미사용 코드 정리

전체 결제 플로우 수동 검증 완료. 빌드 통과."
```

---

## Self-Review

**스펙 커버리지 확인:**

| 스펙 요구 | 담당 태스크 |
|---|---|
| 에셋 4개 복사 | Task 1 Step 1 |
| 디자인 토큰 CSS 변수 | Task 1 Step 2 |
| PhoneFrame | Task 1 Step 5–6 |
| Context + reducer | Task 2 Step 1–3 |
| 옛 컴포넌트 삭제 | Task 2 Step 6 |
| 보유카드를 백엔드와 일치 | Task 3 Step 1 |
| `fetchMyCards()` 어댑터 | Task 3 Step 2 |
| 목업 로그인 (`api/auth.js`) | Task 3 Step 3 |
| Splash·Login 화면 | Task 4 |
| CardFace + 카드 스택 접힘/펼침 | Task 5 |
| QR 180초 카운트다운·만료·새로고침 | Task 6 |
| `data-qr-token` / `data-qr-expires-in` | Task 6 Step 2 |
| 가맹점 랜덤 | Task 6 Step 4 (`pickMerchant`) |
| 결제 7화면 | Task 7–10 |
| 추천 API 호출 + 최소 2.9초 | Task 7 Step 5 |
| 404를 안내로 분기 | Task 7 Step 5, Task 8 Step 2 |
| 호출 실패 시 recommend로 진입 + 다시 시도 | Task 7 Step 5, Task 8 Step 2 |
| `sortByBenefit` 순수 함수 | Task 2 Step 2 |
| 타이머를 화면이 소유 | Task 6·7·9·10의 `useEffect` |
| 이미지 로드 실패 대비 | **미커버 — 아래 참조** |
| 수동 검증 8항목 | Task 11 Step 3 |

**발견한 갭 1 — 이미지 로드 실패 대비:** 스펙은 "로고/에셋 이미지 로드 실패 시 `onError`로 텍스트 대체"를 요구했다. Task 4·5·6에서 로고는 인라인 SVG로 바꿔 이 문제가 사라졌지만, `qr-code.png`·`qr-tight.png`·`kakao-bubble-cut.png`는 여전히 `<img>`다. Task 11에 다음 단계를 추가한다.

- [ ] **Task 11 Step 2b: 이미지 폴백 추가**

`src/components/QrCode.jsx`의 `<img>`에 `onError`를 붙여, 실패 시 네이비 사각형과 "QR" 텍스트로 대체한다.

```jsx
// QrCode.jsx 상단에 추가
import { useState } from 'react'

// 컴포넌트 안에 추가
  const [broken, setBroken] = useState(false)

// <img> 를 아래로 교체
      {broken ? (
        <div
          style={{
            width: '100%', height: '100%', display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            background: '#0A1D4F', color: '#fff', borderRadius: 8,
            fontSize: 20, fontWeight: 800, letterSpacing: 2,
          }}
        >
          QR
        </div>
      ) : (
        <img
          className={styles.image}
          src="/assets/qr-tight.png"
          alt="결제 QR 코드"
          style={{ opacity: expired ? 0.1 : 1 }}
          onError={() => setBroken(true)}
        />
      )}
```

같은 방식으로 `WalletHome.jsx`의 QR 바 아이콘과 `Login.jsx`의 카카오 아이콘에도 `onError={(e) => { e.currentTarget.style.display = 'none' }}`를 붙인다.

**발견한 갭 2 — `won()` 중복:** 각 결제 화면이 지역 `KRW()` 헬퍼를 중복 정의하고 있다. DRY 위반이다. Task 11 Step 2에서 정리한다.

- [ ] **Task 11 Step 2c: 금액 포맷 통일**

`src/utils/format.js`를 아래로 교체하고, 결제 화면 5개(`PayRecommend`, `PayConfirm`, `PayFaceId`, `PayApproving`, `PayDone`)의 지역 `KRW` 정의를 지운 뒤 이 함수를 import한다.

```js
/** 숫자를 천 단위 구분 문자열로 만듭니다. 예: 12000 -> "12,000" */
export function krw(value) {
  return Number(value || 0).toLocaleString('ko-KR')
}

/** 금액을 원화 표시로 만듭니다. 예: 12000 -> "12,000원" */
export function won(value) {
  return `${krw(value)}원`
}
```

각 화면에서:

```jsx
import { krw } from '../../utils/format.js'
// 그리고 KRW( → krw( 로 치환
```

이 정리 후 Task 11 Step 2의 "`won()` 미사용이면 삭제" 지시는 무효다 — `krw()`가 5곳에서 쓰이므로 파일을 유지한다.

**타입 일관성 확인:** `card_id`, `card_company`, `card_name`, `last_four`, `nickname`, `expected_benefit`, `eligible`, `reason`, `benefit_rate` — 백엔드 응답 필드명을 Task 3·5·8·9·10에서 동일하게 사용했다. `gradientFor()`는 Task 3에서 정의하고 Task 5·6·8·9·10에서 사용한다. `sortByBenefit()`는 Task 2에서 정의하고 Task 8·9·10에서 사용한다. `A` 액션 상수는 Task 2의 목록과 각 화면의 dispatch가 일치한다.

**플레이스홀더 검사:** "TBD", "적절히 처리", "위와 유사" 없음. Task 2 Step 4의 결제 스텁 6개는 표로 차이점을 명시했고 기준 코드가 바로 위에 있다.
