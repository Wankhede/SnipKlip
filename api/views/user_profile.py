from api.common import get_user_details
from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.serializers import UserSerializer
from backend.models import *
from api.constants import *


@api_view(['GET', 'PUT'])
def get_user_profile(request):
    if request.method == "GET":
        user_id = request.GET['user_id']
        try:
            user = User.objects.get(id=user_id)
        except Exception:
            return Response({
                "message": APIMessages.USER_ID_NOT_FOUND.value,
                "status": UNAUTHORISED_CODE,
            })
        
        user_serializer = UserSerializer(user,many=False)
        data = user_serializer.data
        data['dob'] = user.dob
        data['gender'] = user.gender
        data['username'] = user.username
        try:
            subscription = Subscription.objects.get(user=user)
            data['subscription_name'] = subscription.name_of_subscription
        except Exception as e:
            # Handle the case where the subscription does not exist for the user
            data['subscription_name'] = None
        
        return Response({
                'data':data,
                "message": APIMessages.USER_RETIREVED.value,
                "status": SUCCESS_STATUS_CODE,
            })
    
    elif request.method == "PUT":
        try:
            print(request.data)
            user = User.objects.get(id=request.user.id)
            first_name = request.data['first_name']
            last_name = request.data['last_name']
            email = request.data['email']
            mobile = request.data['mobile']
            gender = request.data['gender']
            dob = request.data['dob']

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
        data = request.GET
        if data.get('user_id'):
            user_id = int(data.get('user_id')) if data.get('user_id') is not None else None
        if data.get('email'):
            email = data.get('email', None) if data.get('email') is not None else None
            user_id = User.objects.get(email=email).id
        if user_id is not None:
            salon_id, selected_branch_id = get_user_details(user_id)
            if selected_branch_id == False:
                selected_branch_id = None
                subscription_name = "NULL"
            try:
                user = User.objects.get(id=user_id)
            except Exception:
                return Response({
                    "message": APIMessages.USER_ID_NOT_FOUND.value,
                    "status": UNAUTHORISED_CODE,
                })
            # Try to create an Admin group if it doesn't exist
            try:
                admin_group = Group.objects.get(name='Admin')
            except Group.DoesNotExist:
                admin_group = Group(name='Admin')
                admin_group.save()

            if user is not None:
                if admin_group in user.groups.all():
                    salon_id = -1
                    selected_branch_id = -1
                    user_group = "Admin"
                    subscription_name = 'Premium'
                else:
                    user_group = user.groups.first().name
                    salon_id, selected_branch_id = get_user_details(user.id)
                    if selected_branch_id is None:
                        subscription_name = "NULL"
                    else:
                        if user_group == "Manager":
                            manager_of_branch = Branch.objects.get(manager=user)
                            salon = manager_of_branch.salon
                            selected_branch_id = manager_of_branch.id
                            salon_id = salon.id
                        elif user_group == "Staff":
                            employee = Employee.objects.get(user=user,status="Active")
                            selected_branch_id = employee.branch.id
                            salon_id = employee.branch.salon.id
                        elif user_group == "Salon":
                            salon = SalonDetails.objects.get(user=user)
                            selected_branch_id = Branch.objects.filter(salon=salon).first().id
                            salon_id = salon.id
                        elif user_group == "DemoGroup":
                            salon = SalonDetails.objects.get(user=user)
                            selected_branch_id = Branch.objects.filter(salon=salon).first().id
                            salon_id = salon.id
                        else:
                            pass
                        current_datetime = timezone.now()
                        if Subscription.objects.filter(salon=salon,paid=True,end_date__gt=current_datetime):
                            subscription_name = Subscription.objects.get(salon=salon,paid=True,end_date__gt=current_datetime).name_of_subscription
                        else:
                            subscription_name = "NULL"
            response = Response({
                "data": {
                    "user_id": user_id,
                    "salon_id": salon_id,
                    "branch_id": selected_branch_id,
                    "group": user_group,
                    "subscription_name": subscription_name,
                },
                'message': 'successful',
                'status': 200
            })
            return response
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

