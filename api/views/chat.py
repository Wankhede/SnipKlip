from datetime import datetime
from api.common import custom_pagination, get_all_table_records
from api.decorators import jwt_authentication_required
from api.throttles import SustainedRateThrottle
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from api.serializers import CustomerSerializer, AppointmentSerializer, SalarySerializer, MessagingSerializer, EmployeeSerializer, InvoiceSerializer
from backend.models import Branch, Customer, Appointment, Salary, Messaging, Employee, Invoice, BranchCustomerMobile, SalonDetails, User
from api.constants import *

@api_view(['GET',"POST",'PUT'])
@throttle_classes([SustainedRateThrottle])
@jwt_authentication_required
def getAllMessaging(request, id=None):
    if request.method == "GET":
        if id is None:
            branch_id = request.GET['branch_id']

            if branch_id == '-1':
                all_messages = get_all_table_records(request, Messaging)
            else:
                branch = Branch.objects.get(id=branch_id)
                all_messages = Messaging.objects.filter(branch=branch).order_by('-id')

            # Call the custom_pagination function to get the paginated items.
            all_messages = custom_pagination(request, all_messages)            

            serializer = MessagingSerializer(all_messages, many=True)
            # Return the serialized data in the response
            return Response({
                "data": {
                    "count": len(all_messages),
                    "rows": list(serializer.data)
                },
                "message": APIMessages.ALL_MESSAGE_RETRIEVED.value,
                "status": SUCCESS_STATUS_CODE,
            })