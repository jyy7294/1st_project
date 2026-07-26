# PICKA Backend

## 로컬 실행

```powershell
python -m uvicorn app.main:app --reload
```

Swagger: `http://localhost:8000/docs`

## 로그인

일반 로그인 API `POST /api/v1/auth/login`을 사용합니다.

## 개발용 가상 카드

다음 데이터는 실제 금융정보가 아닌 Swagger 테스트용 가상 데이터입니다.

| card_id | card_number | expiry | cvc | password first 2 |
|---:|---|---|---|---|
| 53 | 1111222233334444 | 12/2029 | 123 | 45 |
| 13 | 5555666677778888 | 06/2030 | 456 | 78 |
| 78 | 9999000011112222 | 09/2028 | 789 | 12 |

멱등 Seed 실행:

```powershell
python -m scripts.seed_virtual_card_credentials
```

이 값은 개발용이지만 API 응답에는 전체 카드번호, CVC, 비밀번호 앞
2자리를 반환하지 않습니다.
