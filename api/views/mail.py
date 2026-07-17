from datetime import datetime, timedelta, timezone
from django.conf import settings
from django.core.mail import send_mail
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_joining_mail(email, company_name, name):
    """This function is used to send mail through Sendgrid API
    Args:
        data: It contains list of dictionaries with the required factories data
    Returns:
        Json Response: On success and failure
    """
    EMAIL_SENDER = settings.DEFAULT_FROM_EMAIL
    EMAIL_RECEIVERS = [email]
    subject = f'Welcome to {settings.COMPANY_NAME}'
    message = f'Hello {name},\n\nWelcome to {settings.COMPANY_NAME}.\n\nThank you for joining us.'
    try:
        send_mail(subject, message, EMAIL_SENDER, EMAIL_RECEIVERS, fail_silently=False)
        return {'success': 'email sent'}
    except Exception as e:
        return {'error': str('mail sending: ') + str(e)}

def send_mail(template_id, email, data):
    """This function is used to send mail through Sendgrid API
    Args:
        data: It contains list of dictionaries with the required factories data
    Returns:
        Json Response: On success and failure
    """
    # import ipdb;ipdb.set_trace()
    EMAIL_SENDER = (settings.DEFAULT_FROM_EMAIL, settings.DEFAULT_FROM_NAME)  # account used for sending emails
    EMAIL_RECEIVERS = [(email, email)]
    API_CLIENT = settings.SENDGRID_API_KEY
    TEMPLATE_ID = template_id
    try:
        message = Mail(
            from_email=EMAIL_SENDER,
            to_emails=EMAIL_RECEIVERS)
        message.template_id = TEMPLATE_ID
        if data:
            message.dynamic_template_data = data
            sg = SendGridAPIClient(API_CLIENT)
            response = sg.send(message)
            return {'success': 'email sent', 'sendgrid': {'status_code': response.status_code}}
        else:
            message.dynamic_template_data = {'data': []}
            sg = SendGridAPIClient(API_CLIENT)
            response = sg.send(message)
            return {'success': 'email not sent', 'sendgrid': {'status_code': response.status_code}}
    except Exception as e:
        return {'error': str('mail sending: ') + str(e)}