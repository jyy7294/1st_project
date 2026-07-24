from __future__ import annotations

from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import (
    BenefitUsage,
    Card,
    CardBenefit,
    MerchantAlias,
    MonthlyCardUsage,
    Transaction,
    User,
    UserCard,
)
from app.services.merchant_service import get_merchant_category


class UserNotFoundError(LookupError):
    pass


class NoActiveUserCardsError(LookupError):
    pass


def _extra_value(benefit: CardBenefit, *names: str) -> Any:
    for source in (benefit.additional_conditions, benefit.raw_data):
        if not isinstance(source, dict):
            continue
        for name in names:
            value = source.get(name)
            if value is not None:
                return value
    return None


def _tier_to_state(tier: object) -> dict[str, Any]:
    return {
        "tier_order": tier.tier_order,
        "required_spending": tier.required_spending,
        "monthly_limit": tier.monthly_limit,
        "benefit_value": tier.benefit_value,
        "benefit_unit": tier.benefit_unit,
        "extraction_method": tier.extraction_method,
        "review_required": tier.review_required,
        "raw_data": tier.raw_data,
    }


def _benefit_to_state(benefit: CardBenefit) -> dict[str, Any]:
    return {
        "card_benefit_id": benefit.id,
        "source_benefit_id": benefit.source_benefit_id,
        "benefit_name": benefit.benefit_name,
        "category": benefit.category,
        "category_list": _extra_value(benefit, "category_list", "카테고리목록"),
        "merchant_list": _extra_value(benefit, "merchant_list", "가맹점목록"),
        "benefit_type": benefit.benefit_type,
        "benefit_unit": benefit.benefit_unit,
        "benefit_value": benefit.benefit_value,
        "required_spending": benefit.required_spending,
        "minimum_payment": benefit.minimum_payment,
        "per_transaction_limit": benefit.per_transaction_limit,
        "monthly_spending_limit": benefit.monthly_spending_limit,
        "monthly_benefit_limit": benefit.monthly_benefit_limit,
        "daily_count_limit": benefit.daily_count_limit,
        "monthly_count_limit": benefit.monthly_count_limit,
        "annual_limit": benefit.annual_limit,
        "limit_status": benefit.limit_status,
        "condition_text": benefit.condition_text,
        "exception_text": benefit.exception_text,
        "raw_text": benefit.raw_text,
        "source_summary": benefit.source_summary,
        "source_detail": benefit.source_detail,
        "additional_conditions": benefit.additional_conditions,
        "raw_data": benefit.raw_data,
        "scoring_grade": _extra_value(
            benefit, "scoring_grade", "스코어링등급"
        ),
        "option_group": _extra_value(benefit, "option_group", "옵션그룹"),
        "is_option": _extra_value(benefit, "is_option", "옵션형"),
        "is_option_header": _extra_value(
            benefit, "is_option_header", "옵션헤더"
        ),
        "benefit_tiers": [_tier_to_state(tier) for tier in benefit.tiers],
    }


def build_user_card_states(
    db: Session,
    user_id: int,
    usage_month: str,
) -> list[dict[str, Any]]:
    """DB 사용자 상태를 기존 추천 엔진의 카드 dict 형식으로 변환합니다."""

    if db.get(User, user_id) is None:
        raise UserNotFoundError(f"사용자 ID {user_id}를 찾을 수 없습니다.")

    user_cards = list(
        db.scalars(
            select(UserCard)
            .where(
                UserCard.user_id == user_id,
                UserCard.is_active.is_(True),
            )
            .options(
                joinedload(UserCard.card)
                .selectinload(Card.benefits)
                .selectinload(CardBenefit.tiers)
            )
            .order_by(UserCard.id)
        )
    )

    if not user_cards:
        raise NoActiveUserCardsError("활성 보유 카드가 없습니다.")

    card_ids = [user_card.card_id for user_card in user_cards]
    monthly_results = db.execute(
        select(
            MonthlyCardUsage,
            func.count(Transaction.id),
            func.coalesce(
                func.sum(Transaction.saved_amount).filter(
                    Transaction.status == "APPROVED"
                ),
                0,
            ),
        )
        .outerjoin(
            Transaction,
            and_(
                Transaction.user_id == MonthlyCardUsage.user_id,
                Transaction.card_id == MonthlyCardUsage.card_id,
                Transaction.usage_month == MonthlyCardUsage.usage_month,
            ),
        )
        .where(
            MonthlyCardUsage.user_id == user_id,
            MonthlyCardUsage.card_id.in_(card_ids),
            MonthlyCardUsage.usage_month == usage_month,
        )
        .group_by(MonthlyCardUsage.id)
    ).all()
    monthly_rows = [row[0] for row in monthly_results]
    monthly_by_card = {row.card_id: row for row in monthly_rows}
    transaction_counts = {
        monthly.card_id: count
        for monthly, count, _ in monthly_results
    }
    confirmed_benefits_by_card = {
        monthly.card_id: int(amount or 0)
        for monthly, _, amount in monthly_results
    }

    usage_rows = db.scalars(
        select(BenefitUsage).where(
            BenefitUsage.user_id == user_id,
            BenefitUsage.card_id.in_(card_ids),
            BenefitUsage.usage_month == usage_month,
        )
    ).all()
    usage_by_benefit_id = {row.card_benefit_id: row for row in usage_rows}

    states: list[dict[str, Any]] = []
    for user_card in user_cards:
        card = user_card.card
        monthly = monthly_by_card.get(card.id)
        benefit_usage: dict[str, dict[str, int]] = {}

        for benefit in card.benefits:
            usage = usage_by_benefit_id.get(benefit.id)
            if usage is None or benefit.source_benefit_id is None:
                continue
            benefit_usage[str(benefit.source_benefit_id)] = {
                "monthly_used_amount": usage.monthly_used_amount,
                "monthly_used_count": usage.monthly_used_count,
                "daily_used_count": usage.daily_used_count,
            }

        # 월 집계 캐시가 아니라 승인 거래의 실제 saved_amount를 단일 기준으로 사용한다.
        card_used = confirmed_benefits_by_card.get(card.id, 0)
        states.append(
            {
                "user_id": user_id,
                "user_card_id": user_card.id,
                "card_id": card.id,
                "source_card_id": card.source_card_id,
                "card_name": card.card_name,
                "card_company": card.issuer,
                "issuer": card.issuer,
                "card_type": card.card_type,
                "card_image": card.image_url,
                "image_url": card.image_url,
                "nickname": user_card.nickname,
                "card_number_last4": user_card.card_number_last4,
                "masked_card_number": (
                    f"**** **** **** {user_card.card_number_last4}"
                    if user_card.card_number_last4
                    else None
                ),
                "registration_method": user_card.registration_method,
                "registered_at": user_card.registered_at,
                "required_spending": card.previous_spending or 0,
                "previous_month_spending": (
                    monthly.previous_month_spending if monthly else 0
                ),
                "current_month_spending": (
                    monthly.current_month_spending if monthly else 0
                ),
                "monthly_transaction_count": transaction_counts.get(
                    card.id,
                    0,
                ),
                "monthly_total_limit": card.monthly_total_limit,
                "card_monthly_benefit_used": card_used,
                "monthly_benefit_used": card_used,
                "selected_option_group": user_card.selected_option_group,
                "selected_option_benefit_id": (
                    user_card.selected_option_benefit_id
                ),
                "benefit_usage_this_month": benefit_usage,
                "benefits": [
                    _benefit_to_state(benefit) for benefit in card.benefits
                ],
            }
        )

    return states


def resolve_category_from_aliases(
    aliases: list[MerchantAlias],
    merchant_name: str,
) -> str | None:
    alias = resolve_merchant_alias(aliases, merchant_name)
    return alias.category if alias is not None else None


def resolve_merchant_alias(
    aliases: list[MerchantAlias],
    merchant_name: str,
) -> MerchantAlias | None:
    normalized_name = "".join(merchant_name.lower().split())
    matches = []
    for alias in aliases:
        normalized_alias = "".join(alias.alias.lower().split())
        if normalized_alias and normalized_alias in normalized_name:
            matches.append((alias, normalized_alias))
    if not matches:
        return None
    alias, _ = min(
        matches,
        key=lambda item: (
            -len(item[1]),
            -(item[0].priority or 0),
            item[0].id,
        ),
    )
    return alias


def resolve_merchant_category(db: Session, merchant_name: str) -> str:
    aliases = list(db.scalars(select(MerchantAlias)).all())
    alias_category = resolve_category_from_aliases(aliases, merchant_name)
    if alias_category is not None:
        return alias_category

    return get_merchant_category(merchant_name)


def resolve_payment_category(
    db: Session,
    *,
    merchant_name: str,
    supplied_category: str | None = None,
) -> str:
    """등록된 가맹점 alias를 프론트 입력이나 일반 분류보다 우선한다."""
    aliases = list(db.scalars(select(MerchantAlias)).all())
    alias_category = resolve_category_from_aliases(aliases, merchant_name)
    if alias_category is not None:
        return alias_category
    if supplied_category:
        from app.services.category_normalization import normalize_payment_category

        return normalize_payment_category(supplied_category) or supplied_category
    return get_merchant_category(merchant_name)
