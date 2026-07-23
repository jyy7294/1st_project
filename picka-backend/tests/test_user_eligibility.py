import unittest
from datetime import date, datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models import Card, CardRecommendationSnapshot, User, UserEligibility


class UserEligibilityModelTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        def override_get_db():
            with self.Session() as db:
                yield db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_stores_eligibility_and_user_relationship(self):
        with self.Session() as db:
            user = User(
                email="eligibility@example.com",
                name="Eligibility User",
            )
            user.eligibilities.append(UserEligibility(
                eligibility_type="MILITARY_SERVICE",
                eligibility_value="false",
                verification_status="VERIFIED",
                verified_at=datetime.now(timezone.utc),
            ))
            db.add(user)
            db.commit()
            db.refresh(user)

            self.assertEqual(len(user.eligibilities), 1)
            self.assertEqual(
                user.eligibilities[0].eligibility_value,
                "false",
            )

    def test_prevents_duplicate_type_for_same_user(self):
        with self.Session() as db:
            user = User(
                email="duplicate@example.com",
                name="Duplicate User",
            )
            db.add(user)
            db.flush()
            db.add_all([
                UserEligibility(
                    user_id=user.id,
                    eligibility_type="STUDENT",
                    eligibility_value="true",
                    verification_status="SELF_REPORTED",
                ),
                UserEligibility(
                    user_id=user.id,
                    eligibility_type="STUDENT",
                    eligibility_value="false",
                    verification_status="VERIFIED",
                ),
            ])

            with self.assertRaises(IntegrityError):
                db.commit()

    def test_user_api_updates_eligibility_and_invalidates_cache(self):
        with self.Session() as db:
            user = User(id=1, email="api@example.com", name="API User")
            db.add(user)
            db.add(CardRecommendationSnapshot(
                user_id=1,
                analysis_date=date.today(),
                credit_result={"cards": []},
                check_result={"cards": []},
            ))
            db.commit()

        response = self.client.put(
            "/api/v1/users/1/eligibilities",
            json={"eligibilities": [{
                "eligibility_type": "student",
                "eligibility_value": "true",
                "verification_status": "SELF_REPORTED",
            }]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["eligibilities"][0]["eligibility_type"],
            "STUDENT",
        )
        with self.Session() as db:
            self.assertEqual(db.query(CardRecommendationSnapshot).count(), 0)

    def test_card_rule_api_replaces_rules(self):
        with self.Session() as db:
            db.add(Card(id=1, card_name="Restricted Card", is_active=True))
            db.commit()

        response = self.client.put(
            "/api/v1/cards/1/eligibility-rules",
            json={"rules": [{
                "eligibility_type": "student",
                "required_value": "true",
                "comparison_operator": "EQ",
                "description": "학생 전용",
            }]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["rules"][0]["eligibility_type"], "STUDENT")


if __name__ == "__main__":
    unittest.main()
