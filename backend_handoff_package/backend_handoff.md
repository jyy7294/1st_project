# 백엔드 전달용 카드 추천 데이터 정리

## 현재 상태

- 카드 수: 1,559개
- 혜택 수: 8,476개
- 스냅샷 기준: 최신 크롤링 반영본

## 스코어링 등급 사용법

| 등급 | 백엔드 처리 |
|---|---|
| A_확정계산 | 기본 추천 점수에 바로 사용 |
| B_추정계산 | 임시월캡/수동보정 한도 내에서 보수적으로 계산 |
| C_표시전용 | 상세 화면에 표시하되 기본 추천 점수 제외 |
| D_제외권장 | 일반 소비 추천 점수 제외 |

현재 등급 분포:

```text
스코어링등급
C_표시전용    3253
B_추정계산    2195
A_확정계산    1962
D_제외권장    1066
```

## 백엔드가 우선 읽을 파일

```text
data/backend_recommendation_export.json
data/card_benefits_rules_enriched.csv
data/card_benefit_tiers.csv
data/card_benefits_options_enriched.csv
data/cards_master_performance_enriched.csv
data/merchant_alias_dictionary.csv
```

## 추천 계산 기본 순서

1. 결제처명을 `merchant_alias_dictionary.csv`로 표준 카테고리에 매칭한다.
2. 사용자가 보유한 카드만 후보로 좁힌다.
3. 카드 전월실적과 혜택별 실적조건을 확인한다.
4. 결제 카테고리와 혜택 카테고리/가맹점목록을 매칭한다.
5. A등급은 확정 계산한다.
6. B등급은 `월최대혜택액`, `통합한도_월`, `임시월캡` 순서로 보수 계산한다.
7. C/D등급은 기본 추천 점수에서 제외한다.
8. 같은 `옵션그룹` 혜택은 모두 더하지 말고 선택된 1개 또는 기대혜택 최대 1개만 반영한다.
9. 이미 월한도/횟수를 소진한 혜택은 기대혜택 0원 처리한다.

## B등급 추가 검수

- B등급 혜택 수: 2,195개
- 우선 검수 파일: `data/review_b_grade_priority.csv`
- 우선순위는 고할인, 한도미확인, 주요 소비 카테고리, 옵션형 여부를 기준으로 산정했다.

## 결제처명 테스트

- 테스트 건수: 30개
- 정상 매칭: 30개
- 결과 파일: `data/merchant_match_test_results.csv`

실제 서비스에서는 결제 로그가 생길 때마다 미매칭 결제처명을 `review_unmatched_merchants.csv`에 모아 alias 사전에 추가해야 한다.

## 추천 테스트 시나리오

테스트 파일: `data/recommendation_test_scenarios.json`

현재 샘플 시나리오 수: 5개

## 아직 백엔드/서비스 단계에서 필요한 것

- 사용자 보유 카드 테이블
- 사용자 카드별 전월실적/이번달 사용액
- 혜택별 월 한도 사용량
- 실제 결제 로그
- 추천 결과 로그
- 미매칭 가맹점명 보정 루프
