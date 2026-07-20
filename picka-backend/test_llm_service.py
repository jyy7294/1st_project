from app.services.llm_service import judge_ambiguous_benefit


result = judge_ambiguous_benefit(
    merchant_name="스타벅스 현대백화점 판교점",
    payment_category="카페·디저트",
    payment_amount=12000,
    benefit_name="스타벅스 55% 할인",
    benefit_rule=(
        "스타벅스 결제 시 55% 할인. "
        "단, 백화점 및 대형마트 입점 매장, "
        "상품권 구매, 선불카드 충전은 제외."
    ),
    structured_conditions={
        "discount_rate": 55,
        "required_previous_spending": 400000,
    },
)

print("전체 결과:", result)
print("적용 가능:", result.applicable)
print("확신도:", result.confidence)
print("판단 이유:", result.reason)
print("추가 검토 필요:", result.needs_human_review)

print("\n--- 일반 매장 테스트 ---")

result2 = judge_ambiguous_benefit(
    merchant_name="스타벅스 강남역점",
    payment_category="카페·디저트",
    payment_amount=12000,
    benefit_name="스타벅스 55% 할인",
    benefit_rule=(
        "스타벅스 결제 시 55% 할인. "
        "단, 백화점 및 대형마트 입점 매장, "
        "상품권 구매, 선불카드 충전은 제외."
    ),
    structured_conditions={
        "discount_rate": 55,
        "required_previous_spending": 400000,
    },
)

print("전체 결과:", result2)
print("적용 가능:", result2.applicable)
print("확신도:", result2.confidence)
print("판단 이유:", result2.reason)
print("추가 검토 필요:", result2.needs_human_review)

print("\n--- 정보 부족 테스트 ---")

result3 = judge_ambiguous_benefit(
    merchant_name="에이치커피",
    payment_category="카페·디저트",
    payment_amount=12000,
    benefit_name="제휴 카페 할인",
    benefit_rule="카드사 지정 제휴 가맹점에 한해 할인",
)

print("전체 결과:", result3)
print("적용 가능:", result3.applicable)
print("확신도:", result3.confidence)
print("판단 이유:", result3.reason)
print("추가 검토 필요:", result3.needs_human_review)