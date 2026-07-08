from django.http import JsonResponse
from django.shortcuts import redirect
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import date,timedelta
from backend.models import *
import json
from datetime import datetime, date, timedelta
from backend.views.common.conditions import group_match
from datetime import datetime, date, timedelta
from .essentials import get_user_salon_branch_details, group_match
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count


class Reports(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/reports.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.filter()

    def get(self, request):
        # Check user permissions
        if not group_match('Admin', request) and not group_match('Salon', request):
            return redirect('/')

        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)
        
        today = date.today()
        six_months_ago = today - timedelta(days=180)

        bookings = list(Appointment.objects.filter(date__gte=six_months_ago).values('date').annotate(num_bookings=Count('id')))
        
        booking_list = [i['date'].strftime('%b') for i in bookings]

        booking_set = list(set(booking_list))
        for i in range(0, len(booking_set)):
            booking_set[i] = {'date':booking_set[i], 'num_bookings':0}
            for booking in bookings:
                if booking_set[i]['date'] == booking['date'].strftime('%b'):
                    booking_set[i]['num_bookings'] += booking['num_bookings']


        booking_data = [{'country': booking['date'], 'visits': booking['num_bookings']} for booking in booking_set]

        revenues = list(Appointment.objects.filter(date__gte=six_months_ago, isPaid=True))
        revenues = [{'date':i.date.strftime('%b'), 'price':i.totalPrice} for i in revenues]
        revenue_list = [i['date'] for i in revenues]

        revenue_set = list(set(revenue_list))
        for i in range(0, len(revenue_set)):
            revenue_set[i] = {'date':revenue_set[i], 'price':0}
            for revenue in revenues:
                if revenue_set[i]['date'] == revenue['date']:
                    revenue_set[i]['price'] += revenue['price']
        for revenue in revenue_set:
            revenue['price'] = int(revenue['price'])
        revenue_list = [{'country':revenue['date'], 'visits':revenue['price']} for revenue in revenue_set]
        # income_data = [{'country': booking['date'].strftime('%b'), 'visits': booking['num_bookings']} for booking in total_amount]
        chart_data = prepare_appointment_data()

        # services
        _salon = SalonDetails.objects.filter(name=salon).first()
        _branch = Branch.objects.filter(salon=_salon).first()
        
        services = Appointment.objects.filter(date__gte=six_months_ago, salon=_salon, isPaid=True).values_list('service', flat=True)
        services = [{'name':Service.objects.filter(id=k).first().name, 'price':Service.objects.filter(id=k).first().price} for k in services]
        services_list = [i['name'] for i in services]
        services_set = list(set(services_list))



        for i in range(0, len(services_set)):
            services_set[i] = {'name':services_set[i], 'price':0}
            for service in services:
                if services_set[i]['name'] == service['name']:
                    services_set[i]['price'] += int(service['price'])


        services = [{'country':i['name'], 'visits':i['price']} for i in services_set]


        emp_list = list(Employee.objects.filter(branch=_branch))
        staff_list = emp_list

        emp_price_list = []
        for i in emp_list:
            price = 0
            for k in Appointment.objects.filter(staff_assigned=i):
                price += k.totalPrice
            
            emp_price_list.append(price)

        emp_list = [{'country': f"{i.user.first_name} {i.user.last_name}", 'visits': int(k)} for i, k in zip(emp_list, emp_price_list)]

        return Response({'key': 'Reports', 'data': '', 'page': '', 'pages': '',
            'appointment_data':chart_data,
            'branches':branches,
            'pk_id': pk_id,
            'user': user,
            'is_admin': is_admin,
            'branches': branches,
            'selected_branch': selected_branch,
            'emp_list':staff_list
            })

    def post(self, request):
        return Response({'message': ''})

@csrf_exempt
def booking_reports(request):
    if request.method == 'POST':
        # Check user permissions
        if not group_match('Admin', request) and not group_match('Salon', request):
            return redirect('/')

        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)
        
        data = json.loads(request.body.decode())
        
        start_date = datetime.strptime(data['start'], '%Y-%m-%d %H:%M')
        end_date = datetime.strptime(data['end'], '%Y-%m-%d %H:%M')

        _salon = SalonDetails.objects.filter(name=salon).first()
        
        

        services = []
        if data['emp']:
            user = User.objects.filter(username=data['emp']).first()
            emp = Employee.objects.filter(user=user).first()


            services = Appointment.objects.filter(date__gte=start_date.date(), date__lte=end_date.date(), staff_assigned=emp,salon=_salon, isPaid=True).values_list('service', flat=True)
        else:
            services = Appointment.objects.filter(date__gte=start_date.date(), date__lte=end_date.date(), salon=_salon, isPaid=True).values_list('service', flat=True)

        services = [{'name':Service.objects.filter(id=k).first().name, 'price':Service.objects.filter(id=k).first().price} for k in services]
        services_list = [i['name'] for i in services]
        services_set = list(set(services_list))

        for i in range(0, len(services_set)):
            services_set[i] = {'name':services_set[i], 'price':0}
            for service in services:
                if services_set[i]['name'] == service['name']:
                    services_set[i]['price'] += int(service['price'])


        services = [{'country':i['name'], 'visits':i['price']} for i in services_set]

        return JsonResponse({'data':services, 'code':"200"}, status=200)


    else:
        # Return error response
        response_data = {'message': 'Invalid request method'}
        return JsonResponse(response_data, status=400)


@csrf_exempt
def employee_reports(request):
    if request.method == 'POST':
        # Check user permissions
        if not group_match('Admin', request) and not group_match('Salon', request):
            return redirect('/')

        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)
        
        data = json.loads(request.body.decode())

        _salon = SalonDetails.objects.filter(name=salon).first()
        _branch = Branch.objects.filter(salon=_salon).first()

        
        start_date = datetime.strptime(data['start'], '%Y-%m-%d %H:%M')
        end_date = datetime.strptime(data['end'], '%Y-%m-%d %H:%M')

        
        emp_list = []
        if data['emp']:
            user = User.objects.filter(username=data['emp']).first()
            emp_list = list(Employee.objects.filter(user=user))
            
        else:
            emp_list = list(Employee.objects.filter(branch=_branch))

        emp_price_list = []
        for i in emp_list:
            price = 0
            for k in Appointment.objects.filter(date__gte=start_date.date(), date__lte=end_date.date(), staff_assigned=i):
                price += k.totalPrice
            
            emp_price_list.append(price)

        emp_list = [{'country': f"{i.user.first_name} {i.user.last_name}", 'visits': int(k)} for i, k in zip(emp_list, emp_price_list)]
        if data['emp']:
            if emp_list[0]['visits']<=0:
                emp_list = []

        return JsonResponse({'data':emp_list, 'code':"200"}, status=200)


    else:
        # Return error response
        response_data = {'message': 'Invalid request method'}
        return JsonResponse(response_data, status=400)


@csrf_exempt
def performance_reports(request):
    if request.method == 'POST':
        # Check user permissions
        if not group_match('Admin', request) and not group_match('Salon', request):
            return redirect('/')

        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)
        
        data = json.loads(request.body.decode())

        _salon = SalonDetails.objects.filter(name=salon).first()
        _branch = Branch.objects.filter(salon=_salon).first()

        
        start_date = datetime.strptime(data['start'], '%Y-%m-%d %H:%M')
        end_date = datetime.strptime(data['end'], '%Y-%m-%d %H:%M')

        bookings = []
        if data['emp']:
            user = User.objects.filter(username=data['emp']).first()
            emp = Employee.objects.filter(user=user).first()
            bookings = list(Appointment.objects.filter(date__gte=start_date.date(), date__lte=end_date.date(), staff_assigned=emp).values('date').annotate(num_bookings=Count('id')))
            
        else:
            bookings = list(Appointment.objects.filter(date__gte=start_date.date(), date__lte=end_date.date()).values('date').annotate(num_bookings=Count('id')))
        
        booking_list = [i['date'].strftime('%b') for i in bookings]

        booking_set = list(set(booking_list))
        for i in range(0, len(booking_set)):
            booking_set[i] = {'date':booking_set[i], 'num_bookings':0}
            for booking in bookings:
                if booking_set[i]['date'] == booking['date'].strftime('%b'):
                    booking_set[i]['num_bookings'] += booking['num_bookings']


        booking_data = [{'country': booking['date'], 'visits': booking['num_bookings']} for booking in booking_set]

        return JsonResponse({'data':booking_data, 'code':"200"}, status=200)


    else:
        # Return error response
        response_data = {'message': 'Invalid request method'}
        return JsonResponse(response_data, status=400)


@csrf_exempt
def revenue_reports(request):
    if request.method == 'POST':
        # Check user permissions
        if not group_match('Admin', request) and not group_match('Salon', request):
            return redirect('/')

        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)
        
        data = json.loads(request.body.decode())

        _salon = SalonDetails.objects.filter(name=salon).first()
        _branch = Branch.objects.filter(salon=_salon).first()

        
        start_date = datetime.strptime(data['start'], '%Y-%m-%d %H:%M')
        end_date = datetime.strptime(data['end'], '%Y-%m-%d %H:%M')


        revenues = []
        if data['emp']:
            user = User.objects.filter(username=data['emp']).first()
            emp = Employee.objects.filter(user=user).first()
            revenues = list(Appointment.objects.filter(date__gte=start_date.date(), date__lte=end_date.date(), staff_assigned=emp, isPaid=True))
            
        else:
            revenues = list(Appointment.objects.filter(date__gte=start_date.date(), date__lte=end_date.date(), isPaid=True))


        revenues = [{'date':i.date.strftime('%b'), 'price':i.totalPrice} for i in revenues]
        revenue_list = [i['date'] for i in revenues]

        revenue_set = list(set(revenue_list))
        for i in range(0, len(revenue_set)):
            revenue_set[i] = {'date':revenue_set[i], 'price':0}
            for revenue in revenues:
                if revenue_set[i]['date'] == revenue['date']:
                    revenue_set[i]['price'] += revenue['price']
        for revenue in revenue_set:
            revenue['price'] = int(revenue['price'])
        revenue_list = [{'country':revenue['date'], 'visits':revenue['price']} for revenue in revenue_set]

        return JsonResponse({'data':revenue_list, 'code':"200"}, status=200)


    else:
        # Return error response
        response_data = {'message': 'Invalid request method'}
        return JsonResponse(response_data, status=400)

@csrf_exempt
def payment_details(request):
    if request.method == 'POST':
        # Check user permissions
        if not group_match('Admin', request) and not group_match('Salon', request):
            return redirect('/')

        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)
        
        data = json.loads(request.body.decode())

        _salon = SalonDetails.objects.filter(name=salon).first()
        _branch = Branch.objects.filter(salon=_salon).first()

        
        start_date = datetime.strptime(data['start'], '%Y-%m-%d %H:%M')
        end_date = datetime.strptime(data['end'], '%Y-%m-%d %H:%M')

        data_set = []
        if data['emp']:
            user = User.objects.filter(username=data['emp']).first()
            emp = Employee.objects.filter(user=user).first()
            data_set = list(Appointment.objects.filter(date__gte=start_date.date(), date__lte=end_date.date(), staff_assigned=emp, isPaid=True))
            
        else:
            data_set = list(Appointment.objects.filter(date__gte=start_date.date(), date__lte=end_date.date(), isPaid=True))

        data_list = []
        for i in data_set:
            data_list.append({'country':i.mode_of_payment, 'value': 0})

        for i in data_set:
            for k in data_list:
                if i.mode_of_payment == k['country']:
                    k['value'] +=1


        return JsonResponse({'data':data_list, 'code':"200"}, status=200)


    else:
        # Return error response
        response_data = {'message': 'Invalid request method'}
        return JsonResponse(response_data, status=400)


def get_appointment_data():
     data = Appointment.objects.all().values('booking_status').annotate(total=Count('id'))
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
 