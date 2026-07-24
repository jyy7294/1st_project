import unittest

from app.core.database import database_url_with_required_ssl


class DatabaseSecurityTest(unittest.TestCase):
    def test_remote_postgresql_requires_ssl(self):
        secured = database_url_with_required_ssl(
            "postgresql+psycopg://user:secret@db.example.com:5432/picka"
        )
        self.assertEqual(secured.query["sslmode"], "require")

    def test_remote_postgresql_overrides_insecure_ssl_mode(self):
        secured = database_url_with_required_ssl(
            "postgresql://user:secret@db.example.com/picka?sslmode=disable"
        )
        self.assertEqual(secured.query["sslmode"], "require")

    def test_local_and_sqlite_databases_are_unchanged(self):
        local = database_url_with_required_ssl(
            "postgresql://user:secret@localhost/picka"
        )
        sqlite = database_url_with_required_ssl("sqlite://")
        self.assertNotIn("sslmode", local.query)
        self.assertNotIn("sslmode", sqlite.query)


if __name__ == "__main__":
    unittest.main()
