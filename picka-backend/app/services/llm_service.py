from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field


load_dotenv()


class BenefitJudgment(BaseModel):
    """LLM이 반환하는 카드 혜택 적용 여부 판단 결과."""

    applicable: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    needs_human_review: bool
    caveat: str = ""


class LLMServiceError(Exception):
    """OpenAI API 호출 또는 응답 처리 실패."""


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise LLMServiceError(
            "OPENAI_API_KEY가 설정되지 않았습니다."
        )

    return OpenAI(api_key=api_key)


@lru_cache(maxsize=512)
def _judge_ambiguous_benefit_cached(
    *,
    merchant_name: str,
    payment_category: str,
    payment_amount: int,
    benefit_name: str,
    benefit_rule: str,
    structured_conditions_json: str,
) -> BenefitJudgment:
    """
    카드 혜택 약관의 모호한 부분을 LLM으로 판단한다.

    이 함수는 할인 금액을 계산하지 않는다.
    혜택 적용 가능 여부만 판단한다.
    """

    model_name = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
    client = get_openai_client()

    judgment_input = {
        "merchant_name": merchant_name,
        "payment_category": payment_category,
        "payment_amount": payment_amount,
        "benefit_name": benefit_name,
        "benefit_rule": benefit_rule,
        "structured_conditions": json.loads(structured_conditions_json),
    }

    instructions = """
당신은 카드 혜택 약관의 적용 가능 여부를 판단하는 보조 시스템입니다.

반드시 다음 규칙을 지키세요.

1. 할인 금액을 계산하지 마세요.
2. 최종 추천 카드를 선택하지 마세요.
3. 제공된 가맹점 정보와 혜택 규칙만 사용하세요.
4. 약관에 없는 내용을 임의로 만들어내지 마세요.
5. 혜택 적용이 명확하면 applicable을 true 또는 false로 판단하세요.

6. 결제 품목 정보는 제공되지 않습니다.
   상품권, 선불카드, 기프트카드, 충전금 구매 등 품목에 따라 달라지는 제외 조건은
   일반적인 상품 또는 서비스 결제로 가정하여 applicable을 판단하세요.
   이 경우 needs_human_review는 false로 두고,
   품목 기반 제외 조건을 caveat에 짧게 작성하세요.

7. needs_human_review는 가맹점 자체가 혜택 대상 범위에 포함되는지
   제공된 정보만으로 판단할 수 없을 때만 true로 반환하세요.
   예: 일부 입점 매장 제외, 지정 가맹점만 적용, 특정 제휴 매장만 적용

8. needs_human_review가 true인 경우에도,
   일반적인 경우 혜택 적용 가능성이 높으면 applicable은 true로 반환하세요.

9. reason에는 applicable 판단 근거를 한국어로 짧고 명확하게 작성하세요.
10. caveat에는 사용자가 확인해야 할 예외 또는 주의사항만 작성하세요.
    주의사항이 없다면 빈 문자열을 반환하세요.
11. confidence는 0부터 1 사이의 숫자로 반환하세요.
"""

    try:
        response = client.responses.create(
            model=model_name,
            instructions=instructions,
            input=json.dumps(
                judgment_input,
                ensure_ascii=False,
            ),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "benefit_judgment",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "applicable": {
                                "type": "boolean"
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1
                            },
                            "reason": {
                                "type": "string"
                            },
                            "needs_human_review": {
                                "type": "boolean"
                            },
                            "caveat": {
    "type": "string"
}
                        },
                        "required": [
                            "applicable",
                            "confidence",
                            "reason",
                            "needs_human_review",
                            "caveat"
                        ],
                        "additionalProperties": False
                    }
                }
            },
        )

        result = json.loads(response.output_text)

        return BenefitJudgment.model_validate(result)

    except Exception as exc:
        raise LLMServiceError(
            "LLM 혜택 판단에 실패했습니다."
        ) from exc


def judge_ambiguous_benefit(
    *,
    merchant_name: str,
    payment_category: str,
    payment_amount: int,
    benefit_name: str,
    benefit_rule: str,
    structured_conditions: dict[str, Any] | None = None,
) -> BenefitJudgment:
    """동일한 거래·약관 판단은 메모리 캐시를 재사용합니다."""
    return _judge_ambiguous_benefit_cached(
        merchant_name=merchant_name,
        payment_category=payment_category,
        payment_amount=payment_amount,
        benefit_name=benefit_name,
        benefit_rule=benefit_rule,
        structured_conditions_json=json.dumps(
            structured_conditions or {},
            ensure_ascii=False,
            sort_keys=True,
        ),
    )
