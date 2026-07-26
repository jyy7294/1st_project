from typing import Any

from pydantic import BaseModel, ConfigDict


class RecommendationCardResponse(BaseModel):
    """추천 화면에 전달되는 카드별 계산 결과."""

    model_config = ConfigDict(extra="allow")

    card_id: int
    card_name: str
    expected_benefit: int
    eligible: bool
    is_conditional: bool = False
    caveat: str | None = None


class RecommendationResponse(BaseModel):
    """추천 API 응답. 디버그 등 기존 확장 필드는 그대로 허용합니다."""

    model_config = ConfigDict(extra="allow")

    transaction: dict[str, Any]
    recommendation_basis: str
    recommended_card: RecommendationCardResponse | None
    selectable_cards: list[RecommendationCardResponse]
    other_cards: list[RecommendationCardResponse]
    comparison: list[RecommendationCardResponse]
