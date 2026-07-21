# 실제 서비스 연동 준비 문서

## 한 줄 요약

전처리 데이터는 카드 혜택 규칙이고, 실제 서비스 데이터는 사용자 상태다.
추천 앱은 이 둘을 합쳐야 결제 순간에 어떤 카드가 유리한지 계산할 수 있다.

## 붙어야 하는 데이터

1. 사용자 보유 카드
   - 사용자가 앱에 등록한 카드 목록
   - 전처리 데이터의 `카드번호`와 앱 DB의 `card_id`를 연결한다.

2. 실제 결제 로그
   - 승인일시, 결제처명, 결제금액, 결제 카드가 필요하다.
   - 결제처명은 `merchant_alias_dictionary.csv`로 표준 카테고리에 매칭한다.

3. 카드별 실적/한도 사용량
   - 전월실적 충족 여부와 이번 달 혜택 한도 소진 여부를 저장한다.
   - 같은 카드라도 사용자마다 사용량이 다르므로 앱 DB에 따로 있어야 한다.

4. 카드사 공식 약관 갱신
   - 고할인/한도미확인 혜택은 공식 페이지나 상품설명서 PDF로 보정한다.
   - 보정값은 `card_benefit_manual_corrections.csv`에 기록하고 Step 16으로 반영한다.

## 이번 단계에서 만든 파일

```text
docs/backend_db_schema.sql
docs/service_integration_plan.md
data/sample_user_cards.csv
data/sample_transactions.csv
data/sample_monthly_card_usage.csv
data/sample_benefit_usage.csv
data/service_readiness_checklist.csv
data/review_official_update_backlog.csv
```

## 백엔드 개발 시작 순서

1. `docs/backend_db_schema.sql` 기준으로 DB 테이블을 만든다.
2. `data/backend_recommendation_export.json`을 카드/혜택 기본 데이터로 적재한다.
3. `data/merchant_alias_dictionary.csv`를 결제처명 매칭 사전으로 적재한다.
4. `data/sample_transactions.csv`로 추천 로직을 먼저 테스트한다.
5. 실제 결제 로그가 들어오면 `review_unmatched_merchants.csv`에 미매칭을 모으고 alias를 보강한다.
6. 한도미확인/고할인 혜택은 `review_official_update_backlog.csv` 순서대로 공식자료를 확인한다.
