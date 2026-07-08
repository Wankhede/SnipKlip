import random
from django.conf import settings
from django.core.mail import send_mail
import math
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import User
from django.contrib.auth.models import *
from django.contrib.auth import get_user_model
from backend.models import *
User = get_user_model()
from api.constants import *


def generateOTP_forget_password() :
     digits = "0123456789"
     OTP = ""
     for i in range(4) :
         OTP += digits[math.floor(random.random() * 10)]
     return OTP



@api_view(['POST','GET','PUT'])
def send_code_email(request):
     global otp_num
     global email
     if request.method == "POST":
          global otp_num
          data = request.data
          try:
               email = data['email'] 
          except Exception:
               return Response({
                    "message": APIMessages.EMAIL_NOT_RECEIVED.value,
                    "status": NOT_FOUND_STATUS,
               })
          
          if data['otp_num'] == "" or not data['otp_num'] or data['otp_num'] == None:
               otp_num= str(generateOTP_forget_password())
               try:
                    user = User.objects.get(email=email)
               except User.DoesNotExist:
                    return Response({
                         "message": APIMessages.USER_NOT_FOUND.value,
                         "status": NOT_FOUND_STATUS,
                    })
     

               subject = 'You have requested to reset your password. Please click the link below to reset your password:'
               message = f'OTP is {otp_num}'
               from_email = settings.DEFAULT_FROM_EMAIL
               recipient_list = [f'{email}']

               try:
                    send_mail(subject, message, from_email, recipient_list, fail_silently=False)

                    return Response({
                         "message": APIMessages.EMAIL_SENT.value,
                         "status": SUCCESS_STATUS_CODE,
                    })
               except Exception as e:
                    return Response({
                         "message": f"Failed to send message: {str(e)}",
                         "status": FAILED_STATUS_CODE,
                    })
          else:
               otp_recieve = data['otp_num']
               new_password = data['password']
               confirm_password = data['confirm_password']

               if new_password == "" or confirm_password == "":
                    return Response({
                         'message':APIMessages.FILL_FIELDS.value,
                         'status': FAILED_STATUS_CODE
                    })
               
               if new_password == confirm_password:
                    if otp_recieve == otp_num:
                         user = User.objects.get(email = email)
                         user.set_password(new_password)
                         user.save()
                         return Response({
                              'message': APIMessages.PASSWORD_RESET.value,
                              'status': SUCCESS_STATUS_CODE
                         })
                    else:
                         return Response({
                              'message':APIMessages.OTP_MISMATCH.value,
                              'status': FAILED_STATUS_CODE
                         })
               else:
                    return Response({
                              'message':APIMessages.PASSWORD_MISMATCH.value,
                              'status': FAILED_STATUS_CODE
                         })
