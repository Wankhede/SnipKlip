from datetime import datetime
import requests
from api.common import apply_filters, custom_pagination, get_all_table_records
from api.decorators import jwt_authentication_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.serializers import InvoiceSerializer
from app.settings.base import GET_BASE_URL
from backend.models import *
from api.constants import *
import random
import string

@api_view(['GET', 'POST', 'PUT'])
@jwt_authentication_required
def getAllBillings(request, column_name=None, column_value=None):
    if request.method == "POST":
        data = request.data
        required_fields = (
            'branch_id', 'discount', 'discount_percentage', 'tax',
            'payment_received', 'invoice_detail', 'customerInfo', 'salon_id', 'date',
        )
        missing = [f for f in required_fields if f not in data or data.get(f) in (None, '')]
        if missing:
            return Response({
                'message': f'Missing required fields: {", ".join(missing)}',
                'status': BAD_REQUEST_STATUS,
            }, status=BAD_REQUEST_STATUS)

        # Extract basic data from the request
        branch_id = data['branch_id']
        discount = data['discount']
        discount_percentage = data['discount_percentage']
        tax = data['tax']
        payment_received = data['payment_received']
        due_payment = data.get('due_payment', 0)
        mode_of_payment = data.get('mode_of_payment', 'CASH')
        coupon_code = data.get('coupon_code')

        # Check if the branch exists
        branch_exists = Branch.objects.filter(id=branch_id).exists()
        if not branch_exists:
            return Response({
                'message': APIMessages.USER_OR_BRANCH_NOT_EXISTS.value,
                'status': BAD_REQUEST_STATUS,
            }, status=BAD_REQUEST_STATUS)
        selected_branch = Branch.objects.get(id=branch_id)

        service_list = []  # List to store service/product details
        staff_list = []    # List to store staff details

        try:
            # Iterate through invoice details to extract service/product and staff info
            for info in data['invoice_detail']:
                invoice_item = info['invoice_item']
                category = info['category']
                invoice_item_dict = {'category': category}

                # Retrieve the service or product based on category
                if category == 'Service':
                    invoice_item_dict['invoice_item'] = Service.objects.get(
                        branch=selected_branch, name=invoice_item['attribute_name'])
                elif category == 'Product':
                    invoice_item_dict['invoice_item'] = Product.objects.get(
                        branch=selected_branch, name=invoice_item['attribute_name'])

                service_list.append(invoice_item_dict)

                # Retrieve the staff associated with the service/product
                staff_ids = [staff['attribute_id'] for staff in info['staff']]
                staff_list.append(Employee.objects.filter(id__in=staff_ids, status="Active"))

            # Extract customer information
            user_data = data['customerInfo']
            customer_user = Customer.objects.get(name=user_data['name'], email=user_data['email']).user
            salon = SalonDetails.objects.get(id=data['salon_id'])

            # Parse and format the date
            original_date = data['date']
            date_selected = datetime.strptime(original_date, "%m/%d/%Y").strftime("%Y-%m-%d")
        except (KeyError, TypeError, ValueError, Customer.DoesNotExist, Service.DoesNotExist, Product.DoesNotExist, SalonDetails.DoesNotExist) as e:
            return Response({
                'message': f'Invalid billing payload: {e}',
                'status': BAD_REQUEST_STATUS,
            }, status=BAD_REQUEST_STATUS)

        total_price = 0  # Initialize total price
        appointment_list = []  # List to store created appointments
        order_id_list = []     # List to store generated order IDs

        # Create orders for each service/product and assign staff
        for staff, service_dict in zip(staff_list, service_list):
            order_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))  # Generate random order ID
            
            service = service_dict['invoice_item']
            category = service_dict['category']

            # Create a new appointment/order
            create_order = Appointment(
                user=customer_user,
                salon=salon,
                branch=selected_branch,
                totalPrice=service.price,
                order_id=str(order_id),
                isPaid=True,
                date=date_selected,
                createdAt=datetime.now(),
                booking_platform="WALK IN",
                booking_status="Pending",
                category=category
            )
            create_order.save()

            # Assign staff to the appointment
            for staff_assigned in staff:
                create_order.staff_assigned.add(staff_assigned)
            
            # Link the service or product to the appointment
            if category == "Product":
                create_order.product.add(service)
            elif category == "Service":
                create_order.service.add(service)
            
            create_order.save()

            order_id_list.append(create_order.order_id)
            appointment_list.append(create_order)
            total_price += create_order.totalPrice

        # Generate a random transaction ID
        transaction_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        
        # Calculate the total price after adding tax and discount
        tax_added_in_price = float(tax / 100) * float(total_price)
        discount_added = int(int(discount_percentage)/100 * int(total_price))
        actual_total_price = (float(total_price) - float(discount_added)) + float(tax_added_in_price)
        # Create and save the invoice
        invoice = Invoice(
            transaction="trans_" + transaction_id,
            date_created=datetime.today(),
            date_updated=datetime.today(),
            status="Paid",
            total=total_price,
            tax_added=tax,
            discount_added=discount_added,
            discount_percentage=discount_percentage,
            actual_amount=actual_total_price,
            due_payment=due_payment,
            mode_of_payment=mode_of_payment
        )
        invoice.save()

        current_time = datetime.now()

        try:
            # Retrieve customer mobile number
            customer_object = Customer.objects.get(name=user_data['name'], email=user_data['email'])
            mobile_number_customer = BranchCustomerMobile.objects.get(branch=selected_branch, customer_user=customer_object).mobile
        except Exception as e:
            # Handle errors if customer or mobile number is not found
            return Response({
                "message": APIMessages.ERROR.value,
                "status": METHOD_NOT_ALLOWED,
            })

        # Apply membership discount if available and valid
        if Membership.objects.filter(customer=customer_object, branch=selected_branch).exists():
            membership_available = Membership.objects.get(customer=customer_object, branch=selected_branch)
            if (
                membership_available and not invoice.membership and not invoice.coupon_code and 
                str(membership_available.expiry_date) >= str(current_time)
            ):
                discount_percentage = membership_available.discount_percent
                invoice.membership = membership_available
                invoice.save()
        else:
            # Apply coupon code if provided and valid
            if coupon_code and not invoice.membership and not invoice.coupon_code:
                if CouponCode.objects.filter(coupon_code=coupon_code, branch=selected_branch).exists():
                    coupon = CouponCode.objects.get(coupon_code=coupon_code, branch=selected_branch)
                    if (
                        coupon and coupon.minimum_value_amount <= invoice.total and 
                        coupon.available_count >= 1 and 
                        str(coupon.expiry_date) >= str(current_time)
                    ):
                        invoice.coupon_code = coupon
                        invoice.save()
                        coupon.available_count -= 1
                        coupon.save()
                else:
                    # Return error if coupon is not found or invalid
                    return Response({
                        "message": APIMessages.ERROR.value,
                        "status": NOT_FOUND_STATUS,
                    })

        # Update due payment in the invoice
        invoice.due_payment = int(due_payment)
        invoice.save()

        # Link the created appointments to the invoice
        for appointment in appointment_list:
            invoice.appointment.add(appointment)
            invoice.save()

        # Return success response with the invoice ID
        return Response({
            "data": {
                "id": invoice.id
            },
            "message": APIMessages.INVOICE_CREATED.value,
            "status": SUCCESS_STATUS_CODE,
        })

    if request.method == "GET":
        if column_value is not None:
            try:
                # Check if column_name is a valid field in the Expense model
                valid_fields = [f.name for f in Expense._meta.get_fields()]
                if column_name not in valid_fields:
                    return Response({"message": f"Invalid column name: {column_name}", "status": 400})

                # Build a dynamic filter using double-underscore notation
                filter_kwargs = {
                    f"{column_name}__exact": column_value} if column_name else {}
                invoice = Invoice.objects.get(**filter_kwargs)

                serializer = InvoiceSerializer(invoice, many=False)
                # Return the serialized data in the response
                return Response({
                    "data": {
                        "count": 0,
                        "rows": [serializer.data]
                    },
                    "message": APIMessages.ALL_INVOICE_RETRIEVED.value,
                    "status": SUCCESS_STATUS_CODE,
                })
            except Employee.DoesNotExist:
                return Response({
                    "message": APIMessages.EMPLOYEE_NOT_FOUND.value,
                    "status": NOT_FOUND_STATUS,
                })
        else:
            selected_branch_id = request.GET.get('branch_id')
            request_args = request.GET
            if selected_branch_id == '-1':
                all_invoices = get_all_table_records(request, Invoice)
            else:
                branch = Branch.objects.get(id=selected_branch_id)
                all_invoices = Invoice.objects.filter(
                    appointment__branch=branch,appointment__booking_status__in =['Availed','Pending','Booked']).order_by('-id')

            all_invoices = apply_filters(Invoice, all_invoices, request_args)

            total_rows = all_invoices.count()
            
            # Call the custom_pagination function to get the paginated items.
            invoices = custom_pagination(request, all_invoices)

            serializer = InvoiceSerializer(invoices, many=True)
            # Return the serialized data in the response
            return Response({
                "data": {
                    "count": total_rows,
                    "rows": serializer.data
                },
                "message": APIMessages.BILLING_RETRIEVED.value,
                "status": SUCCESS_STATUS_CODE,
            })

    elif request.method == "PUT":
        data = request.data
        
        # Extracting necessary data from the request
        status = data['status']
        invoice_id = data["invoice_id"]
        selected_branch = Branch.objects.get(id=data['branch_id'])
        payment_recieved = data['payment_received']
        tax_percentage = data["tax_percentage"]
        discount_percentage = data['discount_percentage']
        invoice_detail = data['invoice_detail']
        invoice = Invoice.objects.get(id=invoice_id)
        actual_amount = int(data['actual_amount'])
        mode_of_payment = data.get('mode_of_payment', 'CASH')
        total = 0  # Initialize total amount

        # Calculate the total price based on services in the invoice detail
        for invoice_item in invoice_detail:
            attribute_id = invoice_item['invoice_item']['attribute_id']
            service = Service.objects.get(id=attribute_id)
            price = service.price * invoice_item['qty']  # Multiply service price by quantity
            invoice.status = status  # Update invoice status
            total += price  # Accumulate the total price
        
        # Update invoice details if the condition is met (the condition is always True here)
        if True:
            invoice.total = int(total)
            invoice.tax_percentage = tax_percentage
            invoice.discount_percentage = discount_percentage

            # Calculate and update tax and discount amounts
            invoice.tax_added = int(int(tax_percentage)/100 * int(total)) 
            invoice.discount_added = int(int(discount_percentage)/100 * int(total)) 

            # Update the status and payment details for each appointment linked to the invoice
            if status != 'Cancelled':
                for appointment in invoice.appointment.all():
                    appointment.booking_status = 'Availed'
                    appointment.isPaid = True
                    appointment.save()  # Save the updated details for each appointment

            # Update the actual amount and due payment
            invoice.actual_amount = actual_amount
            invoice.due_payment = invoice.actual_amount - payment_recieved
            invoice.mode_of_payment = mode_of_payment
            invoice.save()  # Save the updated invoice details

            current_time = datetime.now()  # Get the current time

            try:
                # Retrieve customer information using name and email
                user_object = User.objects.get(name=data['customerInfo']['name'], email=data['customerInfo']['email'])
                customer_object = Customer.objects.get(user=user_object)
                # Get the mobile number associated with the customer in the selected branch
                mobile_number_customer = BranchCustomerMobile.objects.get(branch=selected_branch, customer_user=customer_object).mobile
            except Exception as e:
                # Handle case where customer or mobile number is not found
                return Response({
                    "message": APIMessages.ERROR.value,
                    "status": METHOD_NOT_ALLOWED,
                })

            # Check if the customer has a valid membership
            if Membership.objects.filter(customer=customer_object, branch=selected_branch):
                membership_available = Membership.objects.get(customer=customer_object, branch=selected_branch)
                if (
                    membership_available and not invoice.membership and not invoice.coupon_code and 
                    str(membership_available.expiry_date) >= str(current_time)
                ):
                    discount_percentage = membership_available.discount_percent
                    invoice.price_cut_by_membership = int(discount_percentage / 100 * invoice.total)
                    invoice.membership = membership_available
                    invoice.save()
            else:
                try:
                    coupon_code = data['coupon_code']
                except Exception:
                    coupon_code = ''
                
                # Apply coupon code if valid and available
                if (
                    coupon_code != "" and not invoice.membership and not invoice.coupon_code and coupon_code is not None
                ):
                    if CouponCode.objects.filter(coupon_code=coupon_code, branch=selected_branch):
                        coupon = CouponCode.objects.get(coupon_code=coupon_code, branch=selected_branch)
                        if (
                            coupon and coupon.minimum_value_amount <= invoice.total and 
                            coupon.available_count >= 1 and str(coupon.expiry_date) >= str(current_time)
                        ):
                            invoice.coupon_code = coupon
                            invoice.price_cut_by_coupon_code = int(invoice.discount_percent / 100 * invoice.total)
                            invoice.save()
                            coupon.available_count -= 1  # Decrease the available count of the coupon
                            coupon.save()
                    else:
                        # Return error if the coupon is not found or invalid
                        return Response({
                            "message": APIMessages.ERROR.value,
                            "status": NOT_FOUND_STATUS,
                        })

            invoice.save()  # Save the final invoice updates
            
            serializer = InvoiceSerializer(invoice, many=False)
            return Response({
                    "data": {
                        "count": 1,
                        "rows": serializer.data
                    },
                    "message": APIMessages.BILLING_UPDATED.value,
                    "status": SUCCESS_STATUS_CODE,
            })

        else:
            return Response({
                    "message": APIMessages.BILLING_STATUS_UNPAID.value,
                    "status": FAILED_STATUS_CODE,
                })

from backend.crypto_utils import load_fernet_key

def load_key():
    return load_fernet_key()

@api_view(['POST'])
@jwt_authentication_required
def getInvoice(request):
    if request.method == "POST":
        # Retrieve all customers
        print(request.data)
        id = request.data["id"]
        try:
            invoice = Invoice.objects.get(id=id)

            # Create a list to hold the staff data
            appointment_data_list = []
            for appointment in invoice.appointment.filter(booking_status__in = ['Availed','Booked','Pending']):
                if appointment.category == "Service":
                    invoice_item = appointment.service.all()
                elif appointment.category == "Product":
                    invoice_item = appointment.product.all()

                appointment_data = {
                    'invoice_item': {
                        'attribute_id': invoice_item.first().id,
                        'attribute_name': invoice_item.first().name,
                    },
                    'staff_assigned': [],
                    'price': 0,
                    'category': appointment.category
                }

                appointment_data['price'] = invoice_item.first().price

                for staff in appointment.staff_assigned.all():
                    staff_assigned_data = {
                        'attribute_id': staff.id,
                        'attribute_name': staff.user.name
                    }
                    appointment_data['staff_assigned'].append(staff_assigned_data)

                appointment_data_list.append(appointment_data)

            # Serialize all customers
            serializer = InvoiceSerializer(invoice, many=False)

            # Return the serialized data in the response
            return Response({
                "data": {
                    "count": 1,
                    "rows": serializer.data,
                    'staff_data': appointment_data_list
                },
                "message": APIMessages.INVOICE_RETRIEVED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        except Exception:
            return Response({
                "message": APIMessages.ERROR.value,
                "status": FAILED_STATUS_CODE,
            })

