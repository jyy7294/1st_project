from pydantic import BaseModel


class SpendingPatternCardResponse(BaseModel):
    id: int
    name: str
    issuer: str
    benefitName: str
    rate: float
    total: int
    fee: int
    url: str | None
    image_url: str | None
    benefitCategory: str | None
    monthlySpend: int
    recommendationMessage: str
    matchedMerchants: list[str]


class SpendingPatternMerchantResponse(BaseModel):
    name: str
    category: str | None
    amount: int


class SpendingPatternRecommendationResponse(BaseModel):
    analysisStartDate: str
    analysisEndDate: str
    updateCycle: str
    topCategory: str | None
    topCategorySpend: int
    topMerchants: list[SpendingPatternMerchantResponse]
    cards: list[SpendingPatternCardResponse]
