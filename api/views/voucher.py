from datetime import datetime, timedelta, timezone
from api.common import apply_filters, custom_pagination, get_all_table_records
from api.decorators import jwt_authentication_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.serializers import CustomerSerializer, AppointmentSerializer, SalarySerializer, CouponCodeSerializer, EmployeeSerializer, InvoiceSerializer
from backend.models import Branch, Customer, Appointment, Salary, CouponCode, Employee, Invoice, BranchCustomerMobile, SalonDetails, User
from api.constants import *
import pytz

@api_view(['GET','POST','PUT'])
@jwt_authentication_required
def getAllCouponCodes(request, column_name=None, column_value=None):
    if request.method == "GET":
        if column_value is None:
            branch_id = request.GET['branch_id']
            request_args = request.GET
            if branch_id == '-1':
                all_coupons = get_all_table_records(request, CouponCode)
            else:
                branch = Branch.objects.get(id=branch_id)
                all_coupons = CouponCode.objects.filter(branch=branch).order_by('-id')

            final_coupons_list = apply_filters(CouponCode, all_coupons, request_args)
    
            # Call the custom_pagination function to get the paginated items.
            final_coupons_list = custom_pagination(request, final_coupons_list)            

            serializer = CouponCodeSerializer(final_coupons_list, many=True)

            # Return the serialized data in the response
            return Response({
                "data": {
                    "count": len(final_coupons_list),
                    "rows": list(serializer.data)
                },
                "message": APIMessages.ALL_EXPENSE_RETRIEVED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        else:
            try:
                # Check if column_name is a valid field in the Expense model
                valid_fields = [f.name for f in CouponCode._meta.get_fields()]
                if column_name not in valid_fields:
                    return Response({"message": f"Invalid column name: {column_name}", "status": 400})

                # Build a dynamic filter using double-underscore notation
                filter_kwargs = {
                    f"{column_name}__exact": column_value} if column_name else {}
                all_coupons = CouponCode.objects.get(**filter_kwargs)
                
                serializer = CouponCodeSerializer(all_coupons, many=False)
                # Return the serialized data in the response
                return Response({
                        "data": {
                            "count": 0,
                            "rows": [serializer.data]
                        },
                        "message": APIMessages.COUPON_RETRIEVED.value,
                        "status": SUCCESS_STATUS_CODE,
                    })
            except Exception:
                return Response({
                    "message": APIMessages.COUPON_NOT_FOUND.value,
                    "status": NOT_FOUND_STATUS,
                })
    elif request.method == 'POST':
        selected_branch_id = request.data.get('branch_id')
        coupon_code = request.data.get('coupon_code')
        discount_percent = request.data.get('discount_percent')
        expiry_date = request.data.get('expiry_date')
        available_count = request.data.get('available_count')

        try:
            branch = Branch.objects.get(id=selected_branch_id)
            expiry_date_iso = datetime.strptime(expiry_date, '%b %d, %Y').isoformat()

            # Now you can use fromisoformat() with the ISO 8601 formatted string
            ist = pytz.timezone('Asia/Kolkata')
            expiry_date_utc = datetime.fromisoformat(expiry_date_iso).replace(tzinfo=ist)
            coupon = CouponCode(
                branch = branch,
                coupon_code = coupon_code,
                discount_percent = discount_percent,
                expiry_date = expiry_date_utc,
                available_count = available_count
            )
            coupon.save()

            return Response({
                "message": APIMessages.COUPON_CREATED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        
        except Exception:
            return Response({
                "message": APIMessages.ERROR.value,
                "status": FAILED_STATUS_CODE,
            })
    elif request.method == 'PUT':
        id = request.data.get('id', None)
        coupon = CouponCode.objects.get(id=id)
        selected_branch_id = request.data.get('branch_id')
        coupon_code = request.data.get('coupon_code')
        discount_percent = request.data.get('discount_percent')
        expiry_date = request.data.get('expiry_date')
        available_count = request.data.get('available_count')
        status = request.data.get('status')
        if coupon.branch.id == selected_branch_id:
            expiry_date = datetime.strptime(str(expiry_date), '%b %d, %Y').replace(tzinfo=timezone.utc)
            coupon.discount_percent = discount_percent
            coupon.coupon_code = coupon_code
            coupon.expiry_date = expiry_date
            coupon.available_count = available_count
            coupon.status = status
            coupon.save()

            return Response({
                "message": APIMessages.COUPON_UPDATED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        else:
            return Response({
                "message": APIMessages.ERROR.value,
                "status": FAILED_STATUS_CODE,
            })

@api_view(['POST'])
def checkCouponCode(request):
    if request.method == "POST":
        try:
            data = request.data
            print(data)
            branch = Branch.objects.get(id=data['branch_id'])
            coupon_code = data['coupon_code']
            actual_amount = data['actual_amount']

            # coupon_expiry_datetime = datetime(str(coupon.expiry_date).split("+")[0])
            current_time = datetime.now()
            
            coupon = CouponCode.objects.get(coupon_code = coupon_code,branch=branch)
            if coupon and coupon.available_count >= 1 and str(coupon.expiry_date) >= str(current_time):
                if coupon.minimum_value_amount > actual_amount:
                    return Response({
                        "message": str(APIMessages.LIMIT_VALUE.value) + str(coupon.minimum_value_amount) + ' For Availing Coupon',
                        "status": UNAUTHORISED_CODE,
                    }) 
                else:
                    return Response({
                            "message": APIMessages.VALID_COUPON.value,
                            'discount_percentange':int(coupon.discount_percent),
                            "status": SUCCESS_STATUS_CODE,
                        }) 
            else:
                return Response({
                        "message": APIMessages.INVALID_COUPON.value,
                        "status": FAILED_STATUS_CODE,
                    }) 
        except Exception:
            return Response({
                        "message": APIMessages.INVALID_COUPON.value,
                        "status": FAILED_STATUS_CODE,
                    }) 
