from django.shortcuts import render, redirect
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from backend.models import *
from django.contrib import messages
import random
import string
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from backend.views.common.conditions import group_match
from backend.views.common.pagination import get_pagination
from backend.views.vendor.essentials import get_user_salon_branch_details, group_match

class Customers(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/customers.html'
    queryset = SalonDetails.objects.filter()
    permission_classes = [IsAuthenticated]
    def get(self, request):

        # Check user permissions
        if not group_match('Admin', request) and not group_match('Salon', request) and not group_match('Manager', request):
            return redirect('/')

        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)

        
        # Initialize lists to hold the data for each customer
        total_number_of_bookings = []
        last_visited = []
        unique_customer = []
        customer = []
        mobile_numbers = []
        notes = []


        #matched Mobile Number for this Branch:-
        branch_mobile = BranchCustomerMobile.objects.filter(branch=selected_branch)


        #Data of All user of selected Branch even if User had never visited Salon... But User is Related to Branch Somehow..!
        all_user = Customer.objects.filter(mobile_number__in=branch_mobile, status='Active')
        
        ###################### Pagination ###################
        paginated_query = get_pagination(request,all_user,10)
        ###############################

        for all_user in paginated_query['all_data']:
            customer.append(all_user.user.id)

        customer = set(customer)
        
        # Loop through each customer and get their data
        for c in customer:
            #Get User
            customer_user = User.objects.get(id=c)

            # Get the customer's user object and add it to the list of unique customers
            unique_customer.append(Customer.objects.get(user=customer_user))

            # get Mobile number of Cutsomer's User object
            mobile_number = BranchCustomerMobile.objects.get(customer_user=Customer.objects.get(user=customer_user),branch=selected_branch)
            mobile_numbers.append(mobile_number.mobile)
            notes.append(mobile_number.note)
            
            # Get the total number of bookings for the customer
            total_number_of_bookings.append(len(Appointment.objects.filter(user=customer_user, branch=selected_branch)))
            

            # Get the date of the customer's last visit
            visited_date = list(Appointment.objects.filter(user=customer_user, branch=selected_branch, booking_status="Availed").values_list('date', flat=True))
            try:
                last_visited.append(visited_date[-1])
            except IndexError:
                # If the customer has no visits, add a placeholder value to the last_visited list
                last_visited.append("--------")

        
        # Reverse the lists so that they are in descending order of data
        unique_customer.reverse()
        total_number_of_bookings.reverse()
        last_visited.reverse()
        mobile_numbers.reverse()
        notes.reverse()

        last_visited_set = list(set(last_visited))
        

        # Create a context dictionary with all of the data needed for the template
        context = {'num_pages':paginated_query['num_pages'],
                   'next_page':paginated_query['next_page'],
                   'previous_page':paginated_query['previous_page'],
                   'page_split':paginated_query['page_split'],
                   'page_list':paginated_query['page_list'],
                   'start_index':paginated_query['start_index'],
                   'current_page':paginated_query['current_page'],
                   'end_index':paginated_query['end_index'],
                   'total_entries':paginated_query['total_entries'],
                   'mobile_number':mobile_numbers,
                   'note':notes,
                   'customer':unique_customer,
                   'total_number_of_bookings':total_number_of_bookings,
                   'last_visited':last_visited,
                   'branches':branches,
                   'pk_id':pk_id,
                   'user':user,
                   'is_admin':is_admin,
                   'selected_branch':selected_branch,
                   'last_visited_set':last_visited_set
                   }

        # context = {**context, **data}
        return Response(context)

    def post(self, request):
        return Response({'message': ''})



class AddCustomers(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/add-customers.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.filter()


    def get(self, request):
        if group_match('Salon',request) == False:
            return redirect('/')
        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)
        
        return Response({'key': 'Add Customers', 'data': '', 'page': '', 'pages': '',
                        'pk_id': pk_id,
                        'user': user,
                        'is_admin': is_admin,
                        'selected_branch': selected_branch,
                        'branches':branches})

    def post(self, request):
        if not group_match('Salon',request) and not group_match('Manager',request) and not group_match('Admin',request):
            return redirect('/')
    
        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)
        

        # Get the form data from the request
        username = request.POST.get('username')
        first_name = username.split(" ")[0]
        last_name = username.split(" ")[-1]
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        characters = string.ascii_letters + string.digits
        random_string = ''.join(random.choices(characters, k=8))
        password = make_password(random_string)

        try:
            if User.objects.filter(username = username):
                messages.error(request,"This Username Already Exists")
                return redirect('/add-customers')
            if User.objects.filter(mobile=mobile,email = email):
                messages.error(request,"This Mobile Number & Email Id (Both) Already Exists")
                return redirect('/add-customers')
            if User.objects.filter(email=email):
                messages.error(request,"This Email Id Already Exists")
                return redirect('/add-customers')
            if User.objects.filter(mobile=mobile):
                messages.error(request,"This Mobile Number Already Exists")
                return redirect('/add-customers')
            
            user = User(username=username,first_name=first_name,last_name=last_name,email=email,mobile=mobile)
            user.save()
            user.set_password = password
            user.save()
            my_group = Group.objects.get(name='Customer') 
            my_group.user_set.add(user)
            user.save()

            customer = Customer(user=user,
                                username=username,
                                email=email)
            customer.save()

            branch_mobile = BranchCustomerMobile(branch = selected_branch,mobile=mobile,customer_user=customer)
            branch_mobile.save()

            customer.mobile_number.add(branch_mobile)
            customer.save()

            messages.success(request,"Successfully added Customer")
            return redirect('/add-customers')

        except Exception:
            messages.error(request,"Failed to added Customer")
            return redirect('/add-customers')
            
    



class CustomerDetail(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/customer-detail.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.filter()

    def get(self, request,user_id,user_name):
        if not group_match('Admin', request) and not group_match('Salon', request) and not group_match('Manager', request):
            return redirect('/')

        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)

        try:
            customer_user = User.objects.get(id=user_id,username=user_name)
            customer = Customer.objects.get(user=customer_user)
        except Exception:
            return render(request,'error.html')
        
        if group_match('Manager',request) == True:
            order = Appointment.objects.filter(user=customer_user,branch=selected_branch)
        else:
            order = Appointment.objects.filter(user=customer_user)

        context = {
                    'user':customer,
                    'order':order,
                    'pk_id': pk_id,
                    'is_admin': is_admin,
                    'selected_branch': selected_branch,
                    'branches':branches,
                    'branches':branches
                  }
        return Response(context)
        
    def post(self, request):
        return Response({'message': ''})