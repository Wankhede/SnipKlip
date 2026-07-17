from django.conf import settings
from api.throttles import BurstRateThrottle, SustainedRateThrottle
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from api.constants import *

@api_view(['POST'])
@throttle_classes([BurstRateThrottle])
def contactus(request):
    if request.method == 'POST':
        name = request.data.get('name')
        email = request.data.get('email')
        phone = request.data.get('phone')
        message = request.data.get('message')

        # Send email
        subject = f'Message From {name}'
        message = f"Name: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage: {message}"
        from_email = settings.ADMIN_EMAIL
        recipient_list = settings.CONTACT_RECIPIENTS

        try:
            message = Mail(
                from_email=from_email,
                to_emails=recipient_list,
                subject=subject,
                plain_text_content=message
            )
            sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
            response = sg.send(message)

            return Response({
                "message": APIMessages.MESSAGE_TO_SNIPKLIP.value,
                "status": SUCCESS_STATUS_CODE,
            })
        except Exception as e:
            return Response({
                "message": f"Failed to send message: {str(e)}",
                "status": FAILED_STATUS_CODE,
            })
