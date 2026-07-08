from api.throttles import BurstRateThrottle, SustainedRateThrottle
from rest_framework.throttling import UserRateThrottle
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from django.conf import settings
from django.core.mail import send_mail
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
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = settings.CONTACT_RECIPIENTS

        try:
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)

            return Response({
                "message": APIMessages.MESSAGE_TO_SNIPKLIP.value,
                "status": SUCCESS_STATUS_CODE,
            })
        except Exception as e:
            return Response({
                "message": f"Failed to send message: {str(e)}",
                "status": FAILED_STATUS_CODE,
            })
