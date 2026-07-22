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


class SpendingPatternRecommendationResponse(BaseModel):
    cards: list[SpendingPatternCardResponse]
