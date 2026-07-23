from datetime import datetime
from api.common import apply_filters, custom_pagination, get_all_table_records
from api.decorators import jwt_authentication_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.serializers import CustomerSerializer, AppointmentSerializer, SalarySerializer, MembershipSerializer, EmployeeSerializer, InvoiceSerializer
from backend.models import Branch, Customer, Appointment, Salary, Membership, Employee, Invoice, BranchCustomerMobile, SalonDetails, User
from api.constants import *
import pytz

@api_view(['GET','POST','PUT'])
@jwt_authentication_required
def getAllMembership(request, column_name=None, column_value=None):
    if request.method == "GET":
        if column_value is None:
            try:
                request_args = request.GET
                branch_id = request_args.get('branch_id')
                if branch_id in (None, ''):
                    return Response({
                        'message': 'branch_id is required',
                        'status': BAD_REQUEST_STATUS,
                    }, status=BAD_REQUEST_STATUS)
                if branch_id == '-1':
                    all_membership = get_all_table_records(request, Membership)
                else:
                    branch = Branch.objects.get(id=branch_id)
                    all_membership = Membership.objects.filter(branch=branch).order_by('-id')

                final_membership_list = apply_filters(Membership, all_membership, request_args)

                # Call the custom_pagination function to get the paginated items.
                final_membership_list = custom_pagination(request, final_membership_list)

                serializer = MembershipSerializer(final_membership_list, many=True)

                # Return the serialized data in the response
                return Response({
                    "data": {
                        "count": len(final_membership_list),
                        "rows": list(serializer.data)
                    },
                    "message": APIMessages.ALL_MEMBERSHIP_RETRIEVED.value,
                    "status": SUCCESS_STATUS_CODE,
                })
            except (Branch.DoesNotExist, ValueError, TypeError):
                return Response({
                    'message': APIMessages.USER_OR_BRANCH_NOT_EXISTS.value,
                    'status': BAD_REQUEST_STATUS,
                }, status=BAD_REQUEST_STATUS)
            except Exception as e:
                return Response({
                    'message': f'{APIMessages.INTERNAL_SERVER_ERROR.value}: {e}',
                    'status': FAILED_STATUS_CODE,
                }, status=BAD_REQUEST_STATUS)
        else:
            try:
                # Check if column_name is a valid field in the Expense model
                valid_fields = [f.name for f in Membership._meta.get_fields()]
                if column_name not in valid_fields:
                    return Response({"message": f"Invalid column name: {column_name}", "status": 400})

                # Build a dynamic filter using double-underscore notation
                filter_kwargs = {
                    f"{column_name}__exact": column_value} if column_name else {}
                all_coupons = Membership.objects.get(**filter_kwargs)
                
                serializer = MembershipSerializer(all_coupons, many=False)
                # Return the serialized data in the response
                return Response({
                        "data": {
                            "count": 0,
                            "rows": [serializer.data]
                        },
                        "message": APIMessages.MEMBERSHIP_RETRIEVED.value,
                        "status": SUCCESS_STATUS_CODE,
                    })
            except Exception:
                return Response({
                    "message": APIMessages.MEMBERSHIP_NOT_FOUND.value,
                    "status": NOT_FOUND_STATUS,
                })
    elif request.method == 'POST':
        data = request.data
        if not hasattr(data, 'get'):
            return Response({
                'message': 'Invalid JSON body; expected an object',
                'status': BAD_REQUEST_STATUS,
            }, status=BAD_REQUEST_STATUS)

        customer_id = data.get('customer_id')
        selected_branch_id = data.get('branch_id')
        discount_percent = data.get('discount_percent')
        expiry_date = data.get('expiry_date')

        try:
            customer_obj = Customer.objects.get(id=customer_id)
            branch = Branch.objects.get(id=selected_branch_id)
            expiry_date_iso = str(datetime.strptime(expiry_date, '%Y-%m-%dT%H:%M:%S.%fZ'))

            # Now you can use fromisoformat() with the ISO 8601 formatted string
            ist = pytz.timezone('Asia/Kolkata')
            expiry_date_utc = datetime.fromisoformat(expiry_date_iso).replace(tzinfo=ist)
            coupon = Membership(
                customer=customer_obj,
                branch=branch,
                discount_percent=discount_percent,
                expiry_date=expiry_date_utc
            )
            coupon.save()

            return Response({
                "message": APIMessages.MEMBERSHIP_CREATED.value,
                "status": SUCCESS_STATUS_CODE,
            })

        except (Customer.DoesNotExist, Branch.DoesNotExist, TypeError, ValueError, KeyError) as e:
            return Response({
                "message": f'Invalid membership payload: {e}',
                "status": BAD_REQUEST_STATUS,
            }, status=BAD_REQUEST_STATUS)
        except Exception:
            return Response({
                "message": APIMessages.ERROR.value,
                "status": BAD_REQUEST_STATUS,
            }, status=BAD_REQUEST_STATUS)
    elif request.method == 'PUT':
        try:
            id = request.data.get('id', None)
            customer_id = request.data.get('customer_id')
            customer = Customer.objects.get(id=customer_id)
            membership = Membership.objects.get(id=id)
            selected_branch_id = request.data.get('branch_id')
            discount_percent = request.data.get('discount_percent')
            expiry_date = request.data.get('expiry_date')
            status = request.data.get('status')
            
            if membership.branch.id == selected_branch_id and membership.customer == customer:
                ist = pytz.timezone('Asia/Kolkata')
                try:
                    expiry_date = datetime.fromisoformat(expiry_date).replace(tzinfo=ist)
                except:
                    expiry_date = datetime.fromisoformat(expiry_date[:-1]).replace(tzinfo=ist)
                membership.discount_percent = discount_percent
                membership.customer = customer
                membership.expiry_date = expiry_date
                membership.status = status
                membership.save()

                return Response({
                    "message": APIMessages.MEMBERSHIP_UPDATED.value,
                    "status": SUCCESS_STATUS_CODE,
                })
            else:
                return Response({
                    "message": APIMessages.ERROR.value,
                    "status": FAILED_STATUS_CODE,
                })
        except Exception:
            return Response({
                "message": APIMessages.ERROR.value,
                "status": FAILED_STATUS_CODE,
            })
