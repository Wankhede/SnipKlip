import os
import unittest
from unittest.mock import patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings.local')

from app.mail_backend import GmailOAuthEmailBackend


class GmailOAuthEmailBackendTests(unittest.TestCase):
    def test_oauth_token_uses_xoauth2_auth(self):
        backend = GmailOAuthEmailBackend(
            host='smtp.gmail.com',
            port=587,
            username='user@example.com',
            password='token-value',
            use_tls=False,
            use_oauth2=True,
        )

        with patch('app.mail_backend.smtplib.SMTP') as smtp_cls:
            connection = smtp_cls.return_value
            connection.ehlo.return_value = ('250', b'')
            backend.open()

            connection.docmd.assert_called_once()
            self.assertEqual(connection.docmd.call_args[0][0], 'AUTH')
            self.assertTrue(connection.docmd.call_args[0][1].startswith('XOAUTH2 '))


if __name__ == '__main__':
    unittest.main()
