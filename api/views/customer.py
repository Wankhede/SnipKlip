from itertools import chain
from api.common import apply_filters, custom_pagination, get_all_table_records, log_error_with_api_endpoint
from api.decorators import jwt_authentication_required
from api.throttles import SustainedRateThrottle
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from api.serializers import *
from backend.models import Branch, Customer, Appointment, Salary, Expense, Employee, Invoice, BranchCustomerMobile, SalonDetails, User
from backend.views.vendor.essentials import create_username
from api.constants import *

# @group_required('Manager')
@api_view(['GET','POST','PUT'])
@throttle_classes([SustainedRateThrottle])
@jwt_authentication_required
def getAllCustomers(request, column_name=None, column_value=None):
    if request.method == "GET":
        try:
            if column_value is None:
                branch_id = request.GET['branch_id']
                request_args = request.GET
                
                if branch_id == '-1':
                    all_customers = get_all_table_records(request, Customer)
                else:
                    branch_mobile = BranchCustomerMobile.objects.filter(branch_id=branch_id)
                    all_customers = Customer.objects.filter(mobile_number__in = branch_mobile).order_by('name')

                final_customers_list = apply_filters(Customer, all_customers, request_args)

                total_rows = len(final_customers_list)

                # Call the custom_pagination function to get the paginated items.
                final_customers_list = custom_pagination(request, final_customers_list)

                serializer = CustomerSerializer(final_customers_list, many=True)

                # Return the serialized data in the response
                return Response({
                    "data": {
                        "count": total_rows,
                        "rows": serializer.data
                    },
                    "message": APIMessages.ALL_CUSTOMER_RETRIEVED.value,
                    "status": SUCCESS_STATUS_CODE,
                })
            else:
                try:
                    # Check if column_name is a valid field in the Expense model
                    valid_fields = [f.name for f in Customer._meta.get_fields()]
                    if column_name not in valid_fields:
                        return Response({"message": f"Invalid column name: {column_name}", "status":400})

                    # Build a dynamic filter using double-underscore notation
                    filter_kwargs = {f"{column_name}__exact": column_value} if column_name else {}
                    customer = Customer.objects.get(**filter_kwargs)

                    serializer = CustomerSerializer(customer, many=False)
                    # Return the serialized data in the response
                    return Response({
                            "data": {
                                "count": 0,
                                "rows": [serializer.data]
                            },
                            "message": APIMessages.CUSTOMER_RETRIEVED.value,
                            "status": SUCCESS_STATUS_CODE,
                        })
                except Customer.DoesNotExist:
                    return Response({
                        "message": APIMessages.CUSTOMER_NOT_FOUND.value,
                        "status": NOT_FOUND_STATUS,
                    })
        except  Exception as e:
            log_error_with_api_endpoint(request, e)
            return Response({
                "message": APIMessages.INTERNAL_SERVER_ERROR.value,
                "status": FAILED_STATUS_CODE,
            })

    elif request.method == "POST":
        try:
            data = request.data
            selected_branch_id = data['branch_id']
            branch = Branch.objects.get(id=selected_branch_id)
            email = request.data["email"]
            # try:
            #     user = User.objects.get(email=email)
            # except User.DoesNotExist:
            #     user = None
            # if user is not None:
            #     return Response({
            #             "message": APIMessages.EMAIL_ALREADY_EXISTS.value,
            #             "status": BAD_REQUEST_STATUS,
            #     })
            mobile_number = request.data["mobile"]
            first_name = request.data["first_name"]
            last_name = request.data["last_name"]
            gender = request.data["gender"]
            username = create_username(first_name,last_name)
            username = "".join(username.split())
            
            user = User.objects.create(
                username=username,
                email=email,
                mobile=mobile_number,
                name=first_name + ' ' + last_name,
                first_name=first_name,
                last_name=last_name,
                gender=gender
            )
            user.save()

            user = User.objects.get(username=username)
            customer = Customer.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                name=first_name + ' ' + last_name,
                email=email,
            )

            branch_mobile = BranchCustomerMobile(
                branch=branch,
                customer_user = customer,
                mobile = mobile_number
                )
            branch_mobile.save()

            customer.mobile_number.add(branch_mobile)
            customer.save()

            serializer = CustomerSerializer(customer, many=False)
            return Response({
                "data": {
                    "count": 1,
                    "rows": serializer.data
                },
                "message": APIMessages.CUSTOMER_CREATED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        except Exception as e:
            log_error_with_api_endpoint(request, e)
            return Response({
                "message": APIMessages.INTERNAL_SERVER_ERROR.value,
                "status": FAILED_STATUS_CODE,
            })
    
    elif request.method == "PUT":
        try:
            selected_branch_id = request.data['branch_id']
            status = request.data.get('status')
            branch = Branch.objects.get(id=selected_branch_id)
            customer_id = request.data["customer_id"]
            customer = Customer.objects.get(id=customer_id)
            user = customer.user
            customer_branch_mobile = BranchCustomerMobile.objects.get(branch=branch,customer_user=customer)
            
            email = request.data["email"]
            mobile_number = request.data["mobile"]
            first_name = request.data["first_name"]
            last_name = request.data["last_name"]
            gender = request.data["gender"]

            user.gender = gender
            user.save()

            customer_branch_mobile.mobile = mobile_number
            customer_branch_mobile.save()

            name = first_name + " " + last_name
            customer.first_name = first_name
            customer.last_name = last_name
            customer.email = email
            customer.name = name
            customer.status = status
            customer.save()

            serializer = CustomerSerializer(customer, many=False)
            return Response({
                "data": {
                    "count": 1,
                    "rows": serializer.data
                },
                "message": APIMessages.CUSTOMER_UPDATED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        except Exception as e:
            log_error_with_api_endpoint(request, e)
            return Response({
                "message": APIMessages.INTERNAL_SERVER_ERROR.value,
                "status": FAILED_STATUS_CODE,
            })
        
@api_view(['GET'])
@jwt_authentication_required
def getCustomerBookings(request, id):
    if request.method == "GET":
        try:
            branch_id = 6
            branch = Branch.objects.get(id=branch_id)
            user = User.objects.get(id=id)
            appointment = Appointment.objects.filter(branch=branch,user=user)
            invoice = set(Invoice.objects.filter(appointment__in = appointment))
            serializer = InvoiceSerializer(invoice, many=True)
            return Response({
                "data": {
                        "count": len(serializer.data),
                        "rows": serializer.data
                    },
                "message": APIMessages.ALL_CUSTOMER_RETRIEVED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        except Exception:
            return Response({
                'message':"Error",
                'status':400
            })