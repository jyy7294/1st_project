from datetime import date, datetime, timezone
import re
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, model_validator
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
    MonthlyCardUsage,
    Transaction,
    TransactionReward,
    User,
    UserCard,
    UserEligibility,
)
from app.services.card_registration_service import register_virtual_card
from app.services.auth_service import (
    create_oauth_state,
    get_or_create_social_user,
    login_response,
    verify_oauth_state,
    verify_password,
)
from app.services.oauth_service import (
    authorization_url,
    fetch_oauth_profile,
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
    resolve_merchant_category,
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


app = FastAPI(
    title="PICKA Card Recommendation API",
    description="사용자의 보유 카드와 사용 상태를 반영해 결제 카드를 추천합니다.",
    version="1.1.0",
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


VERIFICATION_STATUSES = {
    "VERIFIED",
    "SELF_REPORTED",
    "INFERRED",
    "UNVERIFIED",
}
COMPARISON_OPERATORS = {"EQ", "GTE", "LTE", "CONTAINS"}


class UserEligibilityInput(BaseModel):
    eligibility_type: str = Field(min_length=1, max_length=100)
    eligibility_value: str = Field(min_length=1, max_length=255)
    verification_status: str = "SELF_REPORTED"
    verified_at: datetime | None = None
    expires_at: datetime | None = None

    @field_validator("eligibility_type", "verification_status")
    @classmethod
    def normalize_uppercase(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("verification_status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in VERIFICATION_STATUSES:
            raise ValueError("지원하지 않는 verification_status입니다.")
        return value


class UserEligibilityUpdateRequest(BaseModel):
    eligibilities: list[UserEligibilityInput]

    @model_validator(mode="after")
    def validate_unique_types(self):
        types = [item.eligibility_type for item in self.eligibilities]
        if len(types) != len(set(types)):
            raise ValueError("eligibility_type은 요청 안에서 중복될 수 없습니다.")
        return self


class CardEligibilityRuleInput(BaseModel):
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


class CardEligibilityRuleUpdateRequest(BaseModel):
    rules: list[CardEligibilityRuleInput]

    @model_validator(mode="after")
    def validate_unique_types(self):
        types = [item.eligibility_type for item in self.rules]
        if len(types) != len(set(types)):
            raise ValueError("eligibility_type은 요청 안에서 중복될 수 없습니다.")
        return self


class RecommendationRequest(BaseModel):
    user_id: int = Field(..., gt=0, examples=[2])
    merchant_name: str = Field(..., min_length=1, examples=["스타벅스 강남점"])
    payment_category: str | None = Field(default=None, examples=["카페/디저트"])
    payment_amount: int = Field(..., gt=0, examples=[12000])
    usage_month: str | None = Field(
        default=None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        examples=["2026-07"],
    )


class CardSelectionRequest(BaseModel):
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


class TransactionCreateRequest(BaseModel):
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


class TransactionHistoryListResponse(BaseModel):
    user_id: int
    card_id: int
    usage_month: str | None
    total_count: int
    limit: int
    offset: int
    transactions: list[TransactionHistoryItemResponse]


class LocalLoginRequest(BaseModel):
    email: str = Field(..., min_length=1, examples=["test@example.com"])
    password: str = Field(..., min_length=1, examples=["password123"])


class AuthUserResponse(BaseModel):
    user_id: int
    username: str | None
    email: str | None
    name: str | None
    login_provider: str


class LoginResponse(BaseModel):
    message: str
    access_token: str
    token_type: str
    user: AuthUserResponse


class OAuthAuthorizeResponse(BaseModel):
    authorization_url: str


class ManualCardRegistrationRequest(BaseModel):
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
    user = db.scalar(select(User).where(User.email == request.email))
    if (
        user is None
        or not user.is_active
        or not verify_password(request.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=401,
            detail="아이디 또는 비밀번호가 올바르지 않습니다.",
        )
    return login_response(user, "LOCAL")


@app.get(
    "/api/v1/auth/kakao/authorize",
    response_model=OAuthAuthorizeResponse,
    summary="카카오 로그인 URL 생성",
)
def kakao_authorize():
    state = create_oauth_state("KAKAO")
    return {
        "authorization_url": authorization_url("KAKAO", state),
    }


@app.get(
    "/api/v1/auth/naver/authorize",
    response_model=OAuthAuthorizeResponse,
    summary="네이버 로그인 URL 생성",
)
def naver_authorize():
    state = create_oauth_state("NAVER")
    return {
        "authorization_url": authorization_url("NAVER", state),
    }


async def social_login_callback(
    provider: str,
    code: str,
    state: str,
    db: Session,
) -> dict:
    verify_oauth_state(state, provider)
    profile = await fetch_oauth_profile(provider, code, state)
    try:
        user, account = get_or_create_social_user(
            db=db,
            provider=provider,
            provider_user_id=profile["provider_user_id"],
            email=profile.get("email"),
            name=profile.get("name"),
            profile_image_url=profile.get("profile_image_url"),
        )
        if not user.is_active:
            raise HTTPException(
                status_code=401,
                detail="비활성 사용자입니다.",
            )
        return login_response(
            user,
            provider,
            social_email=account.email,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="소셜 로그인 사용자 저장 중 오류가 발생했습니다.",
        ) from error


@app.get(
    "/api/v1/auth/kakao/callback",
    response_model=LoginResponse,
    summary="카카오 로그인 콜백",
)
async def kakao_callback(
    code: str,
    state: str,
    db: Annotated[Session, Depends(get_db)],
):
    return await social_login_callback("KAKAO", code, state, db)


@app.get(
    "/api/v1/auth/naver/callback",
    response_model=LoginResponse,
    summary="네이버 로그인 콜백",
)
async def naver_callback(
    code: str,
    state: str,
    db: Annotated[Session, Depends(get_db)],
):
    return await social_login_callback("NAVER", code, state, db)


@app.get("/")
def root():
    return {"message": "PICKA 카드 추천 API 서버가 실행 중입니다."}


@app.get("/health")
def health_check():
    return {"status": "ok"}


def _user_eligibility_payload(item: UserEligibility) -> dict:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "eligibility_type": item.eligibility_type,
        "eligibility_value": item.eligibility_value,
        "verification_status": item.verification_status,
        "verified_at": item.verified_at,
        "expires_at": item.expires_at,
    }


@app.get("/api/v1/users/{user_id}/eligibilities")
def get_user_eligibilities(
    user_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
):
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
):
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
                verification_status=item.verification_status,
            )
            db.add(row)
        else:
            row.eligibility_value = item.eligibility_value
            row.verification_status = item.verification_status
        row.verified_at = (
            None
            if item.verification_status == "UNVERIFIED"
            else item.verified_at or now
        )
        row.expires_at = item.expires_at

    db.execute(
        delete(CardRecommendationSnapshot).where(
            CardRecommendationSnapshot.user_id == user_id
        )
    )
    db.commit()
    return get_user_eligibilities(user_id, db)


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
):
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
    return get_card_eligibility_rules(card_id, db)


@app.get(
    "/api/v1/users/{user_id}/cards",
    summary="사용자 보유 카드 조회",
    description="사용자의 활성 보유 카드 목록과 해당 월의 카드 사용 상태를 조회합니다.",
)
def get_user_cards(
    user_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    usage_month: Annotated[
        str | None,
        Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    ] = None,
):
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
):
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
):
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
    usage_month: Annotated[
        str | None,
        Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    ] = None,
):
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
):
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
):
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
        payment_category = (
            request.payment_category
            or resolve_merchant_category(db, request.merchant_name)
        )
        payment_category = (
            normalize_payment_category(payment_category)
            or payment_category
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

        approval_number = f"PICKA-{uuid4().hex[:12].upper()}"
        approved_at = datetime.now(timezone.utc)
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

        monthly_usage = db.scalar(
            select(MonthlyCardUsage).where(
                MonthlyCardUsage.user_id == request.user_id,
                MonthlyCardUsage.card_id == request.card_id,
                MonthlyCardUsage.usage_month == usage_month,
            )
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
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    usage_month: Annotated[
        str | None,
        Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    ] = None,
):
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
    card_type: Annotated[
        str,
        Query(alias="type", pattern="^(credit|check)$"),
    ] = "credit",
    limit: Annotated[int, Query(ge=1, le=20)] = 3,
):
    try:
        return get_daily_card_recommendations(
            db,
            user_id=user_id,
            card_type=card_type,
            limit=limit,
        )
    except SpendingRecommendationUserNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get(
    "/api/v1/users/{user_id}/spending-report",
    response_model=MonthlySpendingReportResponse,
)
def get_monthly_spending_report(
    user_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    month: Annotated[
        str,
        Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    ],
):
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
):
    usage_month = request.usage_month or date.today().strftime("%Y-%m")

    try:
        user_card_states = build_user_card_states(
            db=db,
            user_id=request.user_id,
            usage_month=usage_month,
        )
        payment_category = request.payment_category or resolve_merchant_category(
            db, request.merchant_name
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
):
    usage_month = request.usage_month or date.today().strftime("%Y-%m")

    try:
        # 1. 해당 사용자의 보유 카드와 사용 상태를 DB에서 조회
        user_card_states = build_user_card_states(
            db=db,
            user_id=request.user_id,
            usage_month=usage_month,
        )

        # 2. 가맹점 업종 확인
        payment_category = request.payment_category or resolve_merchant_category(
            db,
            request.merchant_name,
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

        return {
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
