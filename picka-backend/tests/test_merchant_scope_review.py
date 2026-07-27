import unittest

from app.services.recommendation_service import requires_merchant_scope_review


class MerchantScopeReviewGateTest(unittest.TestCase):
    def test_merchant_scope_keywords_require_manual_review(self):
        keywords = [
            "일부 입점 매장",
            "일부 매장",
            "입점 매장 제외",
            "제휴 가맹점",
            "지정 가맹점",
            "카드사 등록 가맹점",
            "특정 가맹점",
        ]

        for keyword in keywords:
            with self.subTest(keyword=keyword):
                benefit = {"source_detail": f"혜택은 {keyword}에 적용됩니다."}
                self.assertTrue(requires_merchant_scope_review(benefit))

    def test_generic_exclusion_keywords_do_not_require_manual_review(self):
        keywords = [
            "제외",
            "제외됩니다",
            "제외 대상",
            "상품권",
            "선불카드",
            "충전",
        ]

        for keyword in keywords:
            with self.subTest(keyword=keyword):
                benefit = {"source_detail": f"{keyword} 관련 안내 문구"}
                self.assertFalse(requires_merchant_scope_review(benefit))


if __name__ == "__main__":
    unittest.main()
