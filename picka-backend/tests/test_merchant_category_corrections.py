import unittest

from app.models import MerchantAlias, Transaction
from app.services.spending_report_service import transaction_report_category
from app.services.user_state_adapter import resolve_category_from_aliases


class MerchantCategoryCorrectionTest(unittest.TestCase):
    def test_report_and_benefit_categories_can_differ(self):
        alias = MerchantAlias(
            id=1,
            alias="동네 문구점",
            canonical_merchant="동네 문구점",
            category="마트/쇼핑",
            report_category="생활",
            priority=200,
        )
        transaction = Transaction(
            merchant_name="동네 문구점",
            payment_category="마트/쇼핑",
        )

        self.assertEqual(
            resolve_category_from_aliases([alias], transaction.merchant_name),
            "마트/쇼핑",
        )
        self.assertEqual(
            transaction_report_category(transaction, [alias]),
            "생활비",
        )

    def test_report_category_falls_back_to_benefit_category(self):
        alias = MerchantAlias(
            id=1,
            alias="온누리약국",
            canonical_merchant="온누리약국",
            category="병원/약국",
            report_category=None,
            priority=200,
        )
        transaction = Transaction(
            merchant_name="온누리약국",
            payment_category="병원/약국",
        )

        self.assertEqual(
            transaction_report_category(transaction, [alias]),
            "생활비",
        )


if __name__ == "__main__":
    unittest.main()
