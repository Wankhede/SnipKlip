from datetime import timedelta
from api.views.hubspot import createDeal
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from api.views.mail import send_joining_mail
from backend.models import *
from django.contrib.auth.models import Group
from api.serializers import SalonDetailsSerializer, BranchSerializer, ServiceSerializer
import random
import string
from api.constants import *
from django.conf import settings

# API to add a new branch
@api_view(['POST'])
def add_branch_api(request):
    if request.method == "POST":
        data = request.data
        basic_data = data.get('basicData', {})
        salon_data = data.get('salonData', {})
        
        # Retrieving user
        try:
            user_id = data.get('user_id')
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'message': APIMessages.USER_NOT_FOUND.value,
                'status': 'FAILED'
            })

        # Extracting data from request
        branch_name = basic_data.get('salonName')
        salon_type = salon_data.get('salonType')
        state = basic_data.get('state')
        city = basic_data.get('city')
        pincode = basic_data.get('pinCode')
        contact_no = basic_data.get('contactNumber')
        address = basic_data.get('address')
        locality = basic_data.get('locality')
        lat = basic_data.get('latitude', 0.0)
        lon = basic_data.get('longitude', 0.0)
        seat_no = salon_data.get('NoOfSeat')
        staff_no = salon_data.get('NoOfStaff')
        
        # Default description if not provided
        salon_desc = """Step into our salon and experience the most contemporary hair cutting, coloring, and designing techniques in demand today. Our talented team of devoted stylists has dedicated their time by continuing their education to ensure you have the latest up to date style. Come in and enjoy the most modern salon. Consultations are always complimentary.<br><br>

        Palace Beauty Salon is known not only for its skilled seasoned stylists but also for its superior customer service and satisfaction guarantee. Mora, our owner, feels that the most important aspect of a hair service is the consultation. A one-on-one discussion of ideas, past experiences, and expectations is an integral part of the Palace Beauty service.<br><br>

        Another important feature of the experience is that clients are taught how to recreate their look at home. Appropriate techniques, product, and application are explained with every service provided at Palace Beauty Salon. The hair service itself is executed by impassioned, well-experienced, highly trained professionals who are always thirsty for the latest techniques and trends.
        """

        # Creating or updating the branch
        try:
            salon, _ = SalonDetails.objects.get_or_create(user=user)
            branch = Branch.objects.create(
                branch_name=branch_name,
                salon=salon,
                address=address,
                owner_contact_no=contact_no,
                city=city,
                state=state,
                pincode=pincode,
                exp_desc=salon_desc,
                lat=lat,
                locality=locality,
                lng=lon,
                total_seat=seat_no,
                total_staff=staff_no,
                salon_type=salon_type
            )
            # Only seed a trial when the salon has no active paid subscription.
            current_datetime = timezone.now()
            has_active_subscription = Subscription.objects.filter(
                salon=salon,
                paid=True,
                end_date__gt=current_datetime,
            ).exists()
            if not has_active_subscription:
                Subscription.objects.create(
                    name_of_subscription="PREMIUM",
                    salon=salon,
                    user=user,
                    start_date=current_datetime,
                    end_date=current_datetime + timedelta(days=7),
                    credit_balance=0,
                    type="MONTHLY",
                    paid=True,
                    order_id=f"DEMO_for_salon--->{salon.name}____{salon.id}",
                )
            return Response({
                'data': {
                    'branch_id': branch.id,
                },
                'message': APIMessages.SALON_REGISTERED.value,
                'status': SUCCESS_STATUS_CODE
            })
        except Exception as e:
            return Response({
                'message': str(e),
                'status': 'FAILED'
            })

    else:
        return Response({
            "message": APIMessages.METHOD_NOT_ALLOWED.value
        }, status=METHOD_NOT_ALLOWED)

# API to add a new salon
@api_view(['POST'])
def add_salon_api(request):
    if request.method == "POST":
        # Extracting data from the request
        salon_name = request.data.get('name')
        owner_name = request.data.get('owner_name')
        contact_no = request.data.get('contact_no')
        personal_email = request.data.get('owner_email')
        password = request.data.get('password')
        re_password = request.data.get('confirmPassword')

        # Checking if passwords match
        if password != re_password:
            return Response({
                'message': APIMessages.PASSWORD_MISMATCH.value,
                'status':FAILED_STATUS_CODE
            })

        # Checking if username already exists
        if User.objects.filter(username=owner_name).exists():
            return Response({
                    'message':APIMessages.USENAME_ALREADY_TAKEN.value,
                    'status':FAILED_STATUS_CODE
                })

        # Checking if email already exists
        if User.objects.filter(email=personal_email).exists():
            return Response({
                    'message':APIMessages.OWNER_EMAIL_ALREADY_TAKEN.value,
                    'status':FAILED_STATUS_CODE
                })

        # Checking if mobile number already exists
        if User.objects.filter(mobile=contact_no).exists() or SalonDetails.objects.filter(contact_no=contact_no).exists():
            return Response({
                    'message':APIMessages.CONTACT_ALREADY_TAKEN.value,
                    'status':FAILED_STATUS_CODE
                })

        # Creating User
        first_name = owner_name.split(" ")[0]
        last_name = owner_name.split(" ")[1] if len(owner_name.split(" ")) >= 2 else ''
        user = User(
            username=owner_name,
            first_name=first_name,
            last_name=last_name,
            name=first_name + ' ' + last_name,
            password=make_password(password),
            email=personal_email,
            mobile=contact_no
        )
        user.save()

        # Adding user to the Salon group
        try:
            group = Group.objects.get(name='Salon')
        except Group.DoesNotExist:
            group = Group(name="Salon")
            group.save()
        user.groups.add(group)

        # Creating Customer
        customer = Customer(
            user=user,
            name=first_name + ' ' + last_name,
            email=user.email
        )
        customer.save()

        # Creating Salon
        reg_no = ''.join(random.choice(string.ascii_uppercase + string.digits) for i in range(15))
        salon = SalonDetails(
            user=user,
            name=salon_name,
            email="",
            reg_no=reg_no,
            contact_no=contact_no,
            owner_name=owner_name,
            owner_email=personal_email
        )
        salon.save()

        if settings.SERVER == 99:
            # send_joining_mail(salon.owner_email,salon.name,salon.owner_name)

            # Call function to create a deal
            createDeal('8000', str(datetime.now())[:10], user.name)

        return Response({"message": APIMessages.SALON_REGISTERED.value,'status':SUCCESS_STATUS_CODE})

    else:
        return Response({"message": APIMessages.METHOD_NOT_ALLOWED.value,'status':METHOD_NOT_ALLOWED}, status=METHOD_NOT_ALLOWED)

@api_view(['GET'])
def getSalon(request):
    try:
        # Extracting data from request
        branch_id = request.GET.get('branch_id')
        salon_id = request.GET.get('salon_id')

        if branch_id in (None, '') or salon_id in (None, ''):
            return Response({
                "message": APIMessages.INVALID_PARAMETERS.value,
                "status": FAILED_STATUS_CODE,
            })

        # Handling scenario to retrieve all salons
        if int(branch_id) == -1 and int(salon_id) == -1:
            salons = SalonDetails.objects.all()
            serializer = SalonDetailsSerializer(salons, many=True)

            return Response({
                "data": {
                    "rows": serializer.data
                },
                "message": APIMessages.ALL_SALON_DETAIL_RETRIEVED.value,
                "status": SUCCESS_STATUS_CODE,
            })

        # Handling scenario for invalid parameters
        else:
            return Response({
                "message": APIMessages.INVALID_PARAMETERS.value,
                "status": FAILED_STATUS_CODE,
            })

    # Handling exceptions
    except (ValueError, TypeError):
        return Response({
            "message": APIMessages.INVALID_PARAMETERS.value,
            "status": FAILED_STATUS_CODE,
        })

    except Exception as e:
        return Response({
            "message": str(e),
            "status": FAILED_STATUS_CODE,
        })
    
@api_view(['GET'])
def getBranch(request):
    try:
        # Extracting data from request
        branch_id = request.GET.get('branch_id')
        salon_id = request.GET.get('salon_id')

        # Handling scenario to retrieve all branches
        if branch_id == '-1' and salon_id == '-1':
            branches = Branch.objects.all()
            serializer = BranchSerializer(branches, many=True)

            return Response({
                "data": {
                    "rows": serializer.data
                },
                "message": APIMessages.ALL_BRANCH_DETAIL_RETRIEVED.value,
                "status": SUCCESS_STATUS_CODE,
            })

        # Handling scenario to retrieve specific branch
        else:
            branch = Branch.objects.get(id=branch_id, salon_id=salon_id)
            serializer = BranchSerializer(branch)

            return Response({
                "data": serializer.data,
                "message": APIMessages.BRANCH_DETAIL_RETRIEVED.value,
                "status": SUCCESS_STATUS_CODE,
            })

    # Handling exceptions
    except Branch.DoesNotExist:
        return Response({
            "message": APIMessages.BRANCH_NOT_FOUND.value,
            "status": FAILED_STATUS_CODE,
        })

    except Exception as e:
        return Response({
            "message": str(e),
            "status": FAILED_STATUS_CODE,
        })
    
    