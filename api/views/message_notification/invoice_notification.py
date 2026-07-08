from datetime import datetime
from rest_framework.response import Response
from api.constants import FAILED_STATUS_CODE, SUCCESS_STATUS_CODE, APIMessages
from api.decorators import jwt_authentication_required
from api.views.message_notification.main import send_notification
from django.conf import settings
from rest_framework.decorators import api_view
from backend.models import Invoice
# Assuming 'SERVER' is defined in settings
server_value = settings.SERVER


@api_view(['POST'])
@jwt_authentication_required
def send_invoice_notification(request):
    try:
        data = request.data
        method = data['method']
        date = data['date'].split('T')[0]
        date = datetime.strptime(date, "%Y-%m-%d").date()
        id = data['id']
        invoice = Invoice.objects.get(id=id)
        customer_info = data['customerInfo']
        cashierInfo = data['cashierInfo']
        
        if server_value != 0:
            email = customer_info['email']
            phone_no = cashierInfo['mobile']
        else:
            email = settings.DEFAULT_EMAIL
            phone_no = settings.DEFAULT_MOBILE_NUMBER

        templateId = 5
        link =  '[NOT AVAILABLE]'
        payload = [{
            "type": "text",
            "text": customer_info.get('name')
        },{
            "type": "text",
            "text": cashierInfo.get('name')
        },{
            "type": "text",
            "text": str(date)
        },{
            "type": "text",
            "text": int(invoice.actual_amount) - int(invoice.due_payment)
        },{
            "type": "text",
            "text": link
        }]
        template_id = 'd-23fdc775f1e44065a09c4378e2c9185f'
        data = {'salonName': customer_info.get('name'), 'name':customer_info.get('name'), 'transactionId': invoice.transaction, 'link':link,'total':int(invoice.actual_amount) - int(invoice.due_payment)}
        status, message = send_notification(method=method, templateId=templateId, payload=payload, template_id=template_id, data=data, phone_no=phone_no, email=email)
        
        return Response({
            "message": APIMessages.NOTIFICATION_CREATED.value,
            "status": SUCCESS_STATUS_CODE,
        })
    except:
        return Response({
            "message": APIMessages.NOTIFICATION_FAILED.value,
            "status": FAILED_STATUS_CODE,
        })
