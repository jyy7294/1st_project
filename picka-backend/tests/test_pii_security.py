import base64
import logging
import unittest

from app.core.config import settings
from app.services.pii_encryption_service import decrypt_text, encrypt_text
from app.services.sensitive_log_filter import (
    SensitiveDataLogFilter,
    mask_sensitive_text,
)


class PiiSecurityTest(unittest.TestCase):
    def setUp(self):
        self.original_key = settings.pii_encryption_key
        settings.pii_encryption_key = base64.urlsafe_b64encode(b"k" * 32).decode()

    def tearDown(self):
        settings.pii_encryption_key = self.original_key

    def test_aes_gcm_encrypts_and_binds_ciphertext_to_context(self):
        encrypted = encrypt_text("01012345678", context="profile:1:phone_number")
        self.assertNotIn("01012345678", encrypted)
        self.assertEqual(
            decrypt_text(encrypted, context="profile:1:phone_number"),
            "01012345678",
        )
        with self.assertRaises(ValueError):
            decrypt_text(encrypted, context="profile:2:phone_number")

    def test_sensitive_log_masking(self):
        message = (
            "Authorization=Bearer abc.def.ghi phone=010-1234-5678 "
            "card=1234-5678-9012-3456 refresh_token=secret-token "
            'email=test@example.com "cvc": "123" '
            "payment_token=picka_pg_private-token "
            "database=postgresql://picka:db-password@db.example.com/picka"
        )
        masked = mask_sensitive_text(message)
        self.assertNotIn("abc.def.ghi", masked)
        self.assertNotIn("010-1234-5678", masked)
        self.assertNotIn("1234-5678-9012-3456", masked)
        self.assertNotIn("secret-token", masked)
        self.assertNotIn("test@example.com", masked)
        self.assertNotIn('"123"', masked)
        self.assertNotIn("picka_pg_private-token", masked)
        self.assertNotIn("db-password", masked)

    def test_sensitive_log_filter_masks_structured_arguments(self):
        record = logging.LogRecord(
            "picka.test",
            logging.INFO,
            __file__,
            1,
            "payload=%s",
            ({
                "refresh_token": "private-refresh-token",
                "nested": {"card_number": "1234567890123456"},
                "safe": "visible",
            },),
            None,
        )

        self.assertTrue(SensitiveDataLogFilter().filter(record))
        rendered = record.getMessage()
        self.assertNotIn("private-refresh-token", rendered)
        self.assertNotIn("1234567890123456", rendered)
        self.assertIn("visible", rendered)


if __name__ == "__main__":
    unittest.main()
