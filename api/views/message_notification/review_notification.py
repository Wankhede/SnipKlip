from django.conf import settings
from rest_framework.response import Response
from api.constants import FAILED_STATUS_CODE, SUCCESS_STATUS_CODE, APIMessages
from api.views.message_notification.main import send_notification
from backend.models import Branch, BranchCustomerMobile, Customer, Invoice, User
from rest_framework.decorators import api_view
from django.conf import settings

# Assuming 'SERVER' is defined in your local.py settings file
server_value = settings.SERVER

@api_view(["POST"])
def send_review_notification_to_customer(request):
    if request.method == "POST":
        data = request.data
        branch_id = data['branch_id']
        invoice_id = data['invoice_id']

        try:
            customer_name = data['customer_name']
            customer = Customer.objects.get(name=customer_name)
        except Exception:
            customer_name = data['customerInfo']['name']
            user_object = User.objects.get(name=customer_name)
            customer = Customer.objects.get(user=user_object)

        branch = Branch.objects.get(id=branch_id)
        try:
            customer_mobile = BranchCustomerMobile.objects.get(customer_user=customer, branch=branch).mobile
            customer_name = customer.name
            method = "WHATSAPP"

            all_appointment = []
            service = []
            invoice = Invoice.objects.get(id=invoice_id)

            # Collect all appointments related to the invoice
            for appointment in invoice.appointment.all():
                all_appointment.append(appointment)

            # Collect all services related to each appointment
            for appoint in all_appointment:
                for services in appoint.service.all():
                    service.append(services)

            if server_value != 0:
                email = customer.email
            else:
                email = settings.DEFAULT_EMAIL

            #Set Phone Number According to Server Number
            if server_value != 0:
                # Validate and format phone number
                if len(str(customer_mobile)) == 10:  # If mobile number is 10 digits
                    phone_no = '91' + str(customer_mobile)
                elif len(str(customer_mobile)) == 12:  # If mobile number is 12 digits (already includes country code)
                    phone_no = str(customer_mobile)
            else:
                phone_no = settings.DEFAULT_MOBILE_NUMBER

            transaction_number = invoice.transaction

            templateId = 6

            link = f"{settings.FRONTEND_LINK}/apps/reviews/add-review/{transaction_number}"

            # Payload for WhatsApp message
            payload = [{
                "type": "text",
                "text": link
            }]

            # Data for further processing (optional)
            data = {'link': link}

            status, message = send_notification(method=method, templateId=templateId, payload=payload, data=data, phone_no=phone_no, email=email)
            return Response({
                "message": APIMessages.NOTIFICATION_CREATED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        except:
            return Response({
                "message": APIMessages.NOTIFICATION_FAILED.value,
                "status": FAILED_STATUS_CODE,
            })
    else:
        return Response({
                "message": APIMessages.NOTIFICATION_FAILED.value,
                "status": FAILED_STATUS_CODE,
            })
    