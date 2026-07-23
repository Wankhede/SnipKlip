from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.serializers import UserSerializer
from backend.models import *
from api.constants import *


@api_view(['GET', 'PUT'])
def get_user_profile(request):
    if request.method == "GET":
        # Accept query param or JSON/body context (frontend often sends user_id in body)
        user_id = request.GET.get('user_id') or request.data.get('user_id')
        if user_id in (None, '', 'null', 'undefined'):
            return Response({
                "message": APIMessages.USER_ID_NOT_FOUND.value,
                "status": BAD_REQUEST_STATUS,
            }, status=BAD_REQUEST_STATUS)
        try:
            user = User.objects.get(id=user_id)
        except Exception:
            return Response({
                "message": APIMessages.USER_ID_NOT_FOUND.value,
                "status": UNAUTHORISED_CODE,
            })

        user_serializer = UserSerializer(user, many=False)
        data = user_serializer.data
        data['dob'] = user.dob
        data['gender'] = user.gender
        data['username'] = user.username
        try:
            subscription = Subscription.objects.filter(user=user).order_by('-end_date').first()
            data['subscription_name'] = (
                subscription.name_of_subscription if subscription else None
            )
        except Exception:
            data['subscription_name'] = None

        return Response({
            'data': data,
            "message": APIMessages.USER_RETIREVED.value,
            "status": SUCCESS_STATUS_CODE,
        })

    elif request.method == "PUT":
        try:
            user = User.objects.get(id=request.user.id)
            first_name = request.data.get('first_name')
            last_name = request.data.get('last_name')
            email = request.data.get('email')
            mobile = request.data.get('mobile')
            gender = request.data.get('gender')
            dob = request.data.get('dob')
            if None in (first_name, last_name, email, mobile, gender, dob):
                return Response({
                    "message": APIMessages.FILL_FIELDS.value,
                    "status": BAD_REQUEST_STATUS,
                })

            try:
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                user.mobile = mobile
                user.gender = gender
                user.dob = dob
                user.save()
                return Response({
                    "message": APIMessages.USER_UPDATED.value,
                    "status": SUCCESS_STATUS_CODE,
                })

            except Exception:
                return Response({
                    "message": APIMessages.FILL_FIELDS.value,
                    "status": BAD_REQUEST_STATUS,
                })

        except Exception:
            return Response({
                "message": APIMessages.USER_NOT_FOUND.value,
                "status": BAD_REQUEST_STATUS,
            })
 

@api_view(['GET', 'PUT'])
def get_user_detail(request):
    if request.method == "GET":
        user_id = request.GET.get('user_id')
        email = request.GET.get('email')
        if not user_id and not email:
            return Response({
                "message": APIMessages.USER_ID_NOT_FOUND.value,
                "status": BAD_REQUEST_STATUS,
            })

        try:
            lookup = {'email': email} if email else {'id': int(user_id)}
            user = User.objects.get(**lookup)
        except (User.DoesNotExist, TypeError, ValueError):
            return Response({
                "message": APIMessages.USER_ID_NOT_FOUND.value,
                "status": UNAUTHORISED_CODE,
            })

        group_names = list(user.groups.values_list('name', flat=True))
        user_group = group_names[0] if group_names else ""
        salon = None
        salon_id = None
        selected_branch_id = None
        subscription_name = "NULL"

        if user.is_superuser or "Admin" in group_names:
            salon_id = -1
            selected_branch_id = -1
            user_group = "Admin"
            subscription_name = "Premium"
        elif user_group == "Manager":
            branch = (
                Branch.objects.select_related('salon')
                .filter(manager=user)
                .first()
            )
            if branch:
                salon = branch.salon
                salon_id = branch.salon_id
                selected_branch_id = branch.id
        elif user_group == "Staff":
            employee = (
                Employee.objects.select_related('branch__salon')
                .filter(user=user, status="Active")
                .first()
            )
            if employee and employee.branch:
                salon = employee.branch.salon
                salon_id = employee.branch.salon_id
                selected_branch_id = employee.branch_id
        elif user_group in ("Salon", "DemoGroup"):
            salon = SalonDetails.objects.filter(user=user).first()
            if salon:
                salon_id = salon.id
                selected_branch_id = (
                    Branch.objects.filter(salon=salon)
                    .values_list('id', flat=True)
                    .first()
                )

        if salon:
            subscription_name = (
                Subscription.objects.filter(
                    salon=salon,
                    paid=True,
                    end_date__gt=timezone.now(),
                )
                .values_list('name_of_subscription', flat=True)
                .first()
                or "NULL"
            )

        return Response({
            "data": {
                "user_id": user.id,
                "salon_id": salon_id,
                "branch_id": selected_branch_id,
                "group": user_group,
                "subscription_name": subscription_name,
            },
            'message': 'successful',
            'status': 200
        })
    elif request.method == "PUT":
        try:
            data = request.data
            user = User.objects.get(id=data['user_id'])
            first_name = data['first_name']
            last_name = data['last_name']
            email = data['email']
            mobile = data['mobile']
            gender = data['gender']
            dob = data['dob']

            try:
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                user.mobile = mobile
                user.gender = gender
                user.dob = dob
                user.save()
                return Response({
                        "message": APIMessages.USER_UPDATED.value,
                        "status": SUCCESS_STATUS_CODE,
                    })
        
            except Exception:
                return Response({
                                "message": APIMessages.ERROR.value,
                                "status": BAD_REQUEST_STATUS,
                                })
        except Exception:
                return Response({
                                "message": APIMessages.USER_NOT_FOUND.value,
                                "status": BAD_REQUEST_STATUS,
                                })
            
    return Response({})

@api_view(['POST'])
def change_password(request):
    if request.method == "POST":
        data = request.data
        old_password = data['old']
        new_password = data['password']
        confirm_password = data['confirm']
        user_id = data['user_id']


        if not User.objects.filter(id=user_id):
            return Response({
                    'message':'User Does Not Matched..!',
                    'status': 500
            })

        if new_password == "" or confirm_password == "":
            return Response({
                    'message':'Please fill Field the Fields Correctly',
                    'status': 500
            })
        
        user = User.objects.get(id=user_id)
        check_pass = user.check_password(old_password)

        if not check_pass:
            return Response({
                'message':'Wrong Password...!',
                'status': 500
            })
        
        if new_password == confirm_password:
            user.set_password(new_password)
            user.save()
            return Response({
                'message':'Successfully Change The Password',
                'status': 200
            })
        else:
                return Response({
                    'message':'Password Does Not Matched',
                    'status': 500
                })

