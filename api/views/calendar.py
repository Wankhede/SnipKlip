from datetime import datetime
import random
import string
from api.throttles import SustainedRateThrottle
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from api.constants import *

from api.serializers import (
    AppointmentSerializer
)
from backend.models import (
    Branch, Service, Appointment, Employee,
    Invoice, SalonDetails, User
)

# credentials = get_credentials()
# http = credentials.authorize(httplib2.Http())

# service_calendar = discovery.build('calendar', 'v3', http=http)
from django.http import JsonResponse
from api.data.events import events


EVENT_COLORS = {
    "Availed": '#1890ff',
    "Booked": '#52c41a',
    "Pending": '#8c8c8c',
    "Cancelled by salon": '#faad14',
    "Cancelled by user": '#f5222d'
}

# Function to convert time to ISO 8601 format
def convert_time(time_str):
    dt_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    return dt_obj.strftime("%Y-%m-%d %H:%M:%S")

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@throttle_classes([SustainedRateThrottle])
def getEvents(request):
    try:
        if request.method == "GET":
            branch_id = request.GET.get('branch_id')

            all_appointments = Appointment.objects.filter(branch__id=branch_id)
            serializer = AppointmentSerializer(all_appointments, many=True)

            event_data = []
            for appointment in serializer.data:
                id = appointment['id']
                booking_status = appointment['booking_status']
                color = EVENT_COLORS[booking_status]
                booking_date = appointment['booking_date']
                start_time = appointment['start_time']
                end_time = appointment['end_time']

                # Convert date and time to ISO 8601 format
                start = convert_time(f"{booking_date} {start_time}")
                end = convert_time(f"{booking_date} {end_time}")

                # Extract service data
                service_data = appointment['service']
                staff_assigned = appointment['staff_assigned']
                # Update the description field by joining the names of services and staff
                service_names = ', '.join(map(lambda service: service['name'], service_data))
                staff_names = ', '.join(map(lambda staff: staff['customer_name'], staff_assigned))
                resource_ids = [str(staff['id']) for staff in staff_assigned]
                # Prepare event data
                try:
                    for resource_id in resource_ids:
                        event = {
                            'id': str(id),
                            'title': f"{appointment['user']['first_name']} {appointment['user']['last_name']}",
                            'description': f"{service_names}, {staff_names}",
                            'allDay': False,
                            'color': color,
                            'start': start,
                            'end': end,
                            'resourceId': resource_id
                        }
                        event_data.append(event)
                except:
                    pass

            # Return the JSON response with event data
            return JsonResponse(event_data, safe=False)
    except Exception as e:
        # If an unexpected error occurs, return an error response
        return Response({
            "message": APIMessages.ERROR.value,
            "status": FAILED_STATUS_CODE,
        })

    # If the request method is not supported, return a 405 Method Not Allowed response
    return Response({
        "message": APIMessages.METHOD_NOT_ALLOWED.value,
        "status": METHOD_NOT_ALLOWED,
    })


@api_view(['POST'])
def addEvents(request):
    global events
    try:
        if request.method == 'POST':
            # Get the new event data from the request payload
            new_event_data = request.data

            # Generate a unique ID for the new event (You can use any appropriate method to generate IDs)
            new_event_data['id'] = str(len(events) + 1)

            # Append the new event data to the events list
            events.append(new_event_data)

            # Return the updated events list as a JSON response
            return JsonResponse(events, safe=False)

        # For other HTTP methods, return the events list as a JSON response
        return JsonResponse(events, safe=False)
    except Exception as e:
        return JsonResponse({'error': APIMessages.INTERNAL_SERVER_ERROR.value}, status=FAILED_STATUS_CODE)

@api_view(['PUT'])
def updateEvents(request):
    try:
        return JsonResponse(events, safe=False)
    except Exception as e:
        return JsonResponse({'error': APIMessages.INTERNAL_SERVER_ERROR.value}, status=FAILED_STATUS_CODE)

@api_view(['DELETE'])
def deleteEvents(request):
    try:
        return JsonResponse(events, safe=False)
    except Exception as e:
        return JsonResponse({'error': APIMessages.INTERNAL_SERVER_ERROR.value}, status=FAILED_STATUS_CODE)

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def getAllAppointments(request, id=None):
    try:
        if request.method == "GET":
            # page_number = int(request.args.get("page_number", 0))
            # page_size = int(request.args.get("page_size", 10))
            # search_value = request.args.get("search_value", "")
            # search_columns = request.args.get("search_columns", "").split(",")
            # sort_by = request.args.get("sort_by", "id")
            # sort_direction = request.args.get("sort_direction", "desc")
            if id is not None:
                try:
                    appointment = Appointment.objects.get(id=id)
                    serializer = AppointmentSerializer(appointment, many=False)
                    return Response({
                        "data": {
                            "count": 1,
                            "rows": [serializer.data]
                        },
                        "message": APIMessages.APPOINTMENT_RETRIEVED.value,
                        "status": SUCCESS_STATUS_CODE,
                    })
                except Appointment.DoesNotExist:
                    return Response({
                        "message": APIMessages.APPOINTMENT_NOT_FOUND.value,
                        "status": NOT_FOUND_STATUS,
                    })
            else:
                # Retrieve all customers
                all_appointments = Appointment.objects.all()
                # data = my_view(request, all_appointments)
                # Serialize all customers
                serializer = AppointmentSerializer(all_appointments, many=True)

                # Return the serialized data in the response
                return Response({
                    "data": {
                        "count": len(all_appointments),
                        "rows": serializer.data
                    },
                    "message": APIMessages.ALL_APPOINTMENT_RETRIEVED.value,
                    "status": SUCCESS_STATUS_CODE,
                })

        elif request.method == "DELETE":
            if id is not None:
                try:
                    appointment = Appointment.objects.get(id=id)
                    appointment.delete()
                    return Response({
                        "message": APIMessages.APPOINTMENT_DELETED.value,
                        "status": SUCCESS_STATUS_CODE,
                    })
                except Employee.DoesNotExist:
                    return Response({
                        "message": APIMessages.APPOINTMENT_NOT_FOUND.value,
                        "status": NOT_FOUND_STATUS,
                    })
            else:
                return Response({
                    "message": APIMessages.APPOINTMENT_NOT_MENTIONED.value,
                    "status": NOT_FOUND_STATUS,
                })

        elif request.method == "POST":
            # import ipdb;ipdb.set_trace()

            customer_id = request.data['customer_id']
            customer_user = User.objects.get(id=customer_id)
            booking_platform = str(request.data["booking_platform"]).upper()

            start_time = request.data["start_time"]
            start_time = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S.%fZ')
            start_time = start_time.strftime('%H:%M:%S')
            end_time = str(datetime.datetime.strptime(f"{start_time}", "%H:%M:%S") + datetime.timedelta(minutes=30)).split(" ")[1]

            date_selected = request.data["date"]
            date_selected = datetime.datetime.strptime(date_selected, '%Y-%m-%dT%H:%M:%S.%fZ')
            date_selected = date_selected.strftime('%m/%d/%Y')
            date_selected = datetime.datetime.strptime(date_selected, "%m/%d/%Y")
            date_selected = date_selected.strftime("%Y-%m-%d")

            booking_status = "Booked"
            is_paid = False

            salon_id = request.data["salon_id"]
            branch_id = request.data["branch_id"]

            salon = SalonDetails.objects.get(id=salon_id)
            branch = Branch.objects.get(id=branch_id)
            user_id = request.data["user_id"]

            user = User.objects.filter(id=user_id).first()

            salon_details = SalonDetails.objects.filter(user=user).first()

            services = request.data["services"]
            staff_assigned = request.data["staff_assigned"]

            services = [i['attribute_id'] for i in services]
            staff = [i['attribute_id'] for i in staff_assigned]

            services = Service.objects.filter(user=salon_details, branch=branch, id__in=services)
            staff = Employee.objects.filter(branch=branch, id__in=staff,status="Active")

            total_price = 0.0
            for i in list(services):
                total_price += int(i.price)

            if booking_platform == "BOOK APPOINTMENT":
                booking_status = "Booked"
                is_paid = False
            else:
                booking_platform = "WALK IN"
                date_selected = datetime.date.today()
                booking_status = "Availed"
                is_paid = True

            res = ''.join(random.choices(string.ascii_uppercase +
                                        string.digits, k=12))

            appointment = Appointment.objects.create(
                user=customer_user,
                salon=salon,
                branch=branch,
                totalPrice=total_price,
                order_id=str(res),
                isPaid=is_paid,
                date=date_selected,
                start_time=start_time,
                end_time=end_time,
                createdAt=datetime.date.today(),
                booking_platform=booking_platform,
                booking_status=booking_status
            )

            appointment.save()

            for emp in staff:
                appointment.staff_assigned.add(emp)
                appointment.save()
            for service in services:
                appointment.service.add(service)
                appointment.save()

            if appointment.booking_platform == "WALK IN":
                invoice = Invoice(transaction="trans_" + str(res), date_created=datetime.datetime.today(),
                                date_updated=datetime.datetime.today(), total=total_price, status=True)
            else:
                invoice = Invoice(transaction="trans_" + str(res), date_created=datetime.datetime.today(),
                                date_updated=datetime.datetime.today(), total=total_price)

            invoice.save()
            inv = Invoice.objects.get(transaction="trans_" + res)
            inv.appointment.add(appointment)
            inv.save()

            return Response({
                "message": APIMessages.APPOINTMENT_CREATED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        elif request.method == "PUT":
            # TODO: Uncomment this line for debugging with ipdb
            # import ipdb; ipdb.set_trace()

            # Extract data from the request
            booking_platform = str(request.data["booking_platform"]).upper()
            start_time = request.data["start_time"]
            end_time = request.data["end_time"]
            date_selected = request.data["date"]
            salon_id = request.data["salon_id"]
            branch_id = request.data["branch_id"]
            user_id = request.data["user_id"]
            services = request.data["services"]
            staff_assigned = request.data["staff_assigned"]

            # Convert date and time strings to appropriate formats
            start_time = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S.%fZ')
            start_time = start_time.strftime('%H:%M:%S')
            start_time = str(datetime.datetime.strptime(f"{start_time}", "%H:%M:%S") + datetime.timedelta(minutes=30)).split(" ")[1]

            end_time = datetime.datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S.%fZ')
            end_time = end_time.strftime('%H:%M:%S')
            end_time = str(datetime.datetime.strptime(f"{end_time}", "%H:%M:%S") + datetime.timedelta(minutes=30)).split(" ")[1]

            date_selected = datetime.datetime.strptime(date_selected, '%Y-%m-%dT%H:%M:%S.%fZ')
            date_selected = date_selected.strftime('%m/%d/%Y')
            date_selected = datetime.datetime.strptime(date_selected, "%m/%d/%Y")
            date_selected = date_selected.strftime("%Y-%m-%d")

            # Initialize variables
            booking_status = "Booked"
            is_paid = False

            # Get salon and branch details
            salon = SalonDetails.objects.get(id=salon_id)
            branch = Branch.objects.get(id=branch_id)

            # Get user details
            user = User.objects.filter(id=user_id).first()
            salon_details = SalonDetails.objects.filter(user=user).first()

            # Get service and staff details
            services = [i['attribute_id'] for i in services]
            staff = [i['attribute_id'] for i in staff_assigned]
            services = Service.objects.filter(user=salon_details, branch=branch, id__in=services)
            staff = Employee.objects.filter(branch=branch, id__in=staff,status="Active")

            total_price = 0.0
            for i in list(services):
                total_price += float(i.price)

            # Determine booking status and payment status
            if booking_platform == "BOOK APPOINTMENT":
                booking_status = "Booked"
                is_paid = False
            else:
                date_selected = datetime.date.today()
                booking_status = "Availed"
                is_paid = True

            # Update the appointment details
            appointment = Appointment.objects.get(id=id)
            appointment.totalPrice = total_price
            appointment.isPaid = is_paid
            appointment.date = date_selected
            appointment.start_time = start_time
            appointment.end_time = end_time
            appointment.booking_platform = booking_platform
            appointment.booking_status = booking_status
            appointment.save()

            # Update staff and services for the appointment
            appointment.staff_assigned.clear()
            appointment.service.clear()

            for emp in staff:
                appointment.staff_assigned.add(emp)
                appointment.save()
            for service in services:
                appointment.service.add(service)
                appointment.save()

            res = appointment.order_id

            # Update the invoice
            invoice = Invoice.objects.get(transaction="trans_" + str(res))
            invoice.total_price = total_price
            invoice.save()

            # Convert appointment start and end time to appropriate formats
            start_time = f'{appointment.date} {start_time}'
            end_time = f'{appointment.date} {end_time}'
            start_time = str(datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=-5, minutes=-30)).replace(' ', 'T')
            end_time = str(datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=-5, minutes=-30)).replace(' ', 'T')

            ## TODO: Implement Sending Email and Adding Event

            # Serialize the updated appointment and return the response
            serializer = AppointmentSerializer(appointment, many=False)
            return Response({
                "data": {
                    "count": 1,
                    "rows": serializer.data
                },
                "message": APIMessages.APPOINTMENT_UPDATED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        
    except Exception as e:
        # If an unexpected error occurs, return an error response
        return Response({
            "message": APIMessages.ERROR.value,
            "status": FAILED_STATUS_CODE,
        })

    # If the request method is not supported, return a 405 Method Not Allowed response
    return Response({
        "message": APIMessages.METHOD_NOT_ALLOWED.value,
        "status": METHOD_NOT_ALLOWED,
    })