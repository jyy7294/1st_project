# 월렛 홈 화면 설계 (Wallet Home)

날짜: 2026-07-16
범위: `front_end`만 수정. `backend`는 건드리지 않음.

## 목적

앱의 첫 홈 화면을 Apple Wallet 스타일의 **겹쳐진 카드 스택** 지갑 화면으로 교체한다.
상단 PICKA 로고는 그대로 유지하고, 전문 디자이너가 구성한 것 같은 완성도를 목표로 한다.

## 화면 흐름

- `WalletHome`이 새 첫 화면(HOME 단계)이 된다. 기존 `PickaQrHome`을 대체(파일은 삭제하지 않고 미사용으로 남김).
- 화면 안의 **QR 결제 타일**을 탭하면 기존 결제 흐름(`startPayment` → LOADING_PAYMENT → PICKA_QR → …)으로 진입한다. 결제 로직은 재사용, 변경 없음.

## 파일

신규:
- `src/data/cards.js` — 프론트 목업 보유 카드 데이터
- `src/components/WalletHome.jsx`
- `src/components/WalletHome.module.css`

수정:
- `src/App.jsx` — HOME 단계에서 `WalletHome` 렌더. HOME일 때만 헤더 오른쪽에 `+`/`⋯` 액션 버튼(장식용) 표시.
- `src/App.module.css` — 헤더 액션 버튼 스타일 (로고 left, 액션 right 정렬).

## 데이터 (`cards.js`)

카드 배열. 각 항목:
- `id`, `company`(카드사), `name`(카드명), `label`(라벨링 칩 텍스트), `last4`, `gradient`(CSS background)

목업 4장 (브랜드 톤 그라데이션):
1. 신한카드 Deep Dream · 라벨 "생활비" · 파랑 그라데이션 · 1234
2. 삼성카드 taptap O · 라벨 "쇼핑" · 다크 그라데이션 · 5678
3. KB국민 톡톡Ⅱ · 라벨 "카페" · 퍼플 그라데이션 · 9012
4. 현대카드 M · 라벨 "교통" · 틸 그라데이션 · 3456

## 레이아웃 (위 → 아래)

1. 제목 `내 지갑` + 서브텍스트 `보유 카드 N장`
2. **겹쳐진 카드 스택**: 카드가 세로로 살짝 겹쳐 쌓임(음수 마진 오버랩). 접힌 카드는 상단 스트립(카드사·카드명·라벨 칩)만 보이고, 선택된 카드는 그라데이션 카드면 전체(•••• last4)로 펼쳐짐.
3. **QR 결제 타일**: `[QR] QR로 결제하기 / 탭하면 결제가 시작돼요`. 탭 → `onScan()`(= startPayment).

## 인터랙션

- `WalletHome`이 `selectedId` 상태 보유. 기본값 = 첫 카드.
- 접힌 카드 탭 → 해당 카드 `selectedId`로 설정되어 펼쳐지고, 나머지는 접힌 채 겹침 유지.
- CSS 트랜지션(height/margin/transform)으로 부드러운 펼침. hover/active 미세 모션.
- `+`/`⋯` 헤더 버튼은 이번 범위에서 장식용(no-op).

## 성공 기준

- `npm run dev` 실행 시 첫 화면이 로고 + 겹쳐진 카드 스택 + QR 타일로 렌더된다.
- 카드를 탭하면 그 카드가 펼쳐지고 나머지는 접힌다.
- QR 타일을 탭하면 기존 결제 흐름으로 정상 진입한다.
- backend 파일은 변경되지 않는다.
