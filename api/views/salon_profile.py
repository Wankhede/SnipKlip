from django.conf import settings

from api.decorators import jwt_authentication_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.serializers import UserSerializer,SalonDetailsSerializer,BranchSerializer
from backend.models import *
from api.constants import *

@api_view(['GET', 'PUT'])
def get_salon_profile(request,user_id):
    if request.method == "GET":
        try:
            user_id = int(user_id)
        except Exception:
            return Response({
                "message": APIMessages.USER_NOT_FOUND.value,
                "status": UNAUTHORISED_CODE,
            })
        
        if user_id == None or user_id == "" or not user_id:
            return Response({
                "message": APIMessages.USER_NOT_FOUND.value,
                "status": UNAUTHORISED_CODE,
            })
        user = User.objects.get(id=user_id)
        if SalonDetails.objects.filter(user=user):
            salon = SalonDetails.objects.get(user=user)
            branch = Branch.objects.filter(salon=salon)
            serializer = BranchSerializer(branch,many=True)
            return Response({
                "data": {
                    "count": 0,
                    "rows": serializer.data
                },
                "message": APIMessages.ALL_EMPLOYEE_RETRIEVED.value,
                "status": SUCCESS_STATUS_CODE,
            })
    
    elif request.method == "PUT":
        user_id = request.data.get('user_id',100)
        user = User.objects.get(email=settings.DEFAULT_FROM_EMAIL)
        try:
            salon_data = SalonDetails.objects.get(user=user)
            try:
                salon_name = request.data["salon_name"]
                owner_name = request.data["owner_name"]
                email = request.data["email"]
                owner_email = request.data["owner_email"]
                contact_no = request.data["contact_no"]

                salon_data.name = salon_name
                salon_data.owner_name = owner_name
                salon_data.email = email
                salon_data.owner_email = owner_email
                salon_data.contact_no = contact_no
                salon_data.save()

                return Response({
                            'message':APIMessages.SALON_UPDATED.value,
                            'status':SUCCESS_STATUS_CODE
                            })
            
            except Exception:
                return Response({
                                'message': APIMessages.FILL_FIELDS.value,
                                'status':BAD_REQUEST_STATUS
                                })

        except Exception:
            return Response({
                'message': APIMessages.SALON_NOT_FOUND.value,
                'status':BAD_REQUEST_STATUS
            })
        



