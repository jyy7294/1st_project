# PICKA 지갑 UI 프론트엔드 재구현 설계

- 날짜: 2026-07-20
- 브랜치: `sunup-front`
- 디자인 레퍼런스: `~/Desktop/1차 플젝/PICKA 웹앱 디자인_0719_rev/design_handoff_picka_wallet/`

## 배경

중간발표용으로 급히 만든 `front_end`를 디자인 핸드오프(`Picka Wallet.dc.html`)에 맞춰 다시 만든다.
디자인 파일 자체는 수정하지 않는다 — 마크업·스타일·상태 로직을 읽고 React로 재구현하는 것이 과제다.

핸드오프 폴더에서 실제로 저장소에 가져오는 파일은 `assets/` 이미지 4개뿐이다.
`Picka Wallet.dc.html`, `support.js`, `PICKA_공유용.html`은 눈으로 보는 레퍼런스이며 복사하지 않는다.
특히 `support.js`(dc-runtime)는 이식 대상이 아니다.

백엔드는 다른 팀원이 담당한다. `backend/`는 이번 작업에서 건드리지 않는다.

## 범위

이번 스펙에 포함:

- Splash
- Login
- Home / Wallet (카드 스택)
- QR 전체화면
- 결제 플로우 7화면 (received → analyzing → recommend → confirm → faceid → approving → done)

이번 스펙에서 제외 (각각 별도 스펙으로):

- Card Detail (`screen: 'detail'`)
- Benefits (`screen: 'benefits'`)
- Cards Management (`screen: 'cards'`)
- Consumption Report (`screen: 'report'`)
- Add Card (`screen: 'add'`, 4단계)

제외한 화면들은 대응하는 백엔드 API가 없고(카드별 상세혜택, 월별 소비 집계, 카테고리 도넛),
목업 데이터 규모가 이번 범위보다 크다.

## 결정 사항

| 항목 | 결정 | 이유 |
|---|---|---|
| 스타일 | CSS Modules + 디자인 토큰 CSS 변수 | 기존 저장소 컨벤션 유지. 픽셀값은 원본 그대로 옮기되 클래스명으로 읽히게 함 |
| 화면 전환 | Context + reducer (라우터 없음) | 데모라 URL이 불필요하고, 결제 8단계처럼 순서가 강제된 플로우에 URL 직접진입 방어가 안 들어감 |
| 보유카드 | 프론트 목업 + `fetchMyCards()` 어댑터 | 백엔드에 보유카드 조회 엔드포인트가 없음. `GET /api/v1/cards`가 생기면 함수 안쪽만 교체 |
| 로그인 | `KDA4/1234` 목업 검증 | 백엔드 인증 API 부재. 검증 로직을 `api/auth.js` 한 곳에 모아 나중에 교체 |
| 가맹점 | `MERCHANTS` 5곳 랜덤 유지 | 업종이 바뀌어야 백엔드 추천 로직이 실제로 동작하는 게 보임 |
| 기존 컴포넌트 | 새 구조로 대체 (삭제) | 디자인 화면과 1:1로 안 맞음 (아래 참조) |

### 기존 컴포넌트가 대체되는 이유

| 기존 | 디자인에서의 대응 |
|---|---|
| `WalletHome.jsx` | 재작성 (카드 스택 접힘/펼침 인터랙션 추가) |
| `PickaQrHome.jsx` + `QrScreen.jsx` | QR 화면 **하나**로 통합 |
| `Loading.jsx` | `PayReceived` / `PayAnalyzing` / `PayApproving` **셋**으로 분화 |
| `Recommendation.jsx` | `PayRecommend` / `PayConfirm` / `PayDone` **셋**으로 분화 |

파일명을 유지하면 한 파일이 여러 화면을 떠안게 되므로 새로 나눈다.

## 파일 구조

```
front_end/
  public/assets/
    qr-code.png              홈 QR 바 아이콘 (38px)
    qr-tight.png             QR 전체화면 코드 (262px)
    kakao-bubble-cut.png     로그인 카카오 버튼 아이콘
    kakao-bubble.png         예비
  src/
    App.jsx                  screen/payStep → 화면 매핑만
    state/
      AppContext.jsx         Provider + useApp()
      appReducer.js          순수 함수. 상태 전이만
    screens/
      Splash.jsx
      Login.jsx
      WalletHome.jsx
      QrScreen.jsx
      pay/
        PayReceived.jsx
        PayAnalyzing.jsx
        PayRecommend.jsx
        PayConfirm.jsx
        PayFaceId.jsx
        PayApproving.jsx
        PayDone.jsx
    components/
      PhoneFrame.jsx         베젤·다이나믹아일랜드·상태바·홈인디케이터
      CardFace.jsx           카드 앞면 (stack | detail | row 3가지 크기)
      QrCode.jsx             QR 이미지 + data-qr-* 속성
    data/
      cards.js               목업 보유카드
      merchants.js           기존 유지
    api/
      picka.js               fetchRecommendation + fetchMyCards
      auth.js                목업 로그인 검증
    styles/
      tokens.css             디자인 토큰 → CSS 변수
    utils/format.js          기존 유지
```

`screens/`와 `components/`의 각 `.jsx` 옆에 같은 이름의 `.module.css`를 둔다
(예: `WalletHome.jsx` + `WalletHome.module.css`). `App.jsx`는 화면 매핑만 하므로 자체 스타일이 없다.

삭제: `components/PickaQrHome.jsx(.module.css)`, `components/Recommendation.jsx(.module.css)`,
`components/Loading.jsx(.module.css)`, `components/QrScreen.jsx(.module.css)`,
`components/WalletHome.jsx(.module.css)`, `App.module.css`.

## 디자인 토큰

`styles/tokens.css`에 CSS 변수로 정의한다. 출처는 README의 Design Tokens 절.

```
--navy: #0E245D          --navy-text: #0A1D4F
--navy-grad: linear-gradient(145deg, #10275F, #071844)
--blue: #2F6BFF          --blue-hover: #1846D8      --blue-light: #6ea6ff
--teal: #19D3C5          --teal-deep: #0DAAA0
--gold: #FFCE45
--green-chart: #2F8F3E   --green-pay: #4ADE80
--danger: #e5484d
--bg-app: #f4f5f8        --bg-card: #ffffff
--pay-dark: linear-gradient(180deg, #0a1224, #060b18)
--text-2: #7a8299        --text-3: #9aa1b3        --text-4: #a8aec0
--kakao: #FEE500         --naver: #03C75A
--r-card: 20px  --r-btn: 14px  --r-chip: 10px
--sh-card: 0 4px 14px rgba(14,36,93,.05)
```

`@keyframes`(`pk-fade`, `pk-pop`, `pk-up`, `pk-spin`, `pk-ring`, `pk-grow`,
`pk-float`, `pk-islandgrow`, `pk-facespin`, `pk-facepop`)도 여기에 둔다 — 여러 화면이 공유한다.

## 상태 관리

### 상태 형태

```js
{
  screen: 'splash' | 'login' | 'home' | 'qr',
  payStep: 'none' | 'received' | 'analyzing' | 'recommend'
         | 'confirm' | 'faceid' | 'approving' | 'done',
  cards: [],          // fetchMyCards() 결과
  expanded: false,    // 카드 스택 펼침
  active: 0,          // 선택된 카드 index
  transaction: null,  // QR로 읽은 결제정보
  payIdx: 0,          // 결제에 쓸 카드 index
  result: null,       // 백엔드 추천 응답
  error: null,
  loginError: '',
  social: null,       // 'kakao' | 'naver' | null
}
```

`payStep !== 'none'`이면 결제 화면이 `screen` 화면 위를 덮는다
(디자인의 `z-index: 44` 오버레이와 동일).

### 타이머 소유권

타이머는 리듀서에 두지 않는다. 각 화면 컴포넌트의 `useEffect`가 소유하고 언마운트 시 정리한다.

| 화면 | 타이머 |
|---|---|
| `PayReceived` | 1.9초 후 `analyzing` |
| `PayAnalyzing` | 620ms 간격 체크리스트 4단계, 최소 2.9초 후 `recommend` |
| `PayFaceId` | 1.2초 후 인증완료 표시, 2.1초 후 `approving` |
| `PayApproving` | 4초 후 `done` |
| `QrScreen` | 1초 간격 180초 카운트다운 |

## 결제 플로우 데이터 흐름

```
QR 화면 "매장에서 QR 인식됨 (데모)" 탭
  → transaction = MERCHANTS 중 랜덤 1건
  → payStep 'received'      거래정보(가맹점·상품·금액) 1.9초 표시
  → payStep 'analyzing'     체크리스트 4단계 진행
       └ 진입과 동시에 POST /api/v1/recommendations
            { merchant_name, payment_category, payment_amount }
  → payStep 'recommend'     최소 2.9초 보장 후 진입
       result.recommended_card → 추천 카드 (할인/최종금액)
       result.comparison[]     → 바텀시트 "다른 카드로 결제하기"
                                 expected_benefit 내림차순 정렬
  → 'confirm' → 'faceid' → 'approving' → 'done'
```

`done`에서 "홈으로"를 누르면 `payStep: 'none'`, `screen: 'home'`으로 초기화한다.

### 응답 필드 매핑

백엔드 `recommend_cards` 응답의 카드 객체에서 화면이 쓰는 필드:

| 필드 | 쓰이는 곳 |
|---|---|
| `card_company` / `card_name` | 카드 앞면 상단, 바텀시트 행 |
| `last_four` | `•••• •••• •••• {last_four}` |
| `expected_benefit` | 할인 혜택 금액, 바텀시트 정렬 키 |
| `eligible` | false면 바텀시트에서 흐리게 + 혜택 0원 |
| `reason` | 추천 이유 한 줄 |
| `reason_details` | 확인 화면 상세 항목 |
| `nickname` | 카드 라벨 칩 |

카드 그라데이션은 백엔드에 없다. `data/cards.js`가 `card_company` → 그라데이션 매핑을 제공한다.

## 에러 처리

| 상황 | 동작 |
|---|---|
| 추천 호출 실패 (5xx / 네트워크) | `analyzing`에서 멈추지 않고 `recommend`로 진입. 추천 카드 자리에 오류 문구 + "다시 시도" 버튼 |
| 404 "추천 가능한 카드가 없습니다" | 오류가 아닌 안내로 구분. "이 업종엔 혜택 카드가 없어요 — 아무 카드로나 결제하세요" + 보유카드 목록 |
| 로고/에셋 이미지 로드 실패 | `onError`로 텍스트 대체 (기존 `logoBroken` 패턴 유지) |
| QR 180초 만료 | QR 흐리게 + 새로고침 버튼 노출. 누르면 타이머·토큰 재발급 |

## 백엔드 연동 지점

지금은 목업이고 나중에 교체할 곳:

| 기능 | 현재 | 교체 대상 |
|---|---|---|
| 로그인 | `api/auth.js`의 `KDA4/1234` 하드코딩 | 인증 API + 세션/토큰 |
| 소셜 로그인 | OAuth URL 새 탭 + 스피너 | 카카오/네이버 OAuth 콜백 |
| 보유카드 | `api/picka.js`의 `fetchMyCards()` → `data/cards.js` 반환 | `GET /api/v1/cards` |
| 결제 추천 | `POST /api/v1/recommendations` (이미 연동됨) | 그대로 |
| QR 토큰 | `QrCode.jsx`의 `data-qr-token` / `data-qr-expires-in` | 결제서버 발급 토큰·만료시각 |
| 결제 승인 | 4초 타이머 | 결제 승인 API |

`data/cards.js`의 카드사·카드명·`last_four`·`nickname`은
백엔드 `user_cards.py`의 3장(카드ID 13, 2262, 2261)과 값을 일치시킨다.
그래야 홈 화면 카드와 결제 추천 결과의 카드가 같은 카드로 보인다.

## 테스트

저장소에 테스트 러너가 없다. 이번 범위는 화면 조립이 대부분이라 러너를 새로 들이지 않는다.

대신 로직을 순수 함수로 떼어 나중에 테스트를 붙일 수 있게 한다:

- `state/appReducer.js` — 상태 전이. 부수효과 없음
- `utils/format.js` — 금액 포맷
- 바텀시트 정렬 함수 — `comparison[]` → 표시 순서

검증은 `npm run dev`로 다음 경로를 직접 눌러 확인한다:

1. Splash 탭 → Login
2. `KDA4/1234` → Home. 틀린 값 → 빨간 오류 문구
3. Home 카드 탭 → 스택 펼침 / 하단 문구 탭 → 접힘
4. "QR 열기" → QR 화면. 180초 카운트다운 감소 확인
5. "매장에서 QR 인식됨" → received → analyzing → recommend
6. 바텀시트에서 다른 카드 선택 → 최종금액 갱신
7. 결제 → faceid → approving → done → 홈
8. 백엔드를 끈 상태로 5번 재실행 → 오류 문구 + 다시 시도 버튼

## 명시적 비목표

- `backend/` 수정
- 핸드오프의 `support.js`(dc-runtime) 이식
- react-router, Tailwind, 상태관리 라이브러리 도입
- 실제 OAuth 연동
- 실제 카드사 카드 이미지 사용 (저작권 — 브랜드 컬러 그라데이션 유지)
