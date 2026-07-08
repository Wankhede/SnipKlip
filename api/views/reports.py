import calendar
from datetime import datetime, timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.serializers import CustomerSerializer, AppointmentSerializer, SalarySerializer, ExpenseSerializer, EmployeeSerializer, InvoiceSerializer
from backend.models import Branch, Customer, Appointment, Salary, Expense, Employee, Invoice, BranchCustomerMobile, SalonDetails, Service, User
from django.db.models import Count
from api.constants import *

#######################################################################################
def booking_reports(branch_id):
    branch = Branch.objects.get(id=branch_id)
    today = datetime.now().date()
    past_7_days = [today - timedelta(days=i) for i in range(7)]
    past_7_days.reverse()
    income = []
    for i in range(0,7):
        appointment = Appointment.objects.filter(date=past_7_days[i], branch=branch, isPaid=True)
        sum_of_invoice_actual_amount = sum(list(Invoice.objects.filter(appointment__in=appointment).values_list('actual_amount',flat=True)))
        income.append(sum_of_invoice_actual_amount)

    data = [{'past_7_days':past_7_days, 'income':income}]
    return data

@api_view(['GET', 'POST'])
def get_all_reports(request, id=None):
    if request.method == 'GET':
        # Return the serialized data in the response
        data = booking_reports(1)
        return Response({
            "data": {
                "services": [
                    {
                    'name': 'Income',
                    'date': data[0]['past_7_days'],
                    'data': data[0]['income']
                    }
                ],
            },
            "message": APIMessages.ALL_CUSTOMER_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        })

    if request.method == 'POST':
        return Response({
            "message": APIMessages.ALL_CUSTOMER_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        })
    

################################################################################################



############################################################################################
@api_view(['GET', 'POST'])
def employee_reports(request):
    if request.method == 'POST':
        salon_id = request.POST.get('salon_id', 1)
        selected_branch_id = request.data.get('branch_id', 1)
        user_id = request.data.get('user_id', 2)
        slot = request.POST.get('slot', 'week')  # Assume default slot is 'week'

        _salon = SalonDetails.objects.get(id=salon_id)
        _branch = Branch.objects.get(id=selected_branch_id)
        emp_id = request.data.get('emp_id', None)

        now = datetime.now()
        if slot == 'week':
            start_date = now - timedelta(days=now.weekday())
            end_date = start_date + timedelta(days=6)
        elif slot == 'month':
            start_date = now.replace(day=1)
            _, last_day = calendar.monthrange(now.year, now.month)
            end_date = start_date + timedelta(days=last_day - 1)
        else:
            # Handle other cases or provide a default behavior
            start_date = now
            end_date = now

        emp_list = []
        if emp_id:
            user = User.objects.get(id=emp_id)
            emp_list = list(Employee.objects.filter(user=user,status="Active"))
        else:
            emp_list = list(Employee.objects.filter(branch=_branch))

        emp_price_list = []
        total_price = 0
        for employee in emp_list:
            price = 0
            for appointment in Appointment.objects.filter(date__gte=start_date.date(), date__lte=end_date.date(), staff_assigned=employee):
                price += appointment.totalPrice
            
            emp_price_list.append(price)
            total_price += price

        emp_names = [f'{employee.user.first_name} {employee.user.last_name}' for employee in emp_list]

        if emp_id:
            if emp_price_list[0] <= 0:
                emp_names = []
                emp_price_list = []

        return Response({
            "data": {
                'employee': emp_names,
                'list': emp_price_list,
                "total":total_price,
            },
            "message": APIMessages.ALL_CUSTOMER_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        }) 

    else:
        branch = Branch.objects.get(id=1)
        today = datetime.now().date()
        past_7_days = [today - timedelta(days=i) for i in range(7)]
        past_7_days.reverse()
        employee = Employee.objects.filter(branch=branch,employee_type="Staff",status="Active")
        employee_data = []

        for emp in employee:
            for i in range(0,7):
                employee_data.append({
                    'date':past_7_days[i],
                    'employee_name':emp.user.username,
                    'employee_service_availed_count':len(Appointment.objects.filter(staff_assigned=emp,date=past_7_days[i], isPaid=True))
                    })

        data = [{'employee_data':employee_data}]
    
        return Response({
            "data": data,
            "message": APIMessages.ALL_EMPLOYEE_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        }) 

@api_view(['GET', 'POST'])
def performance_reports(request):
    if request.method == 'POST':
        # Check user permissions
        salon_id = request.data.get('salon_id')
        selected_branch_id = request.data.get('branch_id')
        user_id = request.data.get('user_id')
        slot = request.POST.get('slot', 'week')  # Assume default slot is 'week'

        _salon = SalonDetails.objects.get(id=salon_id)
        _branch = Branch.objects.get(id=selected_branch_id)
        emp_id = request.data.get('emp_id', None)
        
        now = datetime.now()
        if slot == 'week':
            start_date = now - timedelta(days=now.weekday())
            end_date = start_date + timedelta(days=6)
        elif slot == 'month':
            start_date = now.replace(day=1)
            _, last_day = calendar.monthrange(now.year, now.month)
            end_date = start_date + timedelta(days=last_day - 1)
        else:
            # Handle other cases or provide a default behavior
            start_date = now
            end_date = now

        bookings = []
        if emp_id:
            user = User.objects.get(id=emp_id)
            emp = Employee.objects.filter(user=user,status="Active").first()
            bookings = list(Appointment.objects.filter(date__gte=start_date.date(), date__lte=end_date.date(), staff_assigned=emp).values('date').annotate(num_bookings=Count('id')))
        else:
            bookings = list(Appointment.objects.filter(date__gte=start_date.date(), date__lte=end_date.date()).values('date').annotate(num_bookings=Count('id')))
        
        booking_list = [i['date'].strftime('%b') for i in bookings]

        booking_set = list(set(booking_list))
        for i in range(0, len(booking_set)):
            booking_set[i] = {'date': booking_set[i], 'num_bookings': 0}
            for booking in bookings:
                if booking_set[i]['date'] == booking['date'].strftime('%b'):
                    booking_set[i]['num_bookings'] += booking['num_bookings']

        booking_months = [i['date'] for i in booking_set]
        booking_count = [i['num_bookings'] for i in booking_set]

        total = 0
        for i in booking_count:
            total += i

        return Response({
            "data": {
                'booking_months': booking_months,
                'booking_count': booking_count,
                'total':total,
            },
            "message": APIMessages.ALL_CUSTOMER_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        }) 

    else:
        # Return error response
        response_data = {'message': 'Invalid request method'}
        return Response({
            "data": response_data,
            "message": APIMessages.ALL_CUSTOMER_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        }) 

@api_view(['GET', 'POST'])
def revenue_reports(request):
    if request.method == 'POST':
        # Check user permissions
        salon_id = request.data.get('salon_id', 1)
        selected_branch_id = request.data.get('branch_id', 1)
        user_id = request.data.get('user_id', 2)
        slot = request.POST.get('slot', 'week')  # Assume default slot is 'week'

        _salon = SalonDetails.objects.get(id=salon_id)
        _branch = Branch.objects.get(id=selected_branch_id)
        emp_id = request.data.get('emp_id', None)

        now = datetime.now()
        if slot == 'week':
            start_date = now - timedelta(days=now.weekday())
            end_date = start_date + timedelta(days=6)
        elif slot == 'month':
            start_date = now.replace(day=1)
            _, last_day = calendar.monthrange(now.year, now.month)
            end_date = start_date + timedelta(days=last_day - 1)
        else:
            # Handle other cases or provide a default behavior
            start_date = now
            end_date = now

        revenues = []
        if emp_id:
            user = User.objects.get(id=emp_id)
            emp = Employee.objects.filter(user=user,status="Active").first()
            revenues = list(Appointment.objects.filter(date__gte=start_date.date(), date__lte=end_date.date(), staff_assigned=emp, isPaid=True))
        else:
            revenues = list(Appointment.objects.filter(date__gte=start_date.date(), date__lte=end_date.date(), isPaid=True))

        revenues = [{'date': i.date.strftime('%b'), 'price': i.totalPrice} for i in revenues]
        revenue_list = [i['date'] for i in revenues]

        revenue_set = list(set(revenue_list))
        for i in range(0, len(revenue_set)):
            revenue_set[i] = {'date': revenue_set[i], 'price': 0}
            for revenue in revenues:
                if revenue_set[i]['date'] == revenue['date']:
                    revenue_set[i]['price'] += revenue['price']

        revenue_months = [i['date'] for i in revenue_set]
        revenue_count = [int(i['price']) for i in revenue_set]

        total = sum(revenue_count)

        return Response({
            "data": {
                'revenue_months':revenue_months,
                'revenue_count':revenue_count,
                'total':total,
            },
            "message": APIMessages.ALL_CUSTOMER_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        }) 

    else:
        # Return error response
        response_data = {'message': 'Invalid request method'}
        return Response({
            "data": response_data,
            "message": APIMessages.ALL_CUSTOMER_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        }) 

@api_view(['GET', 'POST'])
def payment_details(request):
    if request.method == 'POST':
        # Check user permissions
        salon_id = request.data.get('salon_id', 1)
        selected_branch_id = request.data.get('branch_id', 1)
        user_id = request.data.get('user_id', 2)
        slot = request.POST.get('slot', 'week')  # Assume default slot is 'week'

        _salon = SalonDetails.objects.get(id=salon_id)
        _branch = Branch.objects.get(id=selected_branch_id)
        emp_id = request.data.get('emp_id', None)

        now = datetime.now()
        if slot == 'week':
            start_date = now - timedelta(days=now.weekday())
            end_date = start_date + timedelta(days=6)
        elif slot == 'month':
            start_date = now.replace(day=1)
            _, last_day = calendar.monthrange(now.year, now.month)
            end_date = start_date + timedelta(days=last_day - 1)
        else:
            # Handle other cases or provide a default behavior
            start_date = now
            end_date = now

        data_set = []
        if emp_id:
            user = User.objects.get(id=emp_id)
            emp = Employee.objects.filter(user=user,status="Active").first()
            data_set = list(Invoice.objects.filter(date_created__gte=start_date.date(), date_created__lte=end_date.date(), status='PAID'))
        else:
            data_set = list(Invoice.objects.filter(date_created__gte=start_date.date(), date_created__lte=end_date.date(), status='PAID'))

        data_list = []
        for i in data_set:
            data_list.append({'country': i.mode_of_payment, 'value': 0})
        for i in data_set:
            for k in data_list:
                if i.mode_of_payment == k['country']:
                    k['value'] += 1

        mode_of_payments = [i['country'] for i in data_list]
        mode_of_payments_count = [i['value'] for i in data_list]

        total = sum(mode_of_payments_count)

        return Response({
            "data": {
                'mode_of_payments':mode_of_payments,
                'mode_of_payments_count':mode_of_payments_count,
                'total':total
            },
            "message": APIMessages.ALL_CUSTOMER_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE
        }) 

    else:
        # Return error response
        response_data = {'message': 'Invalid request method'}
        return Response({
            "data": response_data,
            "message": APIMessages.ALL_CUSTOMER_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE
        }) 

def get_appointment_data():
     data = Appointment.objects.all().values('booking_status').annotate(total=Counter('id'))
     return data

def prepare_appointment_data():
     data = get_appointment_data()
     chart_data = []
     for item in data:
         chart_data.append({
             'category': item['booking_status'],
             'value': item['total']
         })
     return chart_data
    