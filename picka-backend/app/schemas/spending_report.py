from pydantic import BaseModel


class DailySpendingPoint(BaseModel):
    day: int
    amount: int


class CardBenefitReport(BaseModel):
    cardId: int
    cardName: str
    issuer: str
    imageUrl: str | None
    benefit: int


class CategorySpendingReport(BaseModel):
    category: str
    amount: int
    ratio: float


class RewardSummary(BaseModel):
    type: str
    program: str
    amount: float
    unit: str


class MonthlySpendingReportResponse(BaseModel):
    month: str
    totalSpending: int
    previousMonth: str
    previousMonthSpending: int
    spendingDifference: int
    dailyCumulative: list[DailySpendingPoint]
    previousDailyCumulative: list[DailySpendingPoint]
    totalBenefit: int
    previousMonthBenefit: int
    benefitDifference: int
    rewards: list[RewardSummary]
    cardBenefits: list[CardBenefitReport]
    categories: list[CategorySpendingReport]
