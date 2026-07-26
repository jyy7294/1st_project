import unittest
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.models import User, UserEligibility, UserPersonaProfile
from app.services.auth_service import create_access_token


FULL_QUALIFICATION = {
    "military_service_eligible": False,
    "sole_proprietor": True,
    "compact_car_owner": False,
    "pregnancy_parenting_card_eligible": False,
    "other_welfare_card_eligible": False,
    "owns_vehicle": True,
    "primary_transportation": ["자가용", "대중교통"],
    "uses_k_pass": False,
    "uses_hipass": True,
    "mobile_carrier": "SKT",
    "preferred_airline": ["KOREAN_AIR", "ASIANA"],
    "shopping_affiliates": ["신세계", "쿠팡"],
    "memberships": ["T우주"],
    "has_children": True,
    "child_count": 2,
    "children_age_groups": ["미취학", "초등학생"],
}


class QualificationProfileApiTest(unittest.TestCase):
    def setUp(self):
        self.original_jwt_secret_key = settings.jwt_secret_key
        settings.jwt_secret_key = "test-jwt-secret-key-at-least-32-bytes"
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        def override_get_db():
            with self.Session() as db:
                yield db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)
        with self.Session() as db:
            user = User(id=1, email="profile@example.com", name="홍길동")
            user.persona_profile = UserPersonaProfile(
                persona_id="user-1",
                age=30,
                birth_date=date(1996, 1, 2),
                phone_number="01012345678",
                gender="MALE",
                job="개발자",
                residence="서울",
                source_payload={},
            )
            db.add(user)
            db.commit()
            token = create_access_token(user)
        self.client.headers.update({"Authorization": f"Bearer {token}"})

    def tearDown(self):
        settings.jwt_secret_key = self.original_jwt_secret_key
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_initial_create_get_and_partial_update(self):
        created = self.client.put(
            "/api/v1/users/1/qualification-profile", json=FULL_QUALIFICATION
        )
        self.assertEqual(created.status_code, 200, created.text)
        self.assertTrue(created.json()["qualification_completed"])
        self.assertEqual(created.json()["name"], "홍길동")
        self.assertEqual(created.json()["children_age_groups"], ["미취학", "초등학생"])
        self.assertEqual(
            created.json()["preferred_airline"], ["KOREAN_AIR", "ASIANA"]
        )
        with self.Session() as db:
            shopping = db.scalar(select(UserEligibility).where(
                UserEligibility.eligibility_type
                == "PRIMARY_SHOPPING_AFFILIATION"
            ))
            self.assertIsNotNone(shopping)
            self.assertEqual(shopping.eligibility_value, '["신세계","쿠팡"]')

        updated = self.client.patch(
            "/api/v1/users/1/qualification-profile",
            json={"occupation": "기획자", "mobile_carrier": "KT"},
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["occupation"], "기획자")
        self.assertEqual(updated.json()["mobile_carrier"], "KT")
        with self.Session() as db:
            row = db.scalar(select(UserEligibility).where(
                UserEligibility.eligibility_type == "MOBILE_CARRIER"
            ))
            self.assertNotIn("KT", row.eligibility_value_encrypted)

    def test_initial_create_requires_every_qualification_field(self):
        response = self.client.put(
            "/api/v1/users/1/qualification-profile",
            json={"military_service_eligible": False},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("mobile_carrier", response.json()["detail"]["missing_fields"])

    def test_rejects_inconsistent_children(self):
        payload = {**FULL_QUALIFICATION, "has_children": False, "child_count": 2}
        response = self.client.put(
            "/api/v1/users/1/qualification-profile", json=payload
        )
        self.assertEqual(response.status_code, 422)

    def test_rejects_more_than_two_airlines_or_transportation_types(self):
        for field in ("preferred_airline", "primary_transportation"):
            response = self.client.patch(
                "/api/v1/users/1/qualification-profile",
                json={field: ["ONE", "TWO", "THREE"]},
            )
            self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
