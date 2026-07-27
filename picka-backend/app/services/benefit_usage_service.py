from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    BenefitDailyUsage,
    BenefitUsage,
    CardBenefit,
    Transaction,
    TransactionBenefitApplication,
)


def lock_benefit_usage(
    db: Session,
    *,
    user_id: int,
    card_id: int,
    card_benefit_id: int,
    usage_month: str,
    usage_date: date,
) -> tuple[BenefitUsage, BenefitDailyUsage]:
    monthly = db.scalar(
        select(BenefitUsage)
        .where(
            BenefitUsage.user_id == user_id,
            BenefitUsage.card_benefit_id == card_benefit_id,
            BenefitUsage.usage_month == usage_month,
        )
        .with_for_update()
    )
    if monthly is None:
        monthly = BenefitUsage(
            user_id=user_id,
            card_id=card_id,
            card_benefit_id=card_benefit_id,
            usage_month=usage_month,
            monthly_used_amount=0,
            monthly_used_count=0,
        )
        db.add(monthly)
        db.flush()

    daily = db.scalar(
        select(BenefitDailyUsage)
        .where(
            BenefitDailyUsage.user_id == user_id,
            BenefitDailyUsage.card_benefit_id == card_benefit_id,
            BenefitDailyUsage.usage_date == usage_date,
        )
        .with_for_update()
    )
    if daily is None:
        daily = BenefitDailyUsage(
            user_id=user_id,
            card_id=card_id,
            card_benefit_id=card_benefit_id,
            usage_date=usage_date,
            daily_used_amount=0,
            daily_used_count=0,
        )
        db.add(daily)
        db.flush()

    return monthly, daily


def count_limit_is_available(
    benefit: CardBenefit,
    monthly: BenefitUsage,
    daily: BenefitDailyUsage,
) -> bool:
    if (
        benefit.monthly_count_limit is not None
        and monthly.monthly_used_count >= benefit.monthly_count_limit
    ):
        return False
    if (
        benefit.daily_count_limit is not None
        and daily.daily_used_count >= benefit.daily_count_limit
    ):
        return False
    return True


def record_applied_benefit(
    db: Session,
    *,
    transaction: Transaction,
    benefit: CardBenefit,
    monthly: BenefitUsage,
    daily: BenefitDailyUsage,
    applied_amount: int,
    applied_at: datetime,
) -> TransactionBenefitApplication:
    application = TransactionBenefitApplication(
        transaction_id=transaction.id,
        card_benefit_id=benefit.id,
        applied_amount=applied_amount,
        applied_count=1,
        status="APPLIED",
        applied_at=applied_at,
    )
    db.add(application)
    monthly.monthly_used_amount += applied_amount
    monthly.monthly_used_count += 1
    daily.daily_used_amount += applied_amount
    daily.daily_used_count += 1
    return application

