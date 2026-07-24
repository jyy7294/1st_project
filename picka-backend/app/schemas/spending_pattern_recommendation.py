from pydantic import BaseModel


class SpendingPatternCardResponse(BaseModel):
    id: int
    name: str
    issuer: str
    benefitName: str
    rate: float
    benefitValue: float
    benefitUnit: str | None
    expectedBenefitAmount: int
    total: int
    fee: int
    url: str | None
    image_url: str | None
    benefitCategory: str | None
    monthlySpend: int
    recommendationMessage: str
    matchedMerchants: list[str]
    benefits: list["SpendingPatternBenefitResponse"]


class SpendingPatternBenefitResponse(BaseModel):
    id: int
    name: str | None
    category: str | None
    benefitType: str | None
    value: float | None
    unit: str | None
    perTransactionLimit: int | None
    monthlyLimit: int | None
    requiredSpending: int | None
    conditionText: str | None
    summary: str | None
    detail: str | None


class SpendingPatternMerchantResponse(BaseModel):
    name: str
    category: str | None
    amount: int


class EligibilityExcludedCardResponse(BaseModel):
    cardId: int
    cardName: str
    status: str
    eligibilityType: str
    reason: str


class EligibilityConfirmationResponse(BaseModel):
    eligibilityType: str
    reason: str
    cardIds: list[int]


class BenefitEligibilityConfirmationResponse(BaseModel):
    eligibilityType: str
    reason: str
    cardBenefitIds: list[int]


class SpendingPatternRecommendationResponse(BaseModel):
    analysisStartDate: str
    analysisEndDate: str
    updateCycle: str
    topCategory: str | None
    topCategorySpend: int
    topMerchants: list[SpendingPatternMerchantResponse]
    cards: list[SpendingPatternCardResponse]
    excludedCards: list[EligibilityExcludedCardResponse]
    confirmationRequired: list[EligibilityConfirmationResponse]
    excludedBenefitCount: int
    benefitConfirmationRequired: list[BenefitEligibilityConfirmationResponse]
    cached: bool
    generatedAt: str
    policyVersion: str
