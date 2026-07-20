# PICKA Backend

## 로컬 실행

```powershell
python -m uvicorn app.main:app --reload
```

Swagger: `http://localhost:8000/docs`

## 로그인 환경 설정

`.env.example`을 참고해 `.env`에 인증 설정을 추가합니다. 실제 secret은
저장소에 커밋하지 않습니다.

카카오 개발자 콘솔:

- REST API 키와 Client Secret을 발급합니다.
- Redirect URI에
  `http://localhost:8000/api/v1/auth/kakao/callback`을 등록합니다.
- 필요한 동의 항목(이메일, 닉네임, 프로필 이미지)을 설정합니다.

네이버 개발자 센터:

- Client ID와 Client Secret을 발급합니다.
- Callback URL에
  `http://localhost:8000/api/v1/auth/naver/callback`을 등록합니다.
- 제공받을 회원 정보 항목을 설정합니다.

프론트 로그인 버튼:

- 일반 로그인: `POST /api/v1/auth/login`
- 카카오: `GET /api/v1/auth/kakao/authorize`의 URL로 이동
- 네이버: `GET /api/v1/auth/naver/authorize`의 URL로 이동

OAuth callback은 외부 서비스가 전달하는 `code`와 `state`가 필요하므로
Swagger만으로 전체 인증을 완료하기 어렵습니다. 현재 개발용 callback은
서비스 access token과 사용자 정보를 JSON으로 반환합니다. 운영 프론트
연결 시 HttpOnly 쿠키 또는 일회용 code 교환 방식으로 전환하는 것을
권장합니다.

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
