from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from backend.models import *
from datetime import datetime
from backend.views.common.conditions import group_match
from .essentials import get_user_salon_branch_details, group_match

class Expenses(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/expenses.html'
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
    
        page = request.GET.get("page")
        if page == None: page = 1
        
        expenses = Expense.objects.filter(branch=selected_branch)
        all_date = list(set(expenses.values_list('date',flat=True)))
        paginator = Paginator(expenses, 8)
        expenses = paginator.get_page(page)
        start_i = expenses.start_index()
        end_i = expenses.end_index()
        total_count = paginator.count

        context = {'all_date':all_date,'expense':expenses,'selected_branch':selected_branch,'branches':branches,'pk_id': pk_id,'user': user,'is_admin': is_admin,
                   'start_i':start_i,
            'end_i':end_i,
            'list_page':paginator.page_range,
            'total_count':total_count,
            'has_prev':expenses.has_previous(),
            'has_next':expenses.has_next(),
            'next_page':int(page)+1,
            'prev_page':int(page)-1,
            'page_num':int(page),
                   }
        return Response(context)

    def post(self, request):
        return Response({'message': ''})

class AddExpenses(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/add-expenses.html'
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
        
        return Response({'selected_branch':selected_branch,'branches':branches,'pk_id': pk_id,'user': user,'is_admin': is_admin})

    def post(self, request):
        branch = Branch.objects.get(id=int(request.POST.get('selected_branch')))
        branch_id = int(request.POST.get('selected_branch'))
        try:
            spent_on = request.POST.get('spent_on')
            date = datetime.today()
            amount = request.POST.get('amount')
            expen = Expense(
                branch = branch,
                description = spent_on,
                date = date,
                amount = amount
            )
            expen.save()
            messages.success(request,'Expense Added')
            return redirect(f'/add-expenses/?branch={branch_id}')
        except Exception:
            messages.error(request, f'Some Error Occured! Contact {settings.COMPANY_NAME}')
            return redirect(request.path)
        