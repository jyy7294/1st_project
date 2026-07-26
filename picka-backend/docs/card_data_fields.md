# 카드 데이터 필드 정리

## 카드 필드

| **JSON 필드명** | **의미**                        | **DB 컬럼명** | **데이터 타입** | **필수 여부** |
| --------------------- | ------------------------------------- | ------------------- | --------------------- | ------------------- |
| 카드번호              | 카드 고유 식별 번호                   | source_card_id      | VARCHAR / INT         | **필수**      |
| 구분                  | 신용/체크/하이브리드 등 구분          | card_type           | VARCHAR               | **필수**      |
| 카드사                | 카드 발급사 이름                      | issuer              | VARCHAR               | **필수**      |
| 카드명                | 상품명                                | card_name           | VARCHAR               | **필수**      |
| 브랜드_목록           | 지원하는 카드 브랜드 리스트 (VISA 등) | brands              | TEXT / JSON           | **필수**      |
| 전월실적              | 기준 전월 실적 조건 금액              | previous_spending   | INTEGER               | 선택                |
| 연회비_최소           | 기본 또는 최소 연회비 금액            | min_annual_fee      | INTEGER               | 선택                |
| 연회비_무료           | 연회비 면제 여부                      | is_annual_fee_free  | BOOLEAN               | **필수**      |
| 국내전용카드          | 국내 전용 결제 가능 여부              | is_domestic_only    | BOOLEAN               | **필수**      |
| 해외결제가능          | 해외 결제 가능 여부                   | is_international    | BOOLEAN               | **필수**      |
| 통합한도_월           | 월간 통합 혜택 제공 한도액            | monthly_total_limit | INTEGER               | 선택                |
| 상세URL               | 카드사 공식 안내 페이지 주소          | detail_url          | VARCHAR               | 선택                |

## 혜택 필드



| **JSON 필드명** | **의미**                              | **DB 컬럼명**    | **데이터 타입** | **필수 여부** |
| --------------------- | ------------------------------------------- | ---------------------- | --------------------- | ------------------- |
| 혜택ID                | 혜택 고유 식별 번호 (PK)                    | benefit_id             | VARCHAR / INT         | **필수**      |
| 카드번호              | 소속된 카드의 고유 번호 (FK)                | source_card_id         | VARCHAR / INT         | **필수**      |
| 혜택순번              | 노출 또는 적용 우선순위                     | benefit_order          | INTEGER               | **필수**      |
| 카테고리              | 표준화된 대표 업종 카테고리                 | category               | VARCHAR               | **필수**      |
| 카테고리목록          | 세부 적용 카테고리 리스트                   | category_list          | TEXT / JSON           | 선택                |
| 카테고리_원본         | 카드사 표준 원본 문구 또는 분류             | category_raw           | VARCHAR               | 선택                |
| 혜택유형              | 할인, 적립, 캐시백 등 유형                  | benefit_type           | VARCHAR               | **필수**      |
| 혜택값                | 할인율 또는 할인 금액 수치                  | benefit_value          | NUMERIC               | **필수**      |
| 혜택단위              | %, 원, 마일리지 등 수치 단위                | benefit_unit           | VARCHAR               | **필수**      |
| 실적조건              | 해당 혜택을 받기 위한 최소 실적             | performance_condition  | INTEGER               | 선택                |
| 한도_회당             | 1회 결제 시 받을 수 있는 최대 한도          | per_transaction_limit  | INTEGER               | 선택                |
| 한도_월               | 월간 결제 이용 금액 한도                    | monthly_spending_limit | INTEGER               | 선택                |
| 한도_월_최대구간      | 실적 구간별 월 최대 혜택 구간 정보          | monthly_max_tier       | VARCHAR               | 선택                |
| 한도_일               | 일간 결제 이용 금액 한도                    | daily_spending_limit   | INTEGER               | 선택                |
| 한도_연               | 연간 결제 이용 금액 한도                    | annual_spending_limit  | INTEGER               | 선택                |
| 횟수_일               | 하루에 이용 가능한 최대 횟수                | daily_count_limit      | INTEGER               | 선택                |
| 횟수_월               | 한 달에 이용 가능한 최대 횟수               | monthly_count_limit    | INTEGER               | 선택                |
| 월최대혜택액          | 해당 혜택으로 받을 수 있는 월 최대 금액     | monthly_benefit_limit  | INTEGER               | 선택                |
| 한도없음              | 한도 제한 없는 혜택 여부                    | is_unlimited           | BOOLEAN               | **필수**      |
| 한도확보              | 특정 조건 충족 시 한도 추가 부여 여부       | has_extra_limit        | BOOLEAN               | **필수**      |
| 적용범위              | 온/오프라인, 특정 가맹점 등 범위            | coverage_scope         | VARCHAR               | 선택                |
| 옵션그룹              | 다중 선택 또는 조건부 옵션 그룹 식별자      | option_group           | VARCHAR               | 선택                |
| 옵션헤더              | 옵션 조건의 제목 또는 타이틀                | option_header          | VARCHAR               | 선택                |
| 옵션형                | 선택형 혜택 여부 또는 옵션 타입             | is_optional            | VARCHAR               | 선택                |
| 가맹점수준            | 브랜드 단위, 본사 단위 등 적용 레벨         | merchant_level         | VARCHAR               | 선택                |
| 가맹점목록            | 혜택이 적용되는 구체적인 대상 가맹점 리스트 | merchant_list          | TEXT / JSON           | 선택                |
| 요약                  | 혜택 짧은 요약 문구                         | summary                | VARCHAR               | **필수**      |
| 상세                  | 혜택 상세 유의사항 및 조건 전체 문구        | details                | TEXT                  | 선택                |
| 스냅샷일자            | 데이터 수집 및 업데이트 기준일              | snapshot_date          | DATE                  | **필수**      |
