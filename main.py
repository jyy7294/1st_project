from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from recommendation_service import recommend_cards

from user_cards import get_user_card_by_id
from recommendation_service import (
    recommend_cards,
    calculate_card_benefit
)
from merchant_service import get_merchant_category


app = FastAPI(
    title="PICKA Card Recommendation API",
    description="결제정보를 바탕으로 사용자의 보유카드 중 가장 유리한 카드를 추천합니다.",
    version="1.0.0"
)


# React 프론트엔드 연결을 위한 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class RecommendationRequest(BaseModel):
    merchant_name: str = Field(
        ...,
        examples=["스타벅스"]
    )

    payment_category: str = Field(
        ...,
        examples=["카페/디저트"]
    )

    payment_amount: int = Field(
        ...,
        gt=0,
        examples=[12000]
    )

class CardSelectionRequest(BaseModel):
    merchant_name: str
    payment_category: str | None = None
    payment_amount: int = Field(..., gt=0)
    selected_card_id: int


@app.get("/")
def root():
    return {
        "message": "PICKA 카드 추천 API 서버가 실행 중입니다."
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.post("/api/v1/recommendations")
def create_recommendation(
    request: RecommendationRequest
):
    try:
        result = recommend_cards(
            merchant_name=request.merchant_name,
            payment_category=request.payment_category,
            payment_amount=request.payment_amount
        )

        if result["recommended_card"] is None:
            raise HTTPException(
                status_code=404,
                detail="추천 가능한 카드가 없습니다."
            )

        return result

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"추천 결과 생성 중 오류가 발생했습니다: {str(error)}"
        ) from error
    
@app.post("/api/v1/recommendations/select")
def select_recommended_card(
    request: CardSelectionRequest
):
    payment_category = (
        request.payment_category
        or get_merchant_category(
            request.merchant_name
        )
    )

    selected_card = get_user_card_by_id(
        request.selected_card_id
    )

    if selected_card is None:
        raise HTTPException(
            status_code=404,
            detail="선택한 카드는 사용자의 보유카드가 아닙니다."
        )

    recommendation_result = recommend_cards(
        merchant_name=request.merchant_name,
        payment_category=payment_category,
        payment_amount=request.payment_amount
    )

    recommended_card = recommendation_result[
        "recommended_card"
    ]

    selected_card_result = calculate_card_benefit(
        card=selected_card,
        payment_category=payment_category,
        payment_amount=request.payment_amount
    )

    is_recommended_card = (
        recommended_card is not None
        and recommended_card["card_id"]
        == request.selected_card_id
    )

    return {
        "status": "CARD_SELECTED",
        "message": "결제에 사용할 카드가 선택되었습니다.",
        "transaction": {
            "merchant_name": request.merchant_name,
            "category": payment_category,
            "amount": request.payment_amount
        },
        "selected_card": selected_card_result,
        "is_recommended_card": is_recommended_card
    }
    
