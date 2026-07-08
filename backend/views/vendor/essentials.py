import random
from django.http import JsonResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from backend.views.common.conditions import in_group,group_match
from backend.models import *
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist, ValidationError

def get_service_details(request):
    if request.method == 'GET':
        service = request.GET.get('service')  # Get the service from the request parameters

        try:
            service_obj = Service.objects.get(name=service)  # Query the Service model for the given service
            response = {
                'name': service_obj.name,
                'rate': float(service_obj.price)
            }
            return JsonResponse(response)  # Return the response as JSON
        except Service.DoesNotExist:
            return JsonResponse({'error': 'Service not found'}, status=404)  # Handle case when service is not found
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)  # Handle invalid request method

def get_stylist_details(request):
    try:
        staff = Employee.objects.all()  # Query the Service model for the given service
        results = [{'id': c.id, 'name': str(c.user.first_name)} for c in staff]
        return JsonResponse({'items': results})
    except Service.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)  # Handle case when service is not found

def create_username(first_name, last_name):
    # Generate a random 3-digit number
    random_number = random.randint(100, 999)
    # Combine the first name, last name, and random number to create the username
    username = first_name.lower() + "." + last_name.lower() + str(random_number)
    return username

def search_customers(request):
    if request.method == 'GET':
        search_term = request.GET.get('term')
        customers = Customer.objects.filter(username__icontains=search_term, status='Active').values_list('username', flat=True)
        return JsonResponse(list(customers), safe=False)

def search_services(request):
    if request.method == 'GET':
        search_term = request.GET.get('term')
        customers = Service.objects.filter(name__icontains=search_term).values_list('name', flat=True)
        return JsonResponse(list(customers), safe=False)

def customer_search(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'items': []})
    try:
        pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
    except Exception as e:
        # Handle any exceptions that may occur while retrieving user information
        return Response({'message': 'An error occurred while retrieving user information.'}, status=500)

    customers = Customer.objects.filter(username__icontains=query,is_active=True)
    user = list(customers.values_list('user',flat=True))
    results = [{'id':c.user.id,'mobile':str(BranchCustomerMobile.objects.get(customer_user=c,branch=selected_branch).mobile), 'name': str(c.username)} for c in customers]
    return JsonResponse({'items': results,})







# total_entries = len(all_user)
# page = request.GET.get('page')
# if page == "" or page == 1 or page == None:
#     page = 1
# else:
#     page = page
# paginator = 10 #how much row you want to show

# all_user = list(all_user)[(paginator*(int(page)-1)):paginator*int(page)]
# start_index = (paginator*(int(page)-1))+1
# end_index = paginator*int(page)
# current_page = math.ceil(end_index / paginator)
# previous_page = current_page - 1
# next_page = current_page + 1
# num_pages = math.ceil((total_entries/paginator))

# if current_page >= 11 and current_page < (math.ceil((total_entries/paginator)+1)-12):
#     #all index (prevous 6 from current & after 6 from current)
#     page_list = [x for x in range(current_page-6,current_page+6)]

#     for i in range(math.ceil((total_entries/paginator)+1)-6,math.ceil(total_entries/paginator)+1):
#         page_list.append(i)

#     page_split = (current_page + 5)

# elif current_page >= math.ceil(((total_entries/paginator)+1)-12):
#     page_list = [x for x in range(current_page-(math.ceil((total_entries/paginator)+1)-current_page),current_page-4)]
    
#     for i in range(current_page,current_page+(math.ceil((total_entries/paginator)+1)-current_page)):
#         page_list.append(i)

#     page_split = (current_page - 5)

# elif current_page <= 11:
#     page_list = [x for x in range(current_page-(current_page-1),current_page+4)]
#     for i in range(math.ceil((total_entries/paginator)+1)-10,math.ceil(total_entries/paginator)+1):
#         page_list.append(i)
#     page_split = (current_page+4) -1 






def my_view(request, selected_entries):
    paginator = Paginator(selected_entries, 8)  # Show 8 entries per page
    entries = paginator.get_page(8)
    start_index = entries.start_index()
    end_index = entries.end_index()
    total_entries = paginator.count
    current_page = entries.number
    num_pages = paginator.num_pages
    page_list = paginator.page_range
    return {
        'entries': entries,
        'start_index': start_index,
        'end_index': end_index,
        'total_entries': total_entries,
        'current_page': current_page,
        'num_pages': num_pages,
        'page_list': page_list,
    }

# helper function to check if user belongs to a group
def group_match(group_name, request):
    if request.user.groups.filter(name=group_name).exists():
        return True
    return False

# function to get the user ID based on the user's group
def userObj(request):
    if group_match('Admin', request):
        try:
            pk = int(request.GET.get('pk', ''))
        except ValueError:
            raise ValidationError("Invalid user ID")
    else:
        pk = request.user.pk
    return pk

# function to get the user's ID, object, and admin status
def get_pk(request):
    try:
        user_id = userObj(request)
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise ValidationError("User not found")
    
    if group_match('Admin', request):
        try:
            pk_id = int(request.GET.get('pk', ''))
            user = User.objects.get(pk=pk_id)
        except ValueError:
            raise ValidationError("Invalid user ID")
        except User.DoesNotExist:
            raise ValidationError("User not found")
        is_admin = 'true'
    else:
        pk_id = 0
        is_admin = 'false'
    return pk_id, user, is_admin

def get_user_salon_branch_details(request):
    try:
        # Retrieve user information
        pk_id, user, is_admin = get_pk(request)
    except ObjectDoesNotExist as e:
        # Handle exception when user does not exist
        return Response({'message': 'User not found.'}, status=404)
    except Exception as e:
        # Handle any other exception that may occur while retrieving user information
        raise APIException('An error occurred while retrieving user information.') from e

    try:
        # Retrieve salon details
        salon = SalonDetails.objects.get(user=user)
    except ObjectDoesNotExist as e:
        # Handle exception when salon or user does not exist
        return Response({'message': 'Salon or user not found.'}, status=404)
    branches = Branch.objects.filter(salon=salon)
    # Determine branch based on user permissions
    if group_match('Salon', request):
        if 'branch' in request.GET:
            group = "Salon"
            try:
                branch_id = int(request.GET.get('branch', ''))
                selected_branch = Branch.objects.get(pk=branch_id)
            except ValueError:
                # Handle exception when branch ID is invalid
                raise ValidationError("Invalid branch ID")
            except Branch.DoesNotExist:
                # Handle exception when branch does not exist
                raise ValidationError("Branch not found")
        else:
            group = "NA"
            # Get all branches for the salon
            selected_branch = Branch.objects.filter(salon=salon).first()
    elif group_match('Manager', request):
        group = "Manager"
        # Get branches managed by the user's salon
        selected_branch = Branch.objects.filter(salon=salon, manager=user)
    else:
        group = 'NA'
        # Get all branches for the user's salon
        selected_branch = Branch.objects.filter(salon=salon).first()
    
    # Return user, salon, and branch information
    return pk_id, user, is_admin, salon, selected_branch, branches