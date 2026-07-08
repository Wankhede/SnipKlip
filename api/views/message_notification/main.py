from api.views.sms import sms
from api.views.mail import send_mail
from api.views.whatsapp import whatsApp
from django.conf import settings

def send_notification(method, **kwargs):
    if settings.SERVER == 99:
        if method.upper() == 'EMAIL':
            try:
                send_mail(kwargs.get('templated_id'), kwargs.get('email'), kwargs.get('data'))
                status = True
                message = 'Email sent successfully'
            except Exception as e:
                message = str(e)

        elif method.upper() == 'WHATSAPP':
            try:
                whatsApp(messageParams=kwargs.get('payload'), phoneNo=kwargs.get('phone_no'), templateId=kwargs.get('templateId'))
                status = True
                message = 'WhatsApp sent successfully'
            except Exception as e:
                message = str(e)

        elif method.upper() == 'SMS':
            try:
                sms()
                status = True
                message = 'SMS sent successfully'
            except Exception as e:
                message = str(e)

        return status, message
