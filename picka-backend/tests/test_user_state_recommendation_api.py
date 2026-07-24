import unittest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.config import settings
from app.main import app
from app.models import (
    AuthRefreshToken,
    BenefitUsage,
    Card,
    CardBenefit,
    MerchantAlias,
    MonthlyCardUsage,
    RecommendationAuditLog,
    Transaction,
    User,
    UserCard,
)
from app.services.user_state_adapter import build_user_card_states
from app.services.auth_service import create_access_token, hash_password


class UserStateRecommendationApiTest(unittest.TestCase):
    def setUp(self):
        self.original_debug = settings.recommendation_debug
        self.original_auth_settings = {
            "jwt_secret_key": settings.jwt_secret_key,
        }
        settings.recommendation_debug = False
        settings.jwt_secret_key = "test-jwt-secret-key-at-least-32-bytes"
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self._seed()

        def override_get_db():
            with self.Session() as db:
                yield db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)
        with self.Session() as db:
            token = create_access_token(db.get(User, 2))
        self.client.headers.update({"Authorization": f"Bearer {token}"})

    def tearDown(self):
        settings.recommendation_debug = self.original_debug
        for name, value in self.original_auth_settings.items():
            setattr(settings, name, value)
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def _seed(self):
        with self.Session() as db:
            db.add(User(id=2, email="test@example.com", name="테스트유저"))
            cards = [
                Card(
                    id=index,
                    source_card_id=index,
                    card_name=f"테스트카드 {index}",
                    issuer="테스트카드사",
                    previous_spending=300_000,
                )
                for index in range(1, 4)
            ]
            db.add_all(cards)
            db.flush()
            benefits = [
                CardBenefit(
                    card_id=index,
                    source_benefit_id=f"{index}-01",
                    benefit_name="카페 10% 할인",
                    category="카페",
                    benefit_type="할인",
                    benefit_unit="%",
                    benefit_value=10,
                    monthly_benefit_limit=5_000,
                    additional_conditions={"scoring_grade": "A_확정계산"},
                )
                for index in range(1, 4)
            ]
            db.add_all(benefits)
            db.flush()
            db.add_all(
                [
                    UserCard(user_id=2, card_id=index, is_active=True)
                    for index in range(1, 4)
                ]
            )
            db.add_all(
                [
                    MonthlyCardUsage(
                        user_id=2,
                        card_id=index,
                        usage_month="2026-07",
                        previous_month_spending=600_000,
                        current_month_spending=150_000,
                        card_monthly_benefit_used=3_000,
                    )
                    for index in range(1, 4)
                ]
            )
            db.add(
                BenefitUsage(
                    user_id=2,
                    card_id=1,
                    card_benefit_id=benefits[0].id,
                    usage_month="2026-07",
                    monthly_used_amount=4_500,
                    monthly_used_count=2,
                    daily_used_count=1,
                )
            )
            db.add(
                MerchantAlias(
                    alias="스타벅스",
                    canonical_merchant="스타벅스",
                    category="카페",
                    priority=100,
                )
            )
            db.commit()

    def _request(self, **overrides):
        body = {
            "user_id": 2,
            "merchant_name": "스타벅스 강남점",
            "payment_amount": 10_000,
            "usage_month": "2026-07",
        }
        body.update(overrides)
        return self.client.post("/api/v1/recommendations", json=body)

    def _select_request(self, **overrides):
        body = {
            "user_id": 2,
            "merchant_name": "스타벅스 강남점",
            "payment_amount": 10_000,
            "selected_card_id": 2,
            "usage_month": "2026-07",
        }
        body.update(overrides)
        return self.client.post(
            "/api/v1/recommendations/select",
            json=body,
        )

    def _cards_request(self, user_id=2, usage_month="2026-07"):
        return self.client.get(
            f"/api/v1/users/{user_id}/cards",
            params={"usage_month": usage_month},
        )

    def _card_detail_request(
        self,
        user_id=2,
        card_id=1,
        usage_month="2026-07",
    ):
        return self.client.get(
            f"/api/v1/users/{user_id}/cards/{card_id}",
            params={"usage_month": usage_month},
        )

    def _transaction_request(self, **overrides):
        body = {
            "user_id": 2,
            "card_id": 2,
            "merchant_name": "스타벅스 강남점",
            "payment_amount": 10_000,
            "payment_category": "카페",
            "usage_month": "2026-07",
        }
        body.update(overrides)
        return self.client.post("/api/v1/transactions", json=body)

    def _prepare_virtual_card(self):
        with self.Session() as db:
            card = Card(
                id=4,
                source_card_id=4,
                card_name="신규 가상카드",
                issuer="가상카드사",
                previous_spending=0,
            )
            db.add(card)
            db.flush()
            db.add(
                CardBenefit(
                    card_id=4,
                    source_benefit_id="4-01",
                    benefit_name="카페 15% 할인",
                    category="카페",
                    benefit_type="할인",
                    benefit_unit="%",
                    benefit_value=15,
                    monthly_benefit_limit=10_000,
                    additional_conditions={
                        "scoring_grade": "A_확정계산"
                    },
                )
            )
            db.commit()

    def _registration_request(self, method="manual", **overrides):
        body = {
            "card_number": "1234-5678-9012-3456",
            "expiry_month": 12,
            "expiry_year": 2029,
            "cvc": "123",
            "card_password_first2": "45",
        }
        body.update(overrides)
        return self.client.post(
            f"/api/v1/users/2/cards/{method}",
            json=body,
        )

    def test_seed_user_returns_three_owned_cards_and_month(self):
        with self.Session() as db:
            db.add(RecommendationAuditLog(
                user_id=2,
                request_kind="EXPIRED_TEST",
                input_payload={},
                calculation_payload={},
                created_at=datetime.now(timezone.utc) - timedelta(days=91),
            ))
            db.commit()

        response = self._request()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["owned_card_count"], 3)
        self.assertEqual(body["usage_month"], "2026-07")
        self.assertEqual(body["user_state_source"], "database")

        with self.Session() as db:
            audit = db.scalar(select(RecommendationAuditLog))
            self.assertIsNotNone(audit)
            self.assertEqual(db.query(RecommendationAuditLog).count(), 1)
            self.assertEqual(audit.user_id, 2)
            self.assertEqual(audit.request_kind, "PAYMENT_CARD_RECOMMENDATION")
            self.assertEqual(audit.input_payload["payment_amount"], 10_000)
            self.assertEqual(
                audit.calculation_payload["recommendation_basis"],
                body["recommendation_basis"],
            )

    def test_card_selection_saves_original_calculation_audit(self):
        response = self._select_request()
        self.assertEqual(response.status_code, 200)

        with self.Session() as db:
            audit = db.scalar(select(RecommendationAuditLog))
            self.assertEqual(audit.request_kind, "PAYMENT_CARD_SELECTION")
            self.assertEqual(audit.selected_card_id, 2)
            self.assertIn("original_recommendation", audit.calculation_payload)

    def test_get_user_cards_returns_active_database_cards(self):
        response = self._cards_request()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["user_id"], 2)
        self.assertEqual(body["usage_month"], "2026-07")
        self.assertEqual(body["user_state_source"], "database")
        self.assertEqual(body["total_count"], 3)
        self.assertEqual(
            [card["card_id"] for card in body["cards"]],
            [1, 2, 3],
        )

    def test_get_user_cards_other_user_id_returns_403(self):
        response = self._cards_request(user_id=999)
        self.assertEqual(response.status_code, 403)

    def test_get_user_cards_validates_path_and_month(self):
        self.assertEqual(self._cards_request(user_id=0).status_code, 422)
        self.assertEqual(
            self._cards_request(usage_month="2026-13").status_code,
            422,
        )

    def test_get_user_card_detail_returns_database_card(self):
        response = self._card_detail_request(card_id=1)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["user_id"], 2)
        self.assertEqual(body["usage_month"], "2026-07")
        self.assertEqual(body["user_state_source"], "database")
        self.assertEqual(body["card"]["card_id"], 1)
        self.assertTrue(body["card"]["benefits"])

    def test_get_user_card_detail_rejects_unowned_card(self):
        response = self._card_detail_request(card_id=999)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["detail"],
            "사용자의 보유 카드가 아닙니다.",
        )

    def test_get_user_card_detail_validates_parameters(self):
        self.assertEqual(
            self._card_detail_request(user_id=0).status_code,
            422,
        )

    def test_create_transaction_returns_virtual_approval(self):
        response = self._transaction_request()
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["status"], "APPROVED")
        self.assertIsInstance(body["transaction_id"], int)
        self.assertTrue(body["approval_number"].startswith("PICKA-"))
        self.assertNotIn("payment_token", str(body))
        self.assertEqual(body["card"]["card_id"], 2)
        self.assertEqual(body["card"]["card_name"], "테스트카드 2")
        self.assertEqual(
            body["payment"],
            {
                "original_payment_amount": 10_000,
                "saved_amount": 1_000,
                "final_approved_amount": 9_000,
            },
        )
        self.assertTrue(body["applied_benefit"]["applied"])
        with self.Session() as db:
            transaction = db.get(Transaction, body["transaction_id"])
            self.assertIsNotNone(transaction)
            self.assertEqual(transaction.original_payment_amount, 10_000)
            self.assertEqual(transaction.saved_amount, 1_000)
            self.assertEqual(transaction.final_approved_amount, 9_000)
            monthly = db.scalar(
                select(MonthlyCardUsage).where(
                    MonthlyCardUsage.user_id == 2,
                    MonthlyCardUsage.card_id == 2,
                    MonthlyCardUsage.usage_month == "2026-07",
                )
            )
            self.assertEqual(monthly.current_month_spending, 160_000)
            self.assertEqual(monthly.card_monthly_benefit_used, 4_000)

            # 집계 캐시에는 기존 3,000원이 들어 있어도 API 계산 기준은
            # 승인 거래의 실제 saved_amount(1,000원)여야 한다.
            states = build_user_card_states(db, 2, "2026-07")
            card_two = next(card for card in states if card["card_id"] == 2)
            self.assertEqual(card_two["card_monthly_benefit_used"], 1_000)

        report = self.client.get(
            "/api/v1/users/2/spending-report",
            params={"month": "2026-07"},
        ).json()
        self.assertEqual(report["totalBenefit"], 1_000)
        report_card = next(
            card for card in report["cardBenefits"] if card["cardId"] == 2
        )
        self.assertEqual(report_card["benefit"], 1_000)

    def test_payment_clamps_discount_to_card_monthly_total_limit(self):
        with self.Session() as db:
            card = db.get(Card, 2)
            card.monthly_total_limit = 1_800
            db.commit()

        first = self._transaction_request().json()
        second = self._transaction_request().json()

        self.assertEqual(first["payment"]["saved_amount"], 1_000)
        self.assertEqual(second["payment"]["saved_amount"], 800)
        with self.Session() as db:
            saved_total = db.scalar(
                select(func.sum(Transaction.saved_amount)).where(
                    Transaction.user_id == 2,
                    Transaction.card_id == 2,
                    Transaction.usage_month == "2026-07",
                    Transaction.status == "APPROVED",
                )
            )
            self.assertEqual(saved_total, 1_800)

    def test_create_transaction_rejects_unowned_card(self):
        response = self._transaction_request(card_id=999)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["detail"],
            "사용자의 보유 카드가 아닙니다.",
        )

    def test_create_transaction_without_benefit_still_approves(self):
        response = self._transaction_request(
            merchant_name="NO_ALIAS_HOSPITAL",
            payment_category="MEDICAL",
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["payment"]["saved_amount"], 0)
        self.assertEqual(body["payment"]["final_approved_amount"], 10_000)
        self.assertFalse(body["applied_benefit"]["applied"])
        self.assertIsNone(body["applied_benefit"]["benefit_name"])
        with self.Session() as db:
            self.assertEqual(
                db.scalar(select(func.count()).select_from(Transaction)),
                1,
            )
            transaction = db.scalar(select(Transaction))
            self.assertEqual(transaction.payment_category, "병원/약국")

    def test_create_transaction_normalizes_english_payment_category(self):
        response = self._transaction_request(
            merchant_name="NO_ALIAS_MART",
            payment_category="MART",
        )

        self.assertEqual(response.status_code, 201)
        with self.Session() as db:
            transaction = db.scalar(select(Transaction))
            self.assertEqual(transaction.payment_category, "마트/쇼핑")

    def test_create_transaction_validates_request(self):
        self.assertEqual(
            self._transaction_request(payment_amount=0).status_code,
            400,
        )

    def test_merchant_alias_overrides_supplied_category(self):
        response = self._transaction_request(payment_category="MART")
        self.assertEqual(response.status_code, 201)
        with self.Session() as db:
            transaction = db.scalar(select(Transaction))
            self.assertEqual(transaction.payment_category, "카페")

    def test_monthly_spending_report_aggregates_categories_and_benefits(self):
        self._transaction_request(
            merchant_name="NO_ALIAS_RESTAURANT",
            payment_category="RESTAURANT",
            payment_amount=20_000,
            usage_month="2026-07",
        )
        self._transaction_request(
            merchant_name="NO_ALIAS_TELECOM",
            payment_category="TELECOM",
            payment_amount=30_000,
            usage_month="2026-07",
        )
        self._transaction_request(
            merchant_name="NO_ALIAS_FUEL",
            payment_category="FUEL",
            payment_amount=40_000,
            usage_month="2026-07",
        )
        self._transaction_request(
            merchant_name="NO_ALIAS_TRANSIT",
            payment_category="TRANSIT",
            payment_amount=10_000,
            usage_month="2026-06",
        )

        response = self.client.get(
            "/api/v1/users/2/spending-report",
            params={"month": "2026-07"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["totalSpending"], 90_000)
        self.assertEqual(body["previousMonthSpending"], 10_000)
        self.assertEqual(body["spendingDifference"], 80_000)
        categories = {
            item["category"]: item["amount"] for item in body["categories"]
        }
        self.assertEqual(categories["식비"], 20_000)
        self.assertEqual(categories["생활비"], 30_000)
        self.assertEqual(categories["교통"], 0)
        self.assertEqual(categories["주유"], 40_000)
        self.assertEqual(len(body["categories"]), 7)

    def test_card_transaction_history_is_filtered_and_newest_first(self):
        first = self._transaction_request(
            merchant_name="첫 번째 가맹점",
            usage_month="2026-06",
        ).json()
        second = self._transaction_request(
            merchant_name="두 번째 가맹점",
            usage_month="2026-07",
        ).json()

        response = self.client.get(
            "/api/v1/users/2/cards/2/transactions",
            params={"limit": 10, "offset": 0},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total_count"], 2)
        self.assertIsNone(body["usage_month"])
        self.assertEqual(body["limit"], 10)
        self.assertEqual(
            [item["transaction_id"] for item in body["transactions"]],
            [second["transaction_id"], first["transaction_id"]],
        )

        filtered = self.client.get(
            "/api/v1/users/2/cards/2/transactions",
            params={"usage_month": "2026-06"},
        ).json()
        self.assertEqual(filtered["total_count"], 1)
        self.assertEqual(filtered["usage_month"], "2026-06")
        self.assertEqual(
            filtered["transactions"][0]["transaction_id"],
            first["transaction_id"],
        )

    def test_card_transaction_history_paginates_with_total_count(self):
        created_ids = [
            self._transaction_request(
                merchant_name=f"페이지 가맹점 {index}"
            ).json()["transaction_id"]
            for index in range(3)
        ]
        response = self.client.get(
            "/api/v1/users/2/cards/2/transactions",
            params={"limit": 1, "offset": 1},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total_count"], 3)
        self.assertEqual(body["limit"], 1)
        self.assertEqual(body["offset"], 1)
        self.assertEqual(len(body["transactions"]), 1)
        self.assertEqual(
            body["transactions"][0]["transaction_id"],
            created_ids[1],
        )

    def test_card_transaction_history_empty_result_returns_200(self):
        response = self.client.get(
            "/api/v1/users/2/cards/2/transactions",
            params={"usage_month": "2025-01"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["usage_month"], "2025-01")
        self.assertEqual(body["total_count"], 0)
        self.assertEqual(body["limit"], 20)
        self.assertEqual(body["offset"], 0)
        self.assertEqual(body["transactions"], [])

    def test_card_transaction_history_rejects_unowned_card(self):
        response = self.client.get(
            "/api/v1/users/2/cards/999/transactions"
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["detail"],
            "사용자의 보유 카드가 아닙니다.",
        )

    def test_card_transaction_history_does_not_expose_other_user_data(self):
        self._transaction_request()
        with self.Session() as db:
            db.add(
                User(
                    id=3,
                    email="other@example.com",
                    name="다른 사용자",
                )
            )
            db.add(UserCard(user_id=3, card_id=1, is_active=True))
            db.commit()

        response = self.client.get(
            "/api/v1/users/3/cards/2/transactions"
        )
        self.assertEqual(response.status_code, 403)

    def test_card_transaction_history_validates_query(self):
        for params in (
            {"limit": 0},
            {"limit": 101},
            {"offset": -1},
            {"usage_month": "2026-13"},
        ):
            with self.subTest(params=params):
                response = self.client.get(
                    "/api/v1/users/2/cards/2/transactions",
                    params=params,
                )
                self.assertEqual(response.status_code, 422)

    def test_card_detail_includes_five_newest_transactions(self):
        created_ids = []
        for index in range(6):
            created_ids.append(
                self._transaction_request(
                    merchant_name=f"가맹점 {index}"
                ).json()["transaction_id"]
            )

        response = self._card_detail_request(card_id=2)
        self.assertEqual(response.status_code, 200)
        recent = response.json()["recent_transactions"]
        self.assertEqual(len(recent), 5)
        self.assertEqual(
            [item["transaction_id"] for item in recent],
            list(reversed(created_ids))[:5],
        )
        self.assertEqual(
            self._transaction_request(merchant_name="   ").status_code,
            400,
        )
        self.assertEqual(
            self._transaction_request(usage_month="2026-13").status_code,
            400,
        )
        self.assertEqual(
            self._card_detail_request(card_id=0).status_code,
            422,
        )
        self.assertEqual(
            self._card_detail_request(usage_month="2026-13").status_code,
            422,
        )

    def test_other_user_id_returns_403(self):
        response = self._request(user_id=999)
        self.assertEqual(response.status_code, 403)

    def test_inactive_card_is_excluded(self):
        with self.Session() as db:
            user_card = db.scalar(
                select(UserCard).where(
                    UserCard.user_id == 2,
                    UserCard.card_id == 3,
                )
            )
            user_card.is_active = False
            db.commit()
        self.assertEqual(self._request().json()["owned_card_count"], 2)

    def test_missing_monthly_state_defaults_to_zero(self):
        with self.Session() as db:
            states = build_user_card_states(db, 2, "2026-06")
        self.assertEqual(states[0]["previous_month_spending"], 0)
        self.assertEqual(states[0]["card_monthly_benefit_used"], 0)

    def test_benefit_usage_reduces_monthly_remaining_cap(self):
        body = self._request().json()
        card_one = next(
            card
            for card in [body["recommended_card"], *body["other_cards"]]
            if card["card_id"] == 1
        )
        self.assertEqual(card_one["expected_benefit"], 500)
        self.assertEqual(card_one["monthly_used"], 4_500)
        self.assertEqual(card_one["monthly_remaining"], 500)

    def test_adapter_query_count_is_constant(self):
        statements = []

        def count_selects(*args):
            statement = args[2]
            if statement.lstrip().upper().startswith("SELECT"):
                statements.append(statement)

        event.listen(self.engine, "before_cursor_execute", count_selects)
        try:
            with self.Session() as db:
                states = build_user_card_states(db, 2, "2026-07")
        finally:
            event.remove(self.engine, "before_cursor_execute", count_selects)

        self.assertEqual(len(states), 3)
        self.assertLessEqual(len(statements), 6)

    def test_debug_false_does_not_expose_debug_field(self):
        settings.recommendation_debug = False
        self.assertNotIn("debug", self._request().json())

    def test_debug_true_returns_card_traces(self):
        settings.recommendation_debug = True
        body = self._request().json()
        self.assertEqual(body["debug"]["resolved_category"], "카페")
        self.assertEqual(len(body["debug"]["cards"]), 3)
        self.assertTrue(body["debug"]["cards"][0]["benefits"])

    def test_zero_benefit_has_at_least_one_exclusion_reason(self):
        settings.recommendation_debug = True
        with self.Session() as db:
            usage = db.scalar(select(BenefitUsage))
            usage.monthly_used_amount = 5_000
            db.commit()
        traces = self._request().json()["debug"]["cards"]
        zero_benefits = [
            benefit
            for card in traces
            for benefit in card["benefits"]
            if benefit["expected_benefit"] == 0
        ]
        self.assertTrue(zero_benefits)
        self.assertTrue(
            all(item["exclusion_reasons"] for item in zero_benefits)
        )

    def test_local_login_success_and_no_sensitive_fields(self):
        with self.Session() as db:
            user = db.get(User, 2)
            user.password_hash = hash_password("password123")
            db.commit()

        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["token_type"], "bearer")
        self.assertTrue(body["access_token"])
        self.assertTrue(body["refresh_token"])
        self.assertEqual(body["expires_in"], 3600)
        self.assertNotIn("password", body["user"])
        self.assertNotIn("password_hash", body["user"])
        with self.Session() as db:
            stored = db.scalar(select(AuthRefreshToken))
            self.assertIsNotNone(stored)
            self.assertNotEqual(stored.token_hash, body["refresh_token"])
            self.assertEqual(len(stored.token_hash), 64)

    def test_refresh_token_rotates_and_reuse_revokes_session(self):
        with self.Session() as db:
            user = db.get(User, 2)
            user.password_hash = hash_password("password123")
            db.commit()
        login = self.client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        ).json()

        refreshed = self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login["refresh_token"]},
        )
        self.assertEqual(refreshed.status_code, 200)
        self.assertNotEqual(
            refreshed.json()["refresh_token"],
            login["refresh_token"],
        )
        reused = self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login["refresh_token"]},
        )
        self.assertEqual(reused.status_code, 401)
        new_token_after_reuse = self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refreshed.json()["refresh_token"]},
        )
        self.assertEqual(new_token_after_reuse.status_code, 401)

    def test_logout_revokes_refresh_token(self):
        with self.Session() as db:
            user = db.get(User, 2)
            user.password_hash = hash_password("password123")
            db.commit()
        login = self.client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        ).json()

        logout = self.client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": login["refresh_token"]},
        )
        self.assertEqual(logout.status_code, 200)
        rejected = self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login["refresh_token"]},
        )
        self.assertEqual(rejected.status_code, 401)

    def test_local_login_hides_failure_reason(self):
        with self.Session() as db:
            user = db.get(User, 2)
            user.password_hash = hash_password("correct")
            db.commit()

        for email, password in (
            ("missing@example.com", "correct"),
            ("test@example.com", "wrong"),
        ):
            with self.subTest(email=email, password=password):
                response = self.client.post(
                    "/api/v1/auth/login",
                    json={"email": email, "password": password},
                )
                self.assertEqual(response.status_code, 401)
                self.assertEqual(
                    response.json()["detail"],
                    "아이디 또는 비밀번호가 올바르지 않습니다.",
                )

    def test_local_login_empty_password_is_rejected(self):
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": ""},
        )
        self.assertEqual(response.status_code, 422)

    def test_protected_api_requires_bearer_token(self):
        response = self.client.get(
            "/api/v1/users/2/cards",
            headers={"Authorization": ""},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["www-authenticate"], "Bearer")

    def test_protected_api_rejects_invalid_token(self):
        response = self.client.get(
            "/api/v1/users/2/cards",
            headers={"Authorization": "Bearer invalid-token"},
        )
        self.assertEqual(response.status_code, 401)

    def test_manual_virtual_card_registration_and_integration(self):
        self._prepare_virtual_card()
        response = self._registration_request()
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["card"]["card_id"], 4)
        self.assertEqual(
            body["card"]["masked_card_number"],
            "**** **** **** 3456",
        )
        self.assertEqual(body["card"]["registration_method"], "MANUAL")
        self.assertEqual(body["card"]["previous_month_spending"], 0)
        self.assertEqual(body["card"]["current_month_spending"], 0)
        serialized = str(body)
        self.assertNotIn("1234567890123456", serialized)
        self.assertNotIn("'cvc'", serialized)
        self.assertNotIn("card_password_first2", serialized)
        self.assertNotIn("payment_token", serialized)
        with self.Session() as db:
            registered = db.scalar(
                select(UserCard).where(
                    UserCard.user_id == 2,
                    UserCard.card_id == 4,
                )
            )
            self.assertTrue(registered.payment_token.startswith("picka_pg_"))

        cards = self._cards_request().json()["cards"]
        self.assertIn(4, [card["card_id"] for card in cards])
        recommendation = self._request().json()["comparison"]
        self.assertIn(4, [card["card_id"] for card in recommendation])

    def test_card_number_spaces_are_normalized(self):
        self._prepare_virtual_card()
        response = self._registration_request(
            card_number="1234 5678 9012 3456"
        )
        self.assertEqual(response.status_code, 201)

    def test_virtual_card_registration_rejects_unknown_bin_and_format(self):
        self._prepare_virtual_card()
        response = self._registration_request(
            card_number="7777777788889999"
        )
        self.assertEqual(response.status_code, 400)
        for override in (
            {"card_number": "1234"},
            {"cvc": "12"},
            {"card_password_first2": "1"},
            {"expiry_month": 13},
        ):
            with self.subTest(override=override):
                response = self._registration_request(**override)
                self.assertEqual(response.status_code, 422)

    def test_virtual_card_registration_unknown_user_and_duplicate(self):
        self._prepare_virtual_card()
        unknown = self.client.post(
            "/api/v1/users/999/cards/manual",
            json={
                "card_number": "1234567890123456",
                "expiry_month": 12,
                "expiry_year": 2029,
                "cvc": "123",
                "card_password_first2": "45",
            },
        )
        self.assertEqual(unknown.status_code, 403)
        self.assertEqual(self._registration_request().status_code, 201)
        duplicate = self._registration_request()
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(
            duplicate.json()["detail"],
            "이미 등록된 카드입니다.",
        )

    def test_scanned_virtual_card_registration_uses_common_flow(self):
        self._prepare_virtual_card()
        response = self._registration_request(method="scan")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json()["card"]["registration_method"],
            "SCAN",
        )

    def test_user_card_soft_delete_preserves_data_and_can_restore(self):
        self._prepare_virtual_card()
        self.assertEqual(self._registration_request().status_code, 201)
        transaction = self._transaction_request(
            card_id=4,
            payment_category="카페",
        )
        self.assertEqual(transaction.status_code, 201)

        deleted = self.client.delete("/api/v1/users/2/cards/4")
        self.assertEqual(deleted.status_code, 200)
        cards = self._cards_request().json()["cards"]
        self.assertNotIn(4, [card["card_id"] for card in cards])
        recommendation = self._request().json()["comparison"]
        self.assertNotIn(4, [card["card_id"] for card in recommendation])

        with self.Session() as db:
            self.assertIsNotNone(db.get(Card, 4))
            stored_card = db.scalar(
                select(UserCard).where(
                    UserCard.user_id == 2,
                    UserCard.card_id == 4,
                )
            )
            self.assertEqual(stored_card.card_number_last4, "3456")
            self.assertTrue(stored_card.payment_token.startswith("picka_pg_"))
            self.assertEqual(
                db.scalar(
                    select(func.count())
                    .select_from(Transaction)
                    .where(Transaction.card_id == 4)
                ),
                1,
            )

        restored = self._registration_request(method="scan")
        self.assertEqual(restored.status_code, 201)
        self.assertEqual(
            restored.json()["card"]["registration_method"],
            "SCAN",
        )

    def test_delete_user_card_errors_and_other_user_is_unchanged(self):
        with self.Session() as db:
            db.add(
                User(
                    id=3,
                    email="third@example.com",
                    name="세 번째 사용자",
                )
            )
            db.add(UserCard(user_id=3, card_id=1, is_active=True))
            db.commit()
        self.assertEqual(
            self.client.delete("/api/v1/users/999/cards/1").status_code,
            403,
        )
        self.assertEqual(
            self.client.delete("/api/v1/users/2/cards/999").status_code,
            404,
        )
        self.assertEqual(
            self.client.delete("/api/v1/users/2/cards/1").status_code,
            200,
        )
        with self.Session() as db:
            other = db.scalar(
                select(UserCard).where(
                    UserCard.user_id == 3,
                    UserCard.card_id == 1,
                )
            )
            self.assertTrue(other.is_active)

    def test_calculable_benefit_is_included(self):
        settings.recommendation_debug = True
        traces = self._request().json()["debug"]["cards"]
        card_two = next(card for card in traces if card["card_id"] == 2)
        benefit = card_two["benefits"][0]
        self.assertTrue(benefit["included"])
        self.assertEqual(benefit["expected_benefit"], 1_000)

    def test_debug_card_amount_matches_recommendation_amount(self):
        settings.recommendation_debug = True
        body = self._request().json()
        result_cards = {
            card["card_id"]: card["expected_benefit"]
            for card in [body["recommended_card"], *body["other_cards"]]
        }
        debug_cards = {
            card["card_id"]: card["expected_benefit"]
            for card in body["debug"]["cards"]
        }
        self.assertEqual(debug_cards, result_cards)

    def test_select_uses_database_user_card_state(self):
        response = self._select_request()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["user_id"], 2)
        self.assertEqual(body["usage_month"], "2026-07")
        self.assertEqual(body["user_state_source"], "database")
        self.assertEqual(body["selected_card"]["card_id"], 2)

    def test_select_rejects_card_not_owned_by_user(self):
        response = self._select_request(selected_card_id=999)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["detail"],
            "선택한 카드는 사용자의 활성 보유 카드가 아닙니다.",
        )

    def test_select_other_user_id_returns_403(self):
        response = self._select_request(user_id=999)
        self.assertEqual(response.status_code, 403)

    def test_select_validates_usage_month(self):
        response = self._select_request(usage_month="2026-13")
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
