from __future__ import annotations

import json
import os
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


class LLMServiceError(Exception):
    """OpenAI API 호출 또는 응답 처리 실패."""


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise LLMServiceError(
            "OPENAI_API_KEY가 설정되지 않았습니다."
        )

    return OpenAI(api_key=api_key)


def judge_ambiguous_benefit(
    *,
    merchant_name: str,
    payment_category: str,
    payment_amount: int,
    benefit_name: str,
    benefit_rule: str,
    structured_conditions: dict[str, Any] | None = None,
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
        "structured_conditions": structured_conditions or {},
    }

    instructions = """
당신은 카드 혜택 약관의 적용 가능 여부를 판단하는 보조 시스템입니다.

반드시 다음 규칙을 지키세요.

1. 할인 금액을 계산하지 마세요.
2. 최종 추천 카드를 선택하지 마세요.
3. 제공된 가맹점 정보와 혜택 규칙만 사용하세요.
4. 약관에 없는 내용을 임의로 만들어내지 마세요.
5. 혜택 적용이 명확하면 applicable을 true 또는 false로 판단하세요.
6. 제공된 정보만으로 판단할 수 없으면 needs_human_review를 true로 반환하세요.
7. reason에는 판단 근거를 한국어로 짧고 명확하게 작성하세요.
8. confidence는 0부터 1 사이의 숫자로 반환하세요.
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
                            }
                        },
                        "required": [
                            "applicable",
                            "confidence",
                            "reason",
                            "needs_human_review"
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