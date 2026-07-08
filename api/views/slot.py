
from datetime import datetime, time, timedelta
from random import randint
from xml.dom import ValidationErr
from api.decorators import jwt_authentication_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from api.serializers import CustomerSerializer, AppointmentSerializer, SalarySerializer, ExpenseSerializer, EmployeeSerializer, InvoiceSerializer
from backend.models import *
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from cryptography.fernet import Fernet
from api.constants import *
from django.db.models import Q

def check_seat_availability(request, branch, start_time_slot, end_time_slot, date_selected, staff_objects_list):
    try:
        if start_time_slot is None or end_time_slot is None:
            # Handle the case when start_time_slot or end_time_slot is None
            return JsonResponse({
                'message': 'API called',
                'status': 200
            })
        
        for start_time, end_time, staff in zip(start_time_slot, end_time_slot, staff_objects_list):
            for staff in staff:
                time_difference = datetime.timedelta(seconds=1)
                start_time = datetime.datetime.strptime(start_time, "%H:%M") + time_difference
                end_time = datetime.datetime.strptime(end_time, "%H:%M") - time_difference

                appointment_available = Appointment.objects.filter(
                    Q(branch=branch, date=date_selected, staff_assigned=staff, start_time__range=(start_time, end_time)) |
                    Q(branch=branch, date=date_selected, staff_assigned=staff, end_time__range=(start_time, end_time)) |
                    Q(branch=branch, date=date_selected, staff_assigned=staff, start_time__lte=start_time, end_time__gte=end_time)
                )

                if appointment_available:
                    # Handle the case when the seat is not available
                    return JsonResponse({
                        'message': f'{staff} is Not Available between {str(start_time).split(" ")} - {str(end_time).split(" ")}',
                        'status': 301
                    })

        # If seats are available, return a success message
        return JsonResponse({
            'message': 'Seats are available',
            'status': 200
        })

    except Exception as e:
        # Handle any unexpected exceptions here and return an appropriate response
        return JsonResponse({
            'error': str(e),
            'status': 500
        })


'''
Input requests
{
  "staff_assigned": [
    {"attribute_id": 1},
    {"attribute_id": 2}
  ],
  "branch_id": 123,
  "service": [
    {"attribute_name": "Service A"},
    {"attribute_name": "Service B"}
  ],
  "booking_date": "2023-10-30",
  "time_slot": "08:00:00 - 09:00:00"
}

Output data
{
  "staff_availability": [
    {
      "name": "Service A",
      "details": [
        {
          "id": 1,
          "time": "08:00:00",
          "staff": "John Doe",
          "description": "John Doe 08:00:00",
          "status": "not-available"
        },
        {
          "id": 2,
          "time": "08:00:00",
          "staff": "Jane Smith",
          "description": "Jane Smith 08:00:00",
          "status": "false"
        }
      ]
    },
    {
      "name": "Service B",
      "details": [
        {
          "id": 1,
          "time": "08:00:00",
          "staff": "John Doe",
          "description": "John Doe 08:00:00",
          "status": "not-available"
        },
        {
          "id": 2,
          "time": "08:00:00",
          "staff": "Jane Smith",
          "description": "Jane Smith 08:00:00",
          "status": "false"
        }
      ]
    }
  ],
  "status": 200
}
'''

def round_up_to_next_five_minutes(time_str):
    # Parse the time string into a datetime object
    time_obj = datetime.strptime(time_str, "%H:%M:%S")
    
    # Calculate minutes to add to round up to the nearest 5-minute mark
    minutes = time_obj.minute
    if minutes % 5 == 0:
        return time_obj.strftime("%H:%M:%S")
    
    minutes_to_add = 5 - (minutes % 5)
    
    # Add the calculated minutes
    new_time_obj = time_obj + timedelta(minutes=minutes_to_add)
    
    # Format the new time to the desired string format (HH:MM)
    new_time_str = new_time_obj.strftime("%H:%M:%S")

    #format in datetime.time format ("%H:%M:%S")
    formattedTime = datetime.strptime(new_time_str, "%H:%M:%S")
    
    return formattedTime

@api_view(['GET', 'POST'])
@jwt_authentication_required
def getAvailableStaff(request):
    data = request.data
    print(data)
    date = data['booking_date']
    format_date = datetime.strptime(date, "%b %d, %Y").date()
    invoice_id = data['invoice_id']
    if invoice_id != '':
        try:
            invoice = Invoice.objects.get(id=data['invoice_id'])
        except Exception:
            return JsonResponse({
                        'message': "Invoice Id Not Found",
                        'status': 500
                })
        invoice_appointment= []
        for appointment in invoice.appointment.all():
            invoice_appointment.append(appointment)
            
    employee_id_list = []
    for employee in data['staff_assigned']:
        employee_id_list.append(employee['attribute_id'])

    staff_list = []
    branch_id = data['branch_id']
    branch = Branch.objects.get(id=branch_id)
    employee = Employee.objects.filter(branch=branch,id__in=employee_id_list,status="Active")
    service = data['service']
    date_selected = data['booking_date']
    start_time_slot = []
    start_time = datetime.strptime(data['time_slot'].split(' ')[0], "%H:%M")
    five_min_difference = timedelta(minutes=5)
    end_time = datetime.strptime(data['time_slot'].split(' ')[-2], "%H:%M")

    current_time = start_time - five_min_difference
    end_timer = end_time - five_min_difference

    # Loop to print times with 5-minute gap
    while current_time <= end_timer:
        current_time += five_min_difference
        parsed_time = datetime.strptime(str(current_time)[:16], '%Y-%m-%d %H:%M')
        time_portion = parsed_time.strftime('%H:%M')
        start_time_slot.append(time_portion)

    main_data = []
    services_list = []
    for service in service:
        service_object = Service.objects.get(branch=branch,name=service['attribute_name'])
        services_list.append(service_object)
        main_data.append({
            'name':service['attribute_name'],
            'details':[]
        })

    for service in services_list:
        for start_time in start_time_slot:
            for staff in employee:
                time_difference = timedelta(seconds=1)
                time_taken_for_service = timedelta(minutes=service.time_for_each_service)
                start_times = datetime.strptime(start_time, "%H:%M") + time_difference
                end_time = datetime.strptime(start_time, "%H:%M") + time_taken_for_service - time_difference

    # try:
    # Extract staff IDs from the request data
    employee_id_list = [employee['attribute_id'] for employee in data['staff_assigned']]
    
    staff_list = []
    branch_id = data['branch_id']
    branch = Branch.objects.get(id=branch_id)
    
    # Filter employees based on branch and extracted IDs
    employee = Employee.objects.filter(branch=branch, id__in=employee_id_list,status="Active")
    
    service_list = []

    # Iterate through services from the request
    for service_data in data['service']:
        # Get the corresponding service object
        service = Service.objects.get(branch=branch, name=service_data['attribute_name'])
        service_list.append(service)

    date_selected = data['booking_date']
    time_slot = data['time_slot']
    start_time_slot = []

    # Extract start and end times from the time slot
    start_time = datetime.strptime(time_slot.split(' ')[0], "%H:%M")
    end_time = datetime.strptime(time_slot.split(' ')[-2], "%H:%M")


    currentTime = datetime.now().time()
    formatted_time = currentTime.strftime("%H:%M:%S")
    parsedTime = datetime.strptime(formatted_time, "%H:%M:%S").time()

    if datetime.now().date() == format_date:
        format_start_time = start_time.time()
        format_end_time = end_time.time()
        if parsedTime >= format_start_time and parsedTime < format_end_time:
            round_time = round_up_to_next_five_minutes(str(parsedTime))
            start_time = datetime(year=1900,month=1,day=1,hour=round_time.hour,minute=round_time.minute,second=round_time.second)

    
    current_time = start_time - timedelta(minutes=5)
    end_timer = end_time - timedelta(minutes=5)

    # Generate a list of time slots with a 5-minute gap
    while current_time <= end_timer:
        current_time += timedelta(minutes=5)
        time_portion = current_time.strftime('%H:%M')
        start_time_slot.append(time_portion)

    main_data = []

    # Create a data structure to store service details
    for service in service_list:
        service_data = {
            'name': service.name,
            'details': []
        }
        main_data.append(service_data)

    for service in service_list:
        for start_time in start_time_slot:
            for staff in employee:
                time_difference = timedelta(seconds=1)
                time_taken_for_service = timedelta(minutes=service.time_for_each_service)
                start_times = datetime.strptime(start_time, "%H:%M") + time_difference
                end_time = datetime.strptime(start_time, "%H:%M") + time_taken_for_service - time_difference
                convert_into_IST = timedelta(hours=5, minutes=30)

                try:
                    # Parse the booking date with IST adjustment
                    date_obj = datetime.strptime(str(date_selected), "%Y-%m-%d") + convert_into_IST
                except Exception as e:
                    try:
                        date_obj = datetime.strptime(str(date_selected), "%b %d, %Y") + convert_into_IST
                    except Exception:
                        # Handle the exception and provide a fallback or error message
                        date_obj = datetime.now()  # Replace with an appropriate fallback

                formatted_date = date_obj.strftime('%Y-%m-%d')

                appointment_available = Appointment.objects.filter(
                                            Q(branch=branch, date=formatted_date, staff_assigned=staff, start_time__range=(start_times, end_time)) | 
                                            Q(branch=branch, date=formatted_date, staff_assigned=staff, end_time__range=(start_times, end_time)) |
                                            Q(branch=branch, date=formatted_date, staff_assigned=staff, start_time__lte=end_time, end_time__gte=end_time)
                                        )

                if invoice_id != '':
                    appointment_in_appointment_available = any(item in appointment_available for item in invoice_appointment)

                    if appointment_in_appointment_available:
                        invoice = Invoice.objects.get(id=invoice_id)
                        appointment = invoice.appointment.get(service=service)
                        appointment_start_time = datetime.strptime(start_time, "%H:%M")
                        if str(appointment_start_time).split(" ")[1] == str(appointment.start_time):
                            staff_list.append(staff)
                            detail = {
                                'id': staff.id,
                                'time': start_time,
                                'staff': staff.user.get_name(),
                                'description': str(start_time),
                                'status': "True"
                            }
                            for data in main_data:
                                if data['name'] == service.name:
                                    data['details'].append(detail)
                        appointment_available = appointment_available.exclude(pk=appointment.pk)

                if appointment_available:
                    staff_list.append(staff)
                    detail = {
                        'id': staff.id,
                        'time': start_time,
                        'staff': staff.user.get_name(),
                        'description': str(start_time),
                        'status': 'not-available'
                    }
                    for data in main_data:
                        if data['name'] == service.name:
                            data['details'].append(detail)
                else:
                    staff_list.append(staff)
                    detail = {
                        'id': staff.id,
                        'time': start_time,
                        'staff': staff.user.get_name(),
                        'description': str(start_time),
                        'status': 'false'
                    }

                    for data in main_data:
                        if data['name'] == service.name:
                            data['details'].append(detail)

    if invoice_id != '':
        # Create a dictionary to track unique combinations of 'time' and 'staff' for each 'name'
        unique_combinations = {}

        # Create a new list without duplicates
        new_main_data = []

        for item in main_data:
            name = item['name']
            unique_details = []
            for detail in item['details']:
                time_staff_key = (detail['time'], detail['staff'])
                if time_staff_key not in unique_combinations.get(name, set()):
                    unique_combinations.setdefault(name, set()).add(time_staff_key)
                    unique_details.append(detail)
            if unique_details:
                new_item = item.copy()
                new_item['details'] = unique_details
                new_main_data.append(new_item)

    
    if invoice_id != '':
        data = new_main_data
    else:
        data = main_data

    return JsonResponse({
            'staff_availability': data,
            'status': 200
        })

    # except Exception as e:
    #     # Handle any unexpected exceptions here and return an appropriate response
    #     return Response({'error': str(e), 'status': 500})
    

def staff_schedule(request,branch,date_selected):
    employee = Employee.objects.filter(branch=branch,status="Active")
    booked_time = []
    for emp in employee:
        appointment = Appointment.objects.filter(staff_assigned = emp,date=date_selected)
        for appointment in appointment:
            booked_time.append(f"{appointment.start_time} - {appointment.end_time}")

    serializer = EmployeeSerializer(employee, many=True)

    return JsonResponse({
        'booked_time':booked_time,
        'staff': serializer.data,
        'status':200
    })

            
