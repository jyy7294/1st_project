import unittest
from datetime import date, datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.models import (
    Card,
    CardRecommendationSnapshot,
    PrivacyAuditLog,
    User,
    UserEligibility,
    UserPersonaProfile,
)
from app.services.auth_service import create_access_token


class UserEligibilityModelTest(unittest.TestCase):
    def setUp(self):
        self.original_jwt_secret_key = settings.jwt_secret_key
        settings.jwt_secret_key = "test-jwt-secret-key-at-least-32-bytes"
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
        settings.jwt_secret_key = self.original_jwt_secret_key
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

        with self.Session() as db:
            token = create_access_token(db.get(User, 1))
        self.client.headers.update({"Authorization": f"Bearer {token}"})

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
            db.add(User(
                id=1,
                email="rules@example.com",
                name="Rules User",
                role="ADMIN",
            ))
            db.add(Card(id=1, card_name="Restricted Card", is_active=True))
            db.commit()

        with self.Session() as db:
            token = create_access_token(db.get(User, 1))
        self.client.headers.update({"Authorization": f"Bearer {token}"})

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

    def test_regular_user_cannot_replace_card_rules(self):
        with self.Session() as db:
            db.add(User(id=1, email="user@example.com", name="Regular User"))
            db.add(Card(id=1, card_name="Restricted Card", is_active=True))
            db.commit()
            token = create_access_token(db.get(User, 1))

        response = self.client.put(
            "/api/v1/cards/1/eligibility-rules",
            headers={"Authorization": f"Bearer {token}"},
            json={"rules": [{
                "eligibility_type": "STUDENT",
                "required_value": "true",
            }]},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "관리자 권한이 필요합니다.")

    def test_personal_profile_update_invalidates_cache_and_audits_field_names(self):
        with self.Session() as db:
            user = User(id=1, email="profile@example.com", name="Old Name")
            user.persona_profile = UserPersonaProfile(
                persona_id="P001",
                age=25,
                phone_number="01000000000",
                source_payload={},
            )
            db.add(user)
            db.add(CardRecommendationSnapshot(
                user_id=1,
                analysis_date=date.today(),
                credit_result={"cards": []},
                check_result={"cards": []},
            ))
            db.commit()
            token = create_access_token(user)

        response = self.client.patch(
            "/api/v1/users/1/personal-profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "New Name",
                "birth_date": "2000-05-10",
                "phone_number": "010-1234-5678",
                "gender": "FEMALE",
                "occupation": "학생",
                "residence": "서울특별시",
                "eligibilities": [{
                    "eligibility_type": "STUDENT",
                    "eligibility_value": "true",
                }],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "New Name")
        self.assertEqual(response.json()["phone_number"], "01012345678")
        self.assertEqual(response.json()["eligibilities"][0]["eligibility_type"], "STUDENT")
        with self.Session() as db:
            self.assertEqual(db.query(CardRecommendationSnapshot).count(), 0)
            audit = db.scalar(select(PrivacyAuditLog))
            self.assertIn("phone_number", audit.changed_fields)
            self.assertIn("eligibility.STUDENT", audit.changed_fields)
            serialized = str(audit.changed_fields)
            self.assertNotIn("01012345678", serialized)
            self.assertNotIn("New Name", serialized)
            profile = db.scalar(select(UserPersonaProfile))
            eligibility = db.scalar(select(UserEligibility))
            self.assertNotIn("01012345678", profile.phone_number_encrypted)
            self.assertNotIn("true", eligibility.eligibility_value_encrypted)

    def test_personal_profile_rejects_other_user_and_future_birth_date(self):
        with self.Session() as db:
            user = User(id=1, email="profile@example.com", name="User")
            db.add(user)
            db.commit()
            token = create_access_token(user)

        forbidden = self.client.get(
            "/api/v1/users/2/personal-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        invalid = self.client.patch(
            "/api/v1/users/1/personal-profile",
            headers={"Authorization": f"Bearer {token}"},
            json={"birth_date": "2999-01-01"},
        )
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(invalid.status_code, 422)


if __name__ == "__main__":
    unittest.main()
