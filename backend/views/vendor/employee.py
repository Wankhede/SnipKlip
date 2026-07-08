import calendar
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.paginator import Paginator
from django.db.models import Avg, Sum
from django.db.models.functions import TruncDay
from django.http import Http404, HttpResponseBadRequest, JsonResponse,HttpResponse
from django.shortcuts import render, redirect
from django.core import mail
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import date,timedelta
from backend.models import *
import operator
import string
import json
from datetime import datetime, date, timedelta
from backend.views.common.conditions import in_group, group_match
from backend.views.message.mail import send_confirmation_mail
from random import randint, randrange
from backend.views.bookings.customer_side.order import TIME_RANGE, email_send, calendar_event, get_credentials
from backend.views.message.sms import sms
from backend.views.message.whatsapp import whatsApp
from backend.views.vendor.essentials import create_username, get_pk, get_user_salon_branch_details, customer_search, group_match, my_view
from django.db.models.functions import TruncDay
from rest_framework.exceptions import APIException
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404
from django.http import HttpResponseBadRequest
from webpush import send_user_notification

class EmployeeList(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/employee.html'
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

        # Get all employees associated with the selected branch(es)
        employee = Employee.objects.filter(branch=selected_branch)

        # Call custom view function to process employee data
        data = my_view(request, employee)
        sort_list = list(set([i.user.date_joined.date for i in employee]))
        if employee.exists():
            if employee[0].status == 'Active':
                isActive=True
            else:
                isActive=False
        else:
            isActive=False
        # Construct context dictionary with relevant data
        context = {
            'employee': employee,
            'pk_id': pk_id,
            'user': user,
            'is_admin': is_admin,
            'branches': branches,
            'selected_branch': selected_branch,
            'isActive': isActive,
            'sort_list':sort_list
        }

        # Merge context dictionary with data dictionary returned by my_view
        context = {**context, **data}

        # Return context dictionary as JSON response
        return Response(context)


    def post(self, request):
        return Response({'message': ''})

class EmployeeDetail(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/employee-detail.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.filter()

    def get(self, request,user_id,user_name):
        # Check user permissions
        if not group_match('Admin', request) and not group_match('Salon', request) and not group_match('Manager', request):
            return redirect('/')

        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)

        try:
            customer_user = User.objects.get(id=user_id,username=user_name)
        except Exception:
            return render(request,'error.html')
            
        if group_match('Manager',request) == True:
            salon_verfied = False
        else:
            salon_verfied = True

        employee = Employee.objects.get(user=customer_user)
        salary = Salary.objects.filter(employee=employee,paid=True).order_by('-month')

        context = {
                'user':customer_user,'salary':salary,
                'pk_id': pk_id,
                'user': employee,
                'is_admin': is_admin,
                'selected_branch': selected_branch,
                'employee':employee,
                'branches':branches}
        return Response(context)
        
    def post(self, request):
        return Response({'message': ''})

class StaffDetail(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/staff-detail.html'
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

        return Response({'key': 'Staff Details', 'data': '', 'page': '', 'pages': ''})

    def post(self, request):
        return Response({'message': ''})
   
class AddEmployee(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/add-employee.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.filter()

    def get(self, request):
        # Check user permissions
        if not group_match('Admin', request) and not group_match('Salon', request) and not group_match('Manager', request):
            return redirect('/')

        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)

        # Prepare the response context
        context = {'branches':branches,
                'pk_id': pk_id,
                'user': user,
                'is_admin': is_admin,
                'selected_branch': selected_branch
                }
        return Response(context)

    def post(self, request):
        # Check user permissions
        if not group_match('Admin', request) and not group_match('Salon', request) and not group_match('Manager', request):
            return redirect('/')

        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)
        # Get the form data from the request
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = create_username(first_name,last_name)
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        employee_type = request.POST.get('employee_type')
        password = username + str(randint(1000, 9999))
        product_incentive = request.POST.get('product_incentive')
        service_incentive = request.POST.get('service_incentive')
        basic_salary = request.POST.get('basic_salary')


        if User.objects.filter(mobile=phone):
            messages.error(request,"This Mobile Number Already Exists")
            return redirect('/signup')

        # Create a new user and save it to the database

        user_save = User(
            username = username,
            first_name = first_name,
            last_name = last_name,
            email = email,
            mobile = phone,
            password = make_password(password)
        )
        user_save.save()

        # Check if the employee_type group exists, else create a new one
        try:
            group = Group.objects.get(name=employee_type)
        except Group.DoesNotExist:
            group = Group(name=employee_type)
            group.save()

        # Add the user to the employee_type group
        user_save.groups.add(group)

        # Get the salon user and their associated salon details
        salon_user = User.objects.get(id=request.user.id)
        salon_branch = SalonDetails.objects.get(user=salon_user)
        # Get all the branches associated with the salon
        branch = Branch.objects.filter(salon=salon_branch).first()

        # Create a new employee and save it to the database
        emp_save = Employee(
            user = user_save,
            branch = branch,
            employee_type = employee_type,
            product_incentive = int(product_incentive),
            service_incentive = int(service_incentive),
            base_salary = basic_salary
        )
        emp_save.save()

        # If the employee_type is Manager, assign them to the selected branch as a manager
        if employee_type == "Manager":
            try:
                branch_detail = Branch.objects.get(id=selected_branch.id)
                branch_detail.manager = user_save
                branch_detail.save()
            except Branch.DoesNotExist:
                pass

        # Send an email to the new employee with their login credentials
        # mail.send_mail(f"Login Credentials",f"Hello {emp_save.user.username},\n\nLink: https://snipklip.in/login/ \nEmail ID: {email}\nPassword: {password}\n\nTeam SnipKlip",
        #         f'admin@snipklip.in',[email])
        messages.success(request,f"Successfully created a {employee_type}")
        return redirect('add-employee')
    



class EditEmployee(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/edit-employee.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.filter()

    def get(self, request,employee_id):
        if not group_match('Admin', request) and not group_match('Salon', request) and not group_match('Manager', request):
            return redirect('/')
        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)
        

        employee = Employee.objects.get(id=employee_id)
        if employee.branch in branches:
            pass
        else:
            return render(request,'error.html')
        # Prepare the response context
        context = {
                'branches':branches,
                'pk_id': pk_id,
                'user': user,
                'is_admin': is_admin,
                'selected_branch': selected_branch,
                'emp':employee
                }
        return Response(context)

    def post(self, request,employee_id):
        # Check user permissions
        if not group_match('Admin', request) and not group_match('Salon', request) and not group_match('Manager', request):
            return redirect('/')
        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)
        
        
        # Get the form data from the request
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        employee_type = request.POST.get('employee_type')
        product_incentive = request.POST.get('product-incentive')
        service_incentive = request.POST.get('service-incentive')
        active = request.POST.get('status')

        emp = Employee.objects.get(id=employee_id)
        staff_user = User.objects.get(id=emp.user.id)
        staff_user.first_name = first_name
        staff_user.last_name = last_name
        staff_user.email = email
        staff_user.mobile = phone
        staff_user.status = active
        staff_user.save()
        emp.employee_type = employee_type
        emp.product_incentive = product_incentive
        emp.service_incentive = service_incentive
        emp.save()

        # If the employee_type is Manager, assign them to the selected branch as a manager
        if employee_type == "Manager":
            try:
                branch_detail = Branch.objects.get(id=selected_branch.id)
                branch_detail.manager = staff_user
                branch_detail.save()
                my_group = Group.objects.get(name='Staff') 
                my_group.user_set.remove(user)
            except Branch.DoesNotExist:
                pass
        else:
            try:
                branch_detail = Branch.objects.get(id=selected_branch.id)
                branch_detail.manager = None
                branch_detail.save()
                user = User.objects.get(id=emp.user.id)
                my_group = Group.objects.get(name='Staff') 
                my_group.user_set.add(user)
                user.save()
            except Branch.DoesNotExist:
                pass
        messages.success(request,f"Successfully Edit Employee Details For {emp.user.first_name} {emp.user.last_name}")
        return redirect(f'/edit-employee/{emp.id}/?branch={selected_branch.id}')
