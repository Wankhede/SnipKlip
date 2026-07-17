import json
from operator import or_
from xml.dom import ValidationErr
from api.constants import FAILED_STATUS_CODE, SUCCESS_STATUS_CODE, APIMessages
from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.serializers import CustomerSerializer, AppointmentSerializer, ServiceSerializer, SalarySerializer, ExpenseSerializer, EmployeeSerializer, InvoiceSerializer
from backend.models import *
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import calendar
import datetime
from django.db.models import Q
import pytz
from django.urls import resolve
import logging
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import status
from backend.views.common.hubspot import createDeal

logger = logging.getLogger(__name__)

def log_error_with_api_endpoint(request, error):
    """
    Log the error with API endpoint information.

    Parameters:
    - request: The Django request object.
    - error: The exception or error message.

    Usage:
    log_error_with_api_endpoint(request, "Error message or exception")
    """
    try:
        resolved_view = resolve(request.path_info)
        api_endpoint = resolved_view.url_name
        logger.error(f"Error in API endpoint '{api_endpoint}': {str(error)}")
    except Exception as e:
        # If there is an error while getting API endpoint information, log a more general message
        logger.error(f"Error in logging API endpoint error: {str(e)}")

def get_user_details(user_id):
    # Retrieve user information
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise ValidationErr("User not found")
    try:
        # Retrieve salon details
        salon_id = SalonDetails.objects.get(user=user).id
        if Branch.objects.filter(salon__id=salon_id):
            selected_branch_id = Branch.objects.filter(salon__id=salon_id).first().id
        else:
            selected_branch_id = None
    except:
        salon_id = selected_branch_id = None
    # Return user, salon, and branch information
    return salon_id, selected_branch_id

@api_view(['POST'])
def signup(request):
    """
    Public signup for salon owners / staff accounts.
    Expected body: email, password, first_name, last_name (optional: mobile, company_name)
    """
    email = (request.data.get('email') or '').strip().lower()
    password = request.data.get('password') or ''
    first_name = (request.data.get('first_name') or '').strip()
    last_name = (request.data.get('last_name') or '').strip()
    mobile = (request.data.get('mobile') or '').strip()
    company_name = (request.data.get('company_name') or '').strip()
    name = (request.data.get('name') or f'{first_name} {last_name}'.strip()).strip()

    if not email or not password:
        return Response({
            'message': 'email and password are required',
            'status': FAILED_STATUS_CODE,
        }, status=status.HTTP_400_BAD_REQUEST)

    if len(password) < 8:
        return Response({
            'message': 'password must be at least 8 characters',
            'status': FAILED_STATUS_CODE,
        }, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
        return Response({
            'message': 'An account with this email already exists',
            'status': FAILED_STATUS_CODE,
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            name=name or email,
            mobile=mobile or None,
            company_name=company_name or None,
            user_status=1,
        )
        group, _ = Group.objects.get_or_create(name='Salon')
        user.groups.add(group)

        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Signup successful',
            'status': SUCCESS_STATUS_CODE,
            'data': {
                'access_token': str(refresh.access_token),
                'user_id': user.id,
                'email': user.email,
                'name': user.get_name(),
                'group': 'Salon',
            },
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        log_error_with_api_endpoint(request, e)
        return Response({
            'message': APIMessages.INTERNAL_SERVER_ERROR.value,
            'status': FAILED_STATUS_CODE,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def login(request):
    access_token = request.data.get('access_token', None)
    id_token_value = request.data.get('id_token', None)

    if id_token_value is not None and access_token is not None:
        try:
            # Verify the id_token
            id_info = id_token.verify_oauth2_token(id_token_value, requests.Request())
        except ValueError as e:
            return Response({'error': 'Invalid id_token'}, status=status.HTTP_401_UNAUTHORIZED)

        # Use the email from id_info for creating or fetching the user
        email = id_info['email']
        name = id_info['name']
        first_name = id_info['given_name']
        last_name = id_info['family_name']
        user, created = User.objects.get_or_create(first_name=first_name, last_name=last_name, name=name, email=email, defaults={'username': email})
        if created:
            createDeal('8000', str(datetime.datetime.now())[:10], user.name)

        # Assuming 'group_name' is the name of the group you want to assign
        group, group_created = Group.objects.get_or_create(name='Salon')

        # Assign the user to the group
        user.groups.add(group)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({'access_token': access_token}, status=status.HTTP_200_OK)

    # If id_token and access_token are not provided, try to authenticate with username and password
    username_or_email = request.data.get('username')
    password = request.data.get('password')

    try:
        # Authenticate user
        user = authenticate(request, username=username_or_email, password=password)

        # Try to create an Admin group if it doesn't exist
        try:
            admin_group = Group.objects.get(name='Admin')
        except Group.DoesNotExist:
            admin_group = Group(name='Admin')
            admin_group.save()

        if user is not None:
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
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
                    'access_token': access_token,
                    "user_id": user.id,
                    "salon_id": salon_id,
                    "branch_id": selected_branch_id,
                    "group": user_group,
                    "subscription_name": subscription_name,
                    "status": True
                },
                "id": user.id,
                "name": user.get_name(),
                "email": user.email,
                'message': 'Login successful',
                'status': 200
            })
            response.set_cookie("username", user.username, max_age=6*60*60)  # 6 hours in seconds
            response.set_cookie("user_id", user.id, max_age=6*60*60)  # 6 hours in seconds
            return response
        else:
            return Response({
                "data": {
                    "status": False

                },
                'message': 'Invalid credentials',
                'status': 401
            })
    except Exception as e:
        log_error_with_api_endpoint(request, e)
        return Response({
            "message": APIMessages.INTERNAL_SERVER_ERROR.value,
            "status": FAILED_STATUS_CODE,
        })  

@api_view(['GET'])
def getServices(request):
    if request.method == "GET":
        branch_id = request.GET['branch_id']

        all_services = Service.objects.filter(branch__id=branch_id)

        serializer = ServiceSerializer(all_services, many=True)

        # Assuming `all_services` is the list of all services
        all_services = serializer.data

        # Create a dictionary representing the service
        service_dict = {
            "service": all_services  # Assuming `all_services` is a list of dictionaries representing services
        }

        # Return the serialized data in the response
        return Response({
            "data": {
                "count": len(all_services),
                "rows": [service_dict]
            },
            "message": "Successfully retrieved all services",
            "status": 200,
        })

@api_view(['GET'])
def getServicesCustom(request):
    if request.method == "GET":
        branch_id = request.GET['branch_id']

        all_services = Service.objects.filter(branch__id=branch_id)

        serializer = ServiceSerializer(all_services, many=True)

        # Assuming `all_services` is the list of all services
        all_services = serializer.data

        # Return the serialized data in the response
        return Response({
            "data": {
                "count": len(all_services),
                "rows": all_services
            },
            "message": "Successfully retrieved all services",
            "status": 200,
        })


@api_view(['GET'])
def getStaff(request):
    if request.method == 'GET':
        branch_id = request.GET['branch_id']
        all_employees = Employee.objects.filter(branch__id=branch_id,status="Active")
        serializer = EmployeeSerializer(all_employees, many=True)
        all_employees = serializer.data

        # Create a dictionary representing the service
        service_dict = {
            "staff_assigned": all_employees  # Assuming `all_employees` is a list of dictionaries representing services
        }

        # Return the serialized data in the response
        return Response({
            "data": {
                "count": len(all_employees),
                "rows": [service_dict]
            },
            "message": "Successfully retrieved all appointment",
            "status": 200,
        })
         

def get_all_table_records(request, TableName):
    records = TableName.objects.all().order_by('-id')
    return records


def custom_pagination(request, data):
    page = request.GET.get('page_number')
    page_size = request.GET.get('page_size')
    # Check if page_number and page_size are provided in the request.
    if page is not None and page_size is not None:
        page = int(page) + 1  # Increment for 1-based page numbering
        page_size = int(page_size)
        paginator = Paginator(data, page_size)

        try:
            items = paginator.page(page)
        except EmptyPage:
            items = paginator.page(paginator.num_pages)
    else:
        # If page_number and page_size are not provided, return all data.
        items = data
    return items




def ist_converted_time(time): 
    # Parse the UTC date string
    try:
        utc_date = datetime.datetime.strptime(str(time), '%Y-%m-%d %H:%M:%S.%f%z')
    except Exception:
        try:
            utc_date = datetime.datetime.strptime(str(time), '%Y-%m-%d %H:%M:%S.%f')
        except Exception:
            utc_date = datetime.datetime.strptime(str(time), '%Y-%m-%d %H:%M:%S%z')
            
    # Define the UTC timezone
    utc_timezone = pytz.timezone('UTC')

    # Convert the datetime object to UTC
    utc_date = utc_date.replace(tzinfo=utc_timezone)

    # Define the Indian Standard Time (IST) timezone
    ist_timezone = pytz.timezone('Asia/Kolkata')

    # Convert the datetime object to IST
    ist_date = utc_date.astimezone(ist_timezone)

    return ist_date


# def apply_filters(table, query, field, values):
#     """
#     Apply dynamic filters to the query based on the field and values.
#     """
#     field_type = table._meta.get_field(field).get_internal_type()

#     if field_type == 'ForeignKey':
#         # For ForeignKey, use __in for a list of values
#         return query.filter(**{f"{field}__in": values})
#     else:
#         # For other fields, use __icontains for a case-insensitive partial match
#         return query.filter(**{f"{field}__icontains": values[0]})


def search_query(table, query, request_args):
    """
    Filter the query based on search value and columns specified in the request arguments.
    
    Parameters:
    - table: The table/model to query.
    - query: The initial query to filter.
    - request_args: The dictionary containing search parameters.
    
    Returns:
    - Filtered query based on search parameters.
    """
    search_value = request_args.get('search_value', [''])[0]
    search_columns = request_args.get('search_columns', '').split(',')

    # Get the list of actual fields (columns) in the table model
    actual_fields = table._meta.get_fields()

    # Collect fields that exist in the table model
    valid_search_columns = [field_name for field_name in search_columns if any(field_name == field.name for field in actual_fields)]
    if search_value and valid_search_columns:
        search_conditions = Q()
        for column in valid_search_columns:
            search_conditions |= Q(**{f"{column}__icontains": search_value})
        query = query.filter(search_conditions).distinct()

    return query

def apply_filters(table, query, request_args):
    """
    Apply dynamic filters to the query based on the field and values in the request arguments.
    
    Parameters:
    - table: The table/model to query.
    - query: The initial query to filter.
    - request_args: The dictionary containing filter parameters.
    
    Returns:
    - Filtered query based on filter parameters.
    """
    search_value_list = request_args.get('search_value', [''])
    search_value = search_value_list[0] if search_value_list else ''
    search_columns = request_args.get('search_columns', '').split(',')

    if not search_value:
        model_fields = [field.name for field in table._meta.get_fields()]
        query_filter = Q()
        
        for key, value in request_args.items():
            if key in model_fields:
                if isinstance(value, list):
                    # Use the __in lookup for lists
                    query_filter &= Q(**{f"{key}__in": value})
                else:
                    # Normal filtering for single values
                    query_filter &= Q(**{key: value})
        
        records = query.filter(query_filter)
        return records
    else:
        if search_columns:
            records = search_query(table, query, request_args)
            return records
        else:
            return query