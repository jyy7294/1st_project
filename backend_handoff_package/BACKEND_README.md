# Backend handoff package

이 폴더는 백엔드 담당자에게 전달할 최소 파일 묶음입니다.

## 먼저 볼 파일

1. `backend_handoff.md`

   - 추천 데이터 사용법과 A/B/C/D 스코어링 정책 설명
2. `backend_recommendation_export.json`

   - 백엔드 추천 로직에서 읽을 최종 카드/혜택 데이터
3. `backend_db_schema.sql`

   - DB 테이블 설계 초안
4. `service_integration_plan.md`

   - 실제 서비스 연동 시 필요한 사용자 카드, 결제 로그, 실적/한도 상태 구조 설명

## 테스트/보조 파일

- `recommendation_test_scenarios.json`

  - 추천 로직 테스트용 시나리오
- `merchant_alias_dictionary.csv`

  - 결제처명 alias 매칭 사전
- `merchant_match_test_results.csv`

  - 결제처명 매칭 테스트 결과
- `final_preprocessing_quality_summary.json`

  - 최종 전처리 품질 요약
- `final_quality_gate.md`

  - 남은 리스크와 품질 게이트 설명

## 스코어링 정책

- `A_확정계산`: 추천 점수에 바로 반영 가능
- `B_추정계산`: 추천 점수에 반영 가능하되 보수적으로 계산
- `C_표시전용`: 앱 화면에는 표시하되 추천 점수에는 제외
- `D_제외권장`: 추천 점수에서 제외

## 현재 상태

- 고할인 한도 검수 대상: 0개
- 1차 필수 검수: 0개
- 남은 blocker: 공식 약관 갱신 backlog

백엔드 개발은 이 패키지 기준으로 시작 가능합니다.
