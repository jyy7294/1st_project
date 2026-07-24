from datetime import date, datetime, timezone
import re
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import (
    BenefitUsage,
    Card,
    CardEligibilityRule,
    CardRecommendationSnapshot,
    DemoPaymentSession,
    MonthlyCardUsage,
    Transaction,
    TransactionReward,
    User,
    UserCard,
    UserEligibility,
    UserPersonaProfile,
)
from app.services.card_registration_service import register_virtual_card
from app.services.auth_service import (
    get_current_user,
    login_response,
    require_admin,
    require_user_access,
    revoke_refresh_token,
    rotate_refresh_token,
    verify_password,
)
from app.services.recommendation_debug_service import (
    build_recommendation_debug,
)
from app.services.recommendation_service import (
    calculate_card_benefit,
    recommend_cards,
)
from app.services.user_state_adapter import (
    NoActiveUserCardsError,
    UserNotFoundError,
    build_user_card_states,
    resolve_payment_category,
)
from app.schemas.recommendation import RecommendationResponse
from app.schemas.spending_pattern_recommendation import (
    SpendingPatternRecommendationResponse,
)
from app.schemas.spending_report import MonthlySpendingReportResponse
from app.services.spending_report_service import (
    SpendingReportUserNotFoundError,
    build_monthly_spending_report,
)
from app.services.spending_pattern_recommendation_service import (
    SpendingRecommendationUserNotFoundError,
    get_daily_card_recommendations,
    recommend_new_cards_by_spending,
)
from app.services.category_normalization import normalize_payment_category
from app.services.reward_service import calculate_transaction_rewards
from app.services.recommendation_audit_service import save_recommendation_audit
from app.services.benefit_total_service import confirmed_benefit_totals_by_card
from app.services.payment_gateway_service import authorize_demo_payment
from app.services.privacy_audit_service import save_privacy_change_audit
from app.services.pii_encryption_service import decrypt_text, encrypt_text
from app.services.pii_encryption_service import email_blind_index
from app.services.sensitive_log_filter import install_sensitive_data_log_filter
from app.services.daily_recommendation_scheduler import (
    daily_recommendation_scheduler,
)


app = FastAPI(
    title="PICKA Card Recommendation API",
    description="사용자의 보유 카드와 사용 상태를 반영해 결제 카드를 추천합니다.",
    version="1.1.0",
    swagger_ui_oauth2_redirect_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def start_daily_recommendation_scheduler() -> None:
    install_sensitive_data_log_filter()
    daily_recommendation_scheduler.start()


@app.on_event("shutdown")
def stop_daily_recommendation_scheduler() -> None:
    daily_recommendation_scheduler.stop()


COMPARISON_OPERATORS = {"EQ", "GTE", "LTE", "CONTAINS"}


class StrictRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserEligibilityInput(StrictRequestModel):
    eligibility_type: str = Field(min_length=1, max_length=100)
    eligibility_value: str = Field(min_length=1, max_length=255)
    expires_at: datetime | None = None

    @field_validator("eligibility_type")
    @classmethod
    def normalize_uppercase(cls, value: str) -> str:
        return value.strip().upper()


class UserEligibilityUpdateRequest(StrictRequestModel):
    eligibilities: list[UserEligibilityInput]

    @model_validator(mode="after")
    def validate_unique_types(self):
        types = [item.eligibility_type for item in self.eligibilities]
        if len(types) != len(set(types)):
            raise ValueError("eligibility_type은 요청 안에서 중복될 수 없습니다.")
        return self


class PersonalProfileUpdateRequest(StrictRequestModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    birth_date: date | None = None
    phone_number: str | None = Field(default=None, max_length=30)
    gender: str | None = Field(default=None, max_length=30)
    occupation: str | None = Field(default=None, max_length=200)
    residence: str | None = Field(default=None, max_length=200)
    eligibilities: list[UserEligibilityInput] | None = None

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("생년월일은 미래일 수 없습니다.")
        return value

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = re.sub(r"[\s-]", "", value)
        if not normalized.isdigit() or not 7 <= len(normalized) <= 15:
            raise ValueError("전화번호 형식이 올바르지 않습니다.")
        return normalized

    @field_validator("name", "gender", "occupation", "residence")
    @classmethod
    def trim_optional_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @model_validator(mode="after")
    def validate_unique_eligibility_types(self):
        if self.eligibilities is None:
            return self
        types = [item.eligibility_type for item in self.eligibilities]
        if len(types) != len(set(types)):
            raise ValueError("eligibility_type은 요청 안에서 중복될 수 없습니다.")
        return self


class CardEligibilityRuleInput(StrictRequestModel):
    eligibility_type: str = Field(min_length=1, max_length=100)
    required_value: str = Field(min_length=1, max_length=255)
    comparison_operator: str = "EQ"
    description: str | None = None

    @field_validator("eligibility_type", "comparison_operator")
    @classmethod
    def normalize_uppercase(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("comparison_operator")
    @classmethod
    def validate_operator(cls, value: str) -> str:
        if value not in COMPARISON_OPERATORS:
            raise ValueError("지원하지 않는 comparison_operator입니다.")
        return value


class CardEligibilityRuleUpdateRequest(StrictRequestModel):
    rules: list[CardEligibilityRuleInput]

    @model_validator(mode="after")
    def validate_unique_types(self):
        types = [item.eligibility_type for item in self.rules]
        if len(types) != len(set(types)):
            raise ValueError("eligibility_type은 요청 안에서 중복될 수 없습니다.")
        return self


class RecommendationRequest(StrictRequestModel):
    user_id: int = Field(..., gt=0, examples=[2])
    merchant_name: str = Field(..., min_length=1, examples=["스타벅스 강남점"])
    payment_category: str | None = Field(default=None, examples=["카페/디저트"])
    payment_amount: int = Field(..., gt=0, examples=[12000])
    usage_month: str | None = Field(
        default=None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        examples=["2026-07"],
    )


class CardSelectionRequest(StrictRequestModel):
    user_id: int = Field(..., gt=0, examples=[2])
    merchant_name: str = Field(
        ...,
        min_length=1,
        examples=["스타벅스 강남점"],
    )
    payment_category: str | None = Field(
        default=None,
        examples=["카페/디저트"],
    )
    payment_amount: int = Field(
        ...,
        gt=0,
        examples=[12000],
    )
    selected_card_id: int = Field(
        ...,
        gt=0,
        examples=[3],
    )
    usage_month: str | None = Field(
        default=None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        examples=["2026-07"],
    )


class TransactionCreateRequest(StrictRequestModel):
    user_id: int = Field(..., examples=[2])
    card_id: int = Field(..., examples=[53])
    merchant_name: str = Field(
        ...,
        examples=["스타벅스 강남점"],
    )
    payment_amount: int = Field(..., examples=[12000])
    payment_category: str | None = Field(
        default=None,
        examples=["카페/디저트"],
    )
    usage_month: str | None = Field(
        default=None,
        examples=["2026-07"],
    )


class TransactionMerchantResponse(BaseModel):
    merchant_name: str
    payment_category: str


class TransactionCardResponse(BaseModel):
    card_id: int
    user_card_id: int | None
    card_name: str
    card_company: str | None
    nickname: str | None


class TransactionPaymentResponse(BaseModel):
    original_payment_amount: int
    saved_amount: int
    final_approved_amount: int


class AppliedBenefitResponse(BaseModel):
    benefit_name: str | None
    category: str | None
    benefit_type: str | None
    benefit_value: float | None
    benefit_unit: str | None
    applied: bool


class TransactionCreateResponse(BaseModel):
    status: str
    message: str
    transaction_id: int | None
    approval_number: str
    approved_at: str
    user_id: int
    usage_month: str
    data_source: str
    demo_session_id: int | None
    merchant: TransactionMerchantResponse
    card: TransactionCardResponse
    payment: TransactionPaymentResponse
    applied_benefit: AppliedBenefitResponse
    rewards: list[dict]


class TransactionHistoryItemResponse(BaseModel):
    transaction_id: int
    merchant_name: str
    payment_category: str | None
    original_payment_amount: int
    saved_amount: int
    final_approved_amount: int
    applied_benefit_name: str | None
    approval_number: str
    status: str
    usage_month: str
    approved_at: datetime
    data_source: str
    demo_session_id: int | None


class TransactionHistoryListResponse(BaseModel):
    user_id: int
    card_id: int
    usage_month: str | None
    total_count: int
    limit: int
    offset: int
    transactions: list[TransactionHistoryItemResponse]


class LocalLoginRequest(StrictRequestModel):
    email: str = Field(
        ..., min_length=3, max_length=320, examples=["test@example.com"]
    )
    password: str = Field(
        ..., min_length=1, max_length=256, examples=["password123"]
    )


class AuthUserResponse(BaseModel):
    user_id: int
    username: str | None
    email: str | None
    name: str | None


class LoginResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: AuthUserResponse


class RefreshTokenRequest(StrictRequestModel):
    refresh_token: str = Field(min_length=1)


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: AuthUserResponse


class LogoutResponse(BaseModel):
    message: str


class ManualCardRegistrationRequest(StrictRequestModel):
    card_number: str = Field(
        ...,
        examples=["1111-2222-3333-4444"],
    )
    expiry_month: int = Field(..., ge=1, le=12, examples=[12])
    expiry_year: int = Field(..., examples=[2029])
    cvc: str = Field(..., pattern=r"^\d{3}$", examples=["123"])
    card_password_first2: str = Field(
        ...,
        pattern=r"^\d{2}$",
        examples=["45"],
    )

    @field_validator("card_number")
    @classmethod
    def normalize_card_number(cls, value: str) -> str:
        normalized = value.replace(" ", "").replace("-", "")
        if not normalized.isdigit() or len(normalized) != 16:
            raise ValueError("카드번호는 숫자 16자리여야 합니다.")
        return normalized

    @model_validator(mode="after")
    def validate_expiry(self):
        today = date.today()
        if (self.expiry_year, self.expiry_month) < (
            today.year,
            today.month,
        ):
            raise ValueError("만료된 카드는 등록할 수 없습니다.")
        return self


class ScannedCardRegistrationRequest(ManualCardRegistrationRequest):
    pass


class RegisteredUserCardResponse(BaseModel):
    user_card_id: int
    user_id: int
    card_id: int
    card_name: str
    card_company: str | None
    masked_card_number: str
    expiry_month: int
    expiry_year: int
    registration_method: str
    previous_month_spending: int
    current_month_spending: int
    is_active: bool


class CardRegistrationResponse(BaseModel):
    message: str
    card: RegisteredUserCardResponse


class DeleteUserCardResponse(BaseModel):
    message: str
    user_id: int
    card_id: int


def transaction_history_item(transaction: Transaction) -> dict:
    return {
        "transaction_id": transaction.id,
        "merchant_name": transaction.merchant_name,
        "payment_category": transaction.payment_category,
        "original_payment_amount": transaction.original_payment_amount,
        "saved_amount": transaction.saved_amount,
        "final_approved_amount": transaction.final_approved_amount,
        "applied_benefit_name": transaction.applied_benefit_name,
        "approval_number": transaction.approval_number,
        "status": transaction.status,
        "usage_month": transaction.usage_month,
        "approved_at": transaction.approved_at,
        "data_source": transaction.data_source,
        "demo_session_id": transaction.demo_session_id,
    }


def registered_card_response(
    db: Session,
    user_card: UserCard,
    credential,
    usage_month: str,
) -> dict:
    card = db.get(Card, user_card.card_id)
    usage = db.scalar(
        select(MonthlyCardUsage).where(
            MonthlyCardUsage.user_id == user_card.user_id,
            MonthlyCardUsage.card_id == user_card.card_id,
            MonthlyCardUsage.usage_month == usage_month,
        )
    )
    return {
        "message": "카드가 등록되었습니다.",
        "card": {
            "user_card_id": user_card.id,
            "user_id": user_card.user_id,
            "card_id": user_card.card_id,
            "card_name": card.card_name,
            "card_company": card.issuer,
            "masked_card_number": (
                f"**** **** **** {user_card.card_number_last4}"
            ),
            "expiry_month": credential.expiry_month,
            "expiry_year": credential.expiry_year,
            "registration_method": user_card.registration_method,
            "previous_month_spending": (
                usage.previous_month_spending if usage else 0
            ),
            "current_month_spending": (
                usage.current_month_spending if usage else 0
            ),
            "is_active": user_card.is_active,
        },
    }


@app.post(
    "/api/v1/auth/login",
    response_model=LoginResponse,
    summary="아이디와 비밀번호 로그인",
)
def local_login(
    request: LocalLoginRequest,
    db: Annotated[Session, Depends(get_db)],
):
    user = db.scalar(
        select(User).where(
            User.email_blind_index == email_blind_index(request.email)
        )
    )
    if (
        user is None
        or not user.is_active
        or not verify_password(request.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=401,
            detail="아이디 또는 비밀번호가 올바르지 않습니다.",
        )
    return login_response(db, user)


@app.post(
    "/api/v1/auth/refresh",
    response_model=TokenPairResponse,
    summary="Access Token 재발급",
)
def refresh_access_token(
    request: RefreshTokenRequest,
    db: Annotated[Session, Depends(get_db)],
):
    return rotate_refresh_token(db, request.refresh_token)


@app.post(
    "/api/v1/auth/logout",
    response_model=LogoutResponse,
    summary="로그아웃 및 Refresh Token 폐기",
)
def logout(
    request: RefreshTokenRequest,
    db: Annotated[Session, Depends(get_db)],
):
    revoke_refresh_token(db, request.refresh_token)
    return {"message": "로그아웃되었습니다."}


@app.get("/")
def root():
    return {"message": "PICKA 카드 추천 API 서버가 실행 중입니다."}


@app.get("/health")
def health_check():
    return {"status": "ok"}


def _user_eligibility_payload(item: UserEligibility) -> dict:
    value = item.eligibility_value
    if item.eligibility_value_encrypted is not None:
        value = decrypt_text(
            item.eligibility_value_encrypted,
            context=f"eligibility:{item.user_id}:{item.eligibility_type}",
        )
    return {
        "user_id": item.user_id,
        "eligibility_type": item.eligibility_type,
        "eligibility_value": value,
        "verification_status": item.verification_status,
        "verified_at": item.verified_at,
        "expires_at": item.expires_at,
    }


def _age_on(birth_date: date | None, today: date | None = None) -> int:
    if birth_date is None:
        return 0
    reference = today or date.today()
    return reference.year - birth_date.year - (
        (reference.month, reference.day) < (birth_date.month, birth_date.day)
    )


def _personal_profile_payload(db: Session, user: User) -> dict:
    profile = user.persona_profile
    birth_date = profile.birth_date if profile else None
    phone_number = profile.phone_number if profile else None
    residence = profile.residence if profile else None
    if profile and profile.birth_date_encrypted is not None:
        decrypted_birth_date = decrypt_text(
            profile.birth_date_encrypted,
            context=f"profile:{user.id}:birth_date",
        )
        birth_date = date.fromisoformat(decrypted_birth_date)
    if profile and profile.phone_number_encrypted is not None:
        phone_number = decrypt_text(
            profile.phone_number_encrypted,
            context=f"profile:{user.id}:phone_number",
        )
    if profile and profile.residence_encrypted is not None:
        residence = decrypt_text(
            profile.residence_encrypted,
            context=f"profile:{user.id}:residence",
        )
    rows = db.scalars(
        select(UserEligibility)
        .where(UserEligibility.user_id == user.id)
        .order_by(UserEligibility.eligibility_type)
    ).all()
    return {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "birth_date": birth_date,
        "phone_number": phone_number,
        "gender": profile.gender if profile else None,
        "occupation": profile.job if profile else None,
        "residence": residence,
        "eligibilities": [_user_eligibility_payload(row) for row in rows],
    }


@app.get("/api/v1/users/{user_id}/personal-profile")
def get_personal_profile(
    user_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    require_user_access(user_id, current_user)
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return _personal_profile_payload(db, user)


@app.patch("/api/v1/users/{user_id}/personal-profile")
def update_personal_profile(
    user_id: Annotated[int, Path(gt=0)],
    request: PersonalProfileUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    require_user_access(user_id, current_user)
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    if "name" in request.model_fields_set and request.name is None:
        raise HTTPException(status_code=422, detail="이름은 비울 수 없습니다.")

    changed_fields: list[str] = []
    if "name" in request.model_fields_set and user.name != request.name:
        user.name = request.name
        changed_fields.append("name")

    profile_field_map = {
        "birth_date": "birth_date",
        "phone_number": "phone_number",
        "gender": "gender",
        "occupation": "job",
        "residence": "residence",
    }
    requested_profile_fields = set(profile_field_map) & request.model_fields_set
    profile = user.persona_profile
    if requested_profile_fields and profile is None:
        profile = UserPersonaProfile(
            persona_id=f"user-{user_id}",
            age=_age_on(request.birth_date),
            source_payload={},
        )
        user.persona_profile = profile
    for api_field in requested_profile_fields:
        model_field = profile_field_map[api_field]
        new_value = getattr(request, api_field)
        if getattr(profile, model_field) != new_value:
            setattr(profile, model_field, new_value)
            changed_fields.append(api_field)
        if api_field in {"birth_date", "phone_number", "residence"}:
            serialized = (
                new_value.isoformat()
                if isinstance(new_value, date)
                else new_value
            )
            setattr(
                profile,
                f"{model_field}_encrypted",
                encrypt_text(
                    serialized,
                    context=f"profile:{user_id}:{api_field}",
                ),
            )
    if profile is not None and "birth_date" in requested_profile_fields:
        profile.age = _age_on(request.birth_date)

    if request.eligibilities is not None:
        existing = {
            row.eligibility_type: row
            for row in db.scalars(
                select(UserEligibility).where(UserEligibility.user_id == user_id)
            ).all()
        }
        now = datetime.now(timezone.utc)
        for item in request.eligibilities:
            row = existing.get(item.eligibility_type)
            values_changed = row is None or any((
                row.eligibility_value != item.eligibility_value,
                row.verification_status != "SELF_REPORTED",
                row.expires_at != item.expires_at,
            ))
            if row is None:
                row = UserEligibility(
                    user_id=user_id,
                    eligibility_type=item.eligibility_type,
                    eligibility_value=item.eligibility_value,
                    verification_status="SELF_REPORTED",
                )
                db.add(row)
            else:
                row.eligibility_value = item.eligibility_value
                row.verification_status = "SELF_REPORTED"
            row.eligibility_value_encrypted = encrypt_text(
                item.eligibility_value,
                context=f"eligibility:{user_id}:{item.eligibility_type}",
            )
            row.verified_at = now
            row.expires_at = item.expires_at
            if values_changed:
                changed_fields.append(f"eligibility.{item.eligibility_type}")

    if changed_fields:
        db.execute(
            delete(CardRecommendationSnapshot).where(
                CardRecommendationSnapshot.user_id == user_id
            )
        )
        save_privacy_change_audit(
            db,
            actor_user_id=current_user.id,
            target_user_id=user_id,
            changed_fields=changed_fields,
        )
    db.commit()
    db.refresh(user)
    return _personal_profile_payload(db, user)


@app.get("/api/v1/users/{user_id}/eligibilities")
def get_user_eligibilities(
    user_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    require_user_access(user_id, current_user)
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    rows = db.scalars(
        select(UserEligibility)
        .where(UserEligibility.user_id == user_id)
        .order_by(UserEligibility.eligibility_type)
    ).all()
    return {
        "user_id": user_id,
        "eligibilities": [_user_eligibility_payload(row) for row in rows],
    }


@app.put("/api/v1/users/{user_id}/eligibilities")
def update_user_eligibilities(
    user_id: Annotated[int, Path(gt=0)],
    request: UserEligibilityUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    require_user_access(user_id, current_user)
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    existing = {
        row.eligibility_type: row
        for row in db.scalars(
            select(UserEligibility).where(UserEligibility.user_id == user_id)
        ).all()
    }
    now = datetime.now(timezone.utc)
    for item in request.eligibilities:
        row = existing.get(item.eligibility_type)
        if row is None:
            row = UserEligibility(
                user_id=user_id,
                eligibility_type=item.eligibility_type,
                eligibility_value=item.eligibility_value,
                verification_status="SELF_REPORTED",
            )
            db.add(row)
        else:
            row.eligibility_value = item.eligibility_value
            row.verification_status = "SELF_REPORTED"
        row.eligibility_value_encrypted = encrypt_text(
            item.eligibility_value,
            context=f"eligibility:{user_id}:{item.eligibility_type}",
        )
        row.verified_at = now
        row.expires_at = item.expires_at

    db.execute(
        delete(CardRecommendationSnapshot).where(
            CardRecommendationSnapshot.user_id == user_id
        )
    )
    db.commit()
    return get_user_eligibilities(user_id, db, current_user)


def _card_rule_payload(item: CardEligibilityRule) -> dict:
    return {
        "id": item.id,
        "card_id": item.card_id,
        "eligibility_type": item.eligibility_type,
        "comparison_operator": item.comparison_operator,
        "required_value": item.required_value,
        "description": item.description,
    }


@app.get("/api/v1/cards/{card_id}/eligibility-rules")
def get_card_eligibility_rules(
    card_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
):
    if db.get(Card, card_id) is None:
        raise HTTPException(status_code=404, detail="카드를 찾을 수 없습니다.")
    rows = db.scalars(
        select(CardEligibilityRule)
        .where(CardEligibilityRule.card_id == card_id)
        .order_by(CardEligibilityRule.eligibility_type)
    ).all()
    return {"card_id": card_id, "rules": [_card_rule_payload(row) for row in rows]}


@app.put("/api/v1/cards/{card_id}/eligibility-rules")
def replace_card_eligibility_rules(
    card_id: Annotated[int, Path(gt=0)],
    request: CardEligibilityRuleUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    require_admin(current_user)
    if db.get(Card, card_id) is None:
        raise HTTPException(status_code=404, detail="카드를 찾을 수 없습니다.")
    db.execute(
        delete(CardEligibilityRule).where(CardEligibilityRule.card_id == card_id)
    )
    db.add_all([
        CardEligibilityRule(card_id=card_id, **item.model_dump())
        for item in request.rules
    ])
    db.execute(delete(CardRecommendationSnapshot))
    db.commit()
    return get_card_eligibility_rules(card_id, db, current_user)


@app.get(
    "/api/v1/users/{user_id}/cards",
    summary="사용자 보유 카드 조회",
    description="사용자의 활성 보유 카드 목록과 해당 월의 카드 사용 상태를 조회합니다.",
)
def get_user_cards(
    user_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    usage_month: Annotated[
        str | None,
        Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    ] = None,
):
    require_user_access(user_id, current_user)
    usage_month = usage_month or date.today().strftime("%Y-%m")

    try:
        user_card_states = build_user_card_states(
            db=db,
            user_id=user_id,
            usage_month=usage_month,
        )
        return {
            "user_id": user_id,
            "usage_month": usage_month,
            "user_state_source": "database",
            "total_count": len(user_card_states),
            "cards": user_card_states,
        }
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except NoActiveUserCardsError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="사용자 보유 카드 조회 중 데이터베이스 오류가 발생했습니다.",
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="사용자 보유 카드 조회 중 오류가 발생했습니다.",
        ) from error


def process_card_registration(
    request: ManualCardRegistrationRequest,
    user_id: int,
    registration_method: str,
    db: Session,
) -> dict:
    usage_month = date.today().strftime("%Y-%m")
    try:
        user_card, credential = register_virtual_card(
            db=db,
            user_id=user_id,
            card_number=request.card_number,
            expiry_month=request.expiry_month,
            expiry_year=request.expiry_year,
            cvc=request.cvc,
            card_password_first2=request.card_password_first2,
            registration_method=registration_method,
            usage_month=usage_month,
        )
        return registered_card_response(
            db,
            user_card,
            credential,
            usage_month,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="카드 등록 중 데이터베이스 오류가 발생했습니다.",
        ) from error


@app.post(
    "/api/v1/users/{user_id}/cards/manual",
    response_model=CardRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="가상 카드 직접 입력 등록",
)
def register_card_manually(
    user_id: Annotated[int, Path(gt=0)],
    request: ManualCardRegistrationRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    require_user_access(user_id, current_user)
    return process_card_registration(request, user_id, "MANUAL", db)


@app.post(
    "/api/v1/users/{user_id}/cards/scan",
    response_model=CardRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="가상 카드 스캔 결과 등록",
)
def register_scanned_card(
    user_id: Annotated[int, Path(gt=0)],
    request: ScannedCardRegistrationRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    require_user_access(user_id, current_user)
    return process_card_registration(request, user_id, "SCAN", db)


@app.get(
    "/api/v1/users/{user_id}/cards/{card_id}",
    summary="사용자 카드 상세 조회",
    description="사용자의 특정 보유 카드 상세 정보와 혜택 목록을 조회합니다.",
)
def get_user_card_detail(
    user_id: Annotated[int, Path(gt=0)],
    card_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    usage_month: Annotated[
        str | None,
        Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    ] = None,
):
    require_user_access(user_id, current_user)
    usage_month = usage_month or date.today().strftime("%Y-%m")

    try:
        user_card_states = build_user_card_states(
            db=db,
            user_id=user_id,
            usage_month=usage_month,
        )
        selected_card = next(
            (
                card
                for card in user_card_states
                if card["card_id"] == card_id
            ),
            None,
        )
        if selected_card is None:
            raise HTTPException(
                status_code=404,
                detail="사용자의 보유 카드가 아닙니다.",
            )

        recent_transactions = db.scalars(
            select(Transaction)
            .where(
                Transaction.user_id == user_id,
                Transaction.card_id == card_id,
            )
            .order_by(Transaction.approved_at.desc(), Transaction.id.desc())
            .limit(5)
        ).all()

        return {
            "user_id": user_id,
            "usage_month": usage_month,
            "user_state_source": "database",
            "card": selected_card,
            "recent_transactions": [
                transaction_history_item(transaction)
                for transaction in recent_transactions
            ],
        }
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except NoActiveUserCardsError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="사용자 카드 상세 조회 중 데이터베이스 오류가 발생했습니다.",
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="사용자 카드 상세 조회 중 오류가 발생했습니다.",
        ) from error


@app.delete(
    "/api/v1/users/{user_id}/cards/{card_id}",
    response_model=DeleteUserCardResponse,
    summary="사용자 보유 카드 삭제",
)
def delete_user_card(
    user_id: Annotated[int, Path(gt=0)],
    card_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    require_user_access(user_id, current_user)
    try:
        if db.get(User, user_id) is None:
            raise HTTPException(
                status_code=404,
                detail=f"사용자 ID {user_id}를 찾을 수 없습니다.",
            )
        user_card = db.scalar(
            select(UserCard).where(
                UserCard.user_id == user_id,
                UserCard.card_id == card_id,
                UserCard.is_active.is_(True),
            )
        )
        if user_card is None:
            raise HTTPException(
                status_code=404,
                detail="등록된 보유 카드를 찾을 수 없습니다.",
            )
        user_card.is_active = False
        db.commit()
        return {
            "message": "보유 카드가 삭제되었습니다.",
            "user_id": user_id,
            "card_id": card_id,
        }
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="보유 카드 삭제 중 데이터베이스 오류가 발생했습니다.",
        ) from error


@app.post(
    "/api/v1/transactions",
    response_model=TransactionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="가상 결제 처리",
    description=(
        "선택한 카드로 가상 결제를 처리하고 결제 금액, "
        "절약 혜택, 최종 승인 금액을 반환합니다. "
        "실제 카드 승인이나 PG사 연동은 수행하지 않습니다."
    ),
)
def create_transaction(
    request: TransactionCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    require_user_access(request.user_id, current_user)
    if (
        request.user_id < 1
        or request.card_id < 1
        or request.payment_amount <= 0
        or not request.merchant_name.strip()
        or (
            request.usage_month is not None
            and re.fullmatch(
                r"\d{4}-(0[1-9]|1[0-2])",
                request.usage_month,
            )
            is None
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="결제 요청값이 올바르지 않습니다.",
        )

    usage_month = request.usage_month or date.today().strftime("%Y-%m")

    try:
        payment_category = resolve_payment_category(
            db,
            merchant_name=request.merchant_name,
            supplied_category=request.payment_category,
        )
        user_card_states = build_user_card_states(
            db=db,
            user_id=request.user_id,
            usage_month=usage_month,
        )
        selected_card = next(
            (
                card
                for card in user_card_states
                if card["card_id"] == request.card_id
            ),
            None,
        )
        if selected_card is None:
            raise HTTPException(
                status_code=404,
                detail="사용자의 보유 카드가 아닙니다.",
            )

        selected_user_card = db.scalar(
            select(UserCard).where(
                UserCard.id == selected_card["user_card_id"],
                UserCard.user_id == request.user_id,
                UserCard.card_id == request.card_id,
            )
        )
        if selected_user_card is None:
            raise HTTPException(
                status_code=404,
                detail="사용자의 보유 카드가 아닙니다.",
            )

        # 같은 카드의 동시 결제가 월 통합한도를 함께 통과하지 못하도록
        # 월 집계 행을 잠근 뒤 저장 직전의 확정 혜택 합계로 다시 검사한다.
        monthly_usage = db.scalar(
            select(MonthlyCardUsage)
            .where(
                MonthlyCardUsage.user_id == request.user_id,
                MonthlyCardUsage.card_id == request.card_id,
                MonthlyCardUsage.usage_month == usage_month,
            )
            .with_for_update()
        )
        if monthly_usage is None:
            monthly_usage = MonthlyCardUsage(
                user_id=request.user_id,
                card_id=request.card_id,
                usage_month=usage_month,
                previous_month_spending=0,
                current_month_spending=0,
                card_monthly_benefit_used=0,
            )
            db.add(monthly_usage)
            db.flush()

        calculation = calculate_card_benefit(
            card=selected_card,
            merchant_name=request.merchant_name,
            payment_category=payment_category,
            payment_amount=request.payment_amount,
        )
        raw_benefit = calculation.get("expected_benefit")
        if not isinstance(raw_benefit, (int, float)):
            raise HTTPException(
                status_code=400,
                detail="혜택 계산 결과가 올바르지 않습니다.",
            )

        saved_amount = int(
            min(max(raw_benefit, 0), request.payment_amount)
        )
        monthly_total_limit = selected_card.get("monthly_total_limit")
        if monthly_total_limit is not None:
            confirmed_used = confirmed_benefit_totals_by_card(
                db,
                user_id=request.user_id,
                usage_month=usage_month,
            ).get(request.card_id, 0)
            saved_amount = min(
                saved_amount,
                max(int(monthly_total_limit) - confirmed_used, 0),
            )
        applied = saved_amount > 0 and bool(calculation.get("eligible"))
        benefit_name = calculation.get("benefit_name") if applied else None
        benefit = next(
            (
                item
                for item in selected_card["benefits"]
                if item.get("benefit_name") == benefit_name
            ),
            None,
        )

        authorization = authorize_demo_payment(
            selected_user_card,
            payment_amount=request.payment_amount,
        )
        approval_number = authorization.approval_number
        approved_at = datetime.now(timezone.utc)
        demo_session = db.scalar(
            select(DemoPaymentSession)
            .where(
                DemoPaymentSession.user_id == request.user_id,
                DemoPaymentSession.status == "ACTIVE",
            )
            .order_by(DemoPaymentSession.started_at.desc())
        )
        if demo_session is None:
            demo_session = DemoPaymentSession(
                user_id=request.user_id,
                status="ACTIVE",
            )
            db.add(demo_session)
            db.flush()
        final_approved_amount = request.payment_amount - saved_amount
        transaction = Transaction(
            user_id=request.user_id,
            user_card_id=selected_card["user_card_id"],
            card_id=request.card_id,
            merchant_name=request.merchant_name,
            payment_category=payment_category,
            original_payment_amount=request.payment_amount,
            saved_amount=saved_amount,
            final_approved_amount=final_approved_amount,
            applied_benefit_name=benefit_name,
            applied_benefit_category=(
                benefit.get("category") if benefit else None
            ),
            approval_number=approval_number,
            status="APPROVED",
            usage_month=usage_month,
            approved_at=approved_at,
            data_source="DEMO",
            demo_session_id=demo_session.id,
        )
        db.add(transaction)
        db.flush()

        rewards = calculate_transaction_rewards(
            selected_card,
            payment_category=payment_category,
            payment_amount=request.payment_amount,
        )
        for reward in rewards:
            db.add(TransactionReward(
                transaction_id=transaction.id,
                **reward,
            ))

        monthly_usage.current_month_spending += request.payment_amount
        monthly_usage.card_monthly_benefit_used += saved_amount

        if applied and benefit and benefit.get("card_benefit_id") is not None:
            benefit_usage = db.scalar(
                select(BenefitUsage).where(
                    BenefitUsage.user_id == request.user_id,
                    BenefitUsage.card_benefit_id
                    == benefit["card_benefit_id"],
                    BenefitUsage.usage_month == usage_month,
                )
            )
            if benefit_usage is None:
                benefit_usage = BenefitUsage(
                    user_id=request.user_id,
                    card_id=request.card_id,
                    card_benefit_id=benefit["card_benefit_id"],
                    usage_month=usage_month,
                    monthly_used_amount=0,
                    monthly_used_count=0,
                    daily_used_count=0,
                )
                db.add(benefit_usage)
            benefit_usage.monthly_used_amount += saved_amount
            benefit_usage.monthly_used_count += 1
            benefit_usage.daily_used_count += 1

        db.commit()
        db.refresh(transaction)

        return {
            "status": "APPROVED",
            "message": "결제가 완료되었습니다.",
            "transaction_id": transaction.id,
            "approval_number": transaction.approval_number,
            "approved_at": transaction.approved_at.isoformat(),
            "user_id": request.user_id,
            "usage_month": usage_month,
            "data_source": transaction.data_source,
            "demo_session_id": transaction.demo_session_id,
            "merchant": {
                "merchant_name": request.merchant_name,
                "payment_category": payment_category,
            },
            "card": {
                "card_id": selected_card["card_id"],
                "user_card_id": selected_card.get("user_card_id"),
                "card_name": selected_card["card_name"],
                "card_company": selected_card.get("card_company"),
                "nickname": selected_card.get("nickname"),
            },
            "payment": {
                "original_payment_amount": request.payment_amount,
                "saved_amount": saved_amount,
                "final_approved_amount": (
                    final_approved_amount
                ),
            },
            "applied_benefit": {
                "benefit_name": benefit_name,
                "category": benefit.get("category") if benefit else None,
                "benefit_type": (
                    benefit.get("benefit_type") if benefit else None
                ),
                "benefit_value": (
                    benefit.get("benefit_value") if benefit else None
                ),
                "benefit_unit": (
                    benefit.get("benefit_unit") if benefit else None
                ),
                "applied": applied,
            },
            "rewards": rewards,
        }
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except NoActiveUserCardsError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="결제 처리 중 데이터베이스 오류가 발생했습니다.",
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="결제 처리 중 오류가 발생했습니다.",
        ) from error


@app.get(
    "/api/v1/users/{user_id}/cards/{card_id}/transactions",
    response_model=TransactionHistoryListResponse,
    summary="카드별 전체 거래 내역 조회",
    description=(
        "사용자가 보유한 특정 카드의 전체 거래 내역을 "
        "페이지네이션하여 최신순으로 조회합니다."
    ),
)
def get_card_transactions(
    user_id: Annotated[int, Path(gt=0)],
    card_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    usage_month: Annotated[
        str | None,
        Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    ] = None,
):
    require_user_access(user_id, current_user)
    try:
        card_states = build_user_card_states(
            db=db,
            user_id=user_id,
            usage_month=usage_month or date.today().strftime("%Y-%m"),
        )
        if not any(card["card_id"] == card_id for card in card_states):
            raise HTTPException(
                status_code=404,
                detail="사용자의 보유 카드가 아닙니다.",
            )

        filters = [
            Transaction.user_id == user_id,
            Transaction.card_id == card_id,
        ]
        if usage_month is not None:
            filters.append(Transaction.usage_month == usage_month)

        total_count = db.scalar(
            select(func.count())
            .select_from(Transaction)
            .where(*filters)
        )
        transactions = db.scalars(
            select(Transaction)
            .where(*filters)
            .order_by(
                Transaction.approved_at.desc(),
                Transaction.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        ).all()

        return {
            "user_id": user_id,
            "card_id": card_id,
            "usage_month": usage_month,
            "total_count": total_count or 0,
            "limit": limit,
            "offset": offset,
            "transactions": [
                transaction_history_item(transaction)
                for transaction in transactions
            ],
        }
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except NoActiveUserCardsError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="결제 내역 조회 중 데이터베이스 오류가 발생했습니다.",
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="결제 내역 조회 중 오류가 발생했습니다.",
        ) from error


@app.get(
    "/api/v1/users/{user_id}/card-recommendations",
    response_model=SpendingPatternRecommendationResponse,
)
def get_spending_pattern_card_recommendations(
    user_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    card_type: Annotated[
        str,
        Query(alias="type", pattern="^(credit|check)$"),
    ] = "credit",
    limit: Annotated[int, Query(ge=1, le=20)] = 3,
    refresh: Annotated[bool, Query()] = False,
):
    require_user_access(user_id, current_user)
    try:
        result = get_daily_card_recommendations(
            db,
            user_id=user_id,
            card_type=card_type,
            limit=limit,
            force_refresh=refresh,
        )
        save_recommendation_audit(
            db,
            user_id=user_id,
            request_kind="NEW_CARD_SPENDING_PATTERN",
            input_payload={"card_type": card_type, "limit": limit, "refresh": refresh},
            calculation_payload=result,
            policy_version=result.get("policyVersion"),
            cache_hit=bool(result.get("cached")),
        )
        return result
    except SpendingRecommendationUserNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get(
    "/api/v1/users/{user_id}/spending-report",
    response_model=MonthlySpendingReportResponse,
)
def get_monthly_spending_report(
    user_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    month: Annotated[
        str,
        Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    ],
):
    require_user_access(user_id, current_user)
    try:
        return build_monthly_spending_report(
            db,
            user_id=user_id,
            usage_month=month,
        )
    except SpendingReportUserNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post(
    "/api/v1/recommendations",
    response_model=RecommendationResponse,
)
def create_recommendation(
    request: RecommendationRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    require_user_access(request.user_id, current_user)
    usage_month = request.usage_month or date.today().strftime("%Y-%m")

    try:
        user_card_states = build_user_card_states(
            db=db,
            user_id=request.user_id,
            usage_month=usage_month,
        )
        payment_category = resolve_payment_category(
            db,
            merchant_name=request.merchant_name,
            supplied_category=request.payment_category,
        )
        result = recommend_cards(
            merchant_name=request.merchant_name,
            payment_category=payment_category,
            payment_amount=request.payment_amount,
            user_card_states=user_card_states,
        )

        if (
            result["recommended_card"] is None
            and not result.get("selection_required", False)
        ):
            raise HTTPException(
                status_code=404,
                detail="추천 가능한 카드가 없습니다.",
            )

        response = {
            **result,
            "user_id": request.user_id,
            "usage_month": usage_month,
            "user_state_source": "database",
            "owned_card_count": len(user_card_states),
        }
        if settings.recommendation_debug:
            response["debug"] = build_recommendation_debug(
                cards=user_card_states,
                merchant_name=request.merchant_name,
                payment_category=payment_category,
                payment_amount=request.payment_amount,
            )
        save_recommendation_audit(
            db,
            user_id=request.user_id,
            request_kind="PAYMENT_CARD_RECOMMENDATION",
            usage_month=usage_month,
            input_payload={
                "merchant_name": request.merchant_name,
                "payment_category": payment_category,
                "payment_amount": request.payment_amount,
            },
            calculation_payload=response,
        )
        return response
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except NoActiveUserCardsError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="사용자 상태 조회 중 데이터베이스 오류가 발생했습니다.",
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="추천 결과 생성 중 오류가 발생했습니다.",
        ) from error


@app.post("/api/v1/recommendations/select")
def select_recommended_card(
    request: CardSelectionRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    require_user_access(request.user_id, current_user)
    usage_month = request.usage_month or date.today().strftime("%Y-%m")

    try:
        # 1. 해당 사용자의 보유 카드와 사용 상태를 DB에서 조회
        user_card_states = build_user_card_states(
            db=db,
            user_id=request.user_id,
            usage_month=usage_month,
        )

        # 2. 가맹점 업종 확인
        payment_category = resolve_payment_category(
            db,
            merchant_name=request.merchant_name,
            supplied_category=request.payment_category,
        )

        # 3. 사용자가 선택한 카드가 실제 보유 카드인지 확인
        selected_card = next(
            (
                card
                for card in user_card_states
                if card["card_id"] == request.selected_card_id
            ),
            None,
        )

        if selected_card is None:
            raise HTTPException(
                status_code=404,
                detail="선택한 카드는 사용자의 활성 보유 카드가 아닙니다.",
            )

        # 4. 추천 결과 다시 계산
        recommendation_result = recommend_cards(
            merchant_name=request.merchant_name,
            payment_category=payment_category,
            payment_amount=request.payment_amount,
            user_card_states=user_card_states,
        )

        recommended_card = recommendation_result["recommended_card"]

        # 5. 사용자가 선택한 카드의 예상 혜택 계산
        selected_card_result = calculate_card_benefit(
            card=selected_card,
            merchant_name=request.merchant_name,
            payment_category=payment_category,
            payment_amount=request.payment_amount,
        )

        response = {
            "status": "CARD_SELECTED",
            "message": "결제에 사용할 카드가 선택되었습니다.",
            "user_id": request.user_id,
            "usage_month": usage_month,
            "user_state_source": "database",
            "transaction": {
                "merchant_name": request.merchant_name,
                "category": payment_category,
                "amount": request.payment_amount,
            },
            "selected_card": selected_card_result,
            "is_recommended_card": (
                recommended_card is not None
                and recommended_card["card_id"]
                == request.selected_card_id
            ),
        }
        save_recommendation_audit(
            db,
            user_id=request.user_id,
            request_kind="PAYMENT_CARD_SELECTION",
            usage_month=usage_month,
            selected_card_id=request.selected_card_id,
            input_payload={
                "merchant_name": request.merchant_name,
                "payment_category": payment_category,
                "payment_amount": request.payment_amount,
                "selected_card_id": request.selected_card_id,
            },
            calculation_payload={
                "selection": response,
                "original_recommendation": recommendation_result,
            },
        )
        return response

    except UserNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except NoActiveUserCardsError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except HTTPException:
        raise

    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="카드 선택 처리 중 데이터베이스 오류가 발생했습니다.",
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="카드 선택 결과 생성 중 오류가 발생했습니다.",
        ) from error
