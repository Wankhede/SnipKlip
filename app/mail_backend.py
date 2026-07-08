import base64
import smtplib

from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend


class GmailOAuthEmailBackend(EmailBackend):
    def __init__(self, *args, **kwargs):
        self.use_oauth2 = kwargs.pop('use_oauth2', None)
        if self.use_oauth2 is None:
            self.use_oauth2 = getattr(settings, 'EMAIL_USE_OAUTH2', False) if settings.configured else False

        use_tls = kwargs.get('use_tls')
        if use_tls is None:
            kwargs['use_tls'] = getattr(settings, 'EMAIL_USE_TLS', True) if settings.configured else True

        use_ssl = kwargs.get('use_ssl')
        if use_ssl is None:
            kwargs['use_ssl'] = getattr(settings, 'EMAIL_USE_SSL', False) if settings.configured else False

        super().__init__(*args, **kwargs)

    def open(self):
        if self.connection:
            return False

        self.connection = smtplib.SMTP(self.host, self.port)
        self.connection.set_debuglevel(int(self.use_tls))
        self.connection.ehlo()

        if self.use_tls:
            self.connection.starttls()
            self.connection.ehlo()

        if self.use_oauth2 and self.password:
            auth_string = 'user=%s\x01auth=Bearer %s\x01\x01' % (self.username, self.password)
            self.connection.docmd('AUTH', 'XOAUTH2 ' + base64.b64encode(auth_string.encode('utf-8')).decode('ascii'))

        return True
