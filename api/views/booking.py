import datetime
from api.common import apply_filters, custom_pagination, get_all_table_records, ist_converted_time, log_error_with_api_endpoint
from api.decorators import jwt_authentication_required
from api.throttles import SustainedRateThrottle
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from api.serializers import AppointmentSerializer, InvoiceSerializer
from api.views.message_notification.review_notification import send_review_notification_to_customer
from backend.models import Branch, Service, Customer, Appointment, Employee, Invoice, SalonDetails, User
import random
import string
from django.utils.dateparse import parse_datetime
from api.constants import *
import json
from django.utils import timezone
from datetime import timedelta
from api.views.slot import check_seat_availability
from api.views.salary import staffSalary
import pytz
# credentials = get_credentials()
# http = credentials.authorize(httplib2.Http())

# service_calendar = discovery.build('calendar', 'v3', http=http)


@api_view(['POST'])
def check_seat_available(request):
    data = request.data
    booking_platform = str(request.data["booking_platform"]).upper()

    start_time = request.data["start_time"]
    start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    start_time = (start_time.strftime('%H:%M:%S'))
    start_time = datetime.datetime.strptime(start_time, "%H:%M:%S")

    date_selected = request.data["booking_date"]
    date_selected = parse_datetime(date_selected)

    if date_selected == None:
        date_selected = datetime.date.today()

    salon_id = request.data["salon_id"]
    user_id = request.data["user_id"]
    branch_id = request.data['branch_id']

    user = User.objects.get(id=user_id)
    branch = Branch.objects.get(id=branch_id)
    salon_details = SalonDetails.objects.get(user=user, id=salon_id)

    services_id = []
    staff_objects_list = []

    # Iterate through serviceAssignments
    for assignment in data['service']:
        # Extract and append service_ids to the services_id list
        service_ids = [service['attribute_id']
                       for service in assignment['service']]
        services_id.extend(service_ids)

        # Get the staff objects for the current assignment
        staff_objects = assignment.get('staff', [])

        # Query Employee objects based on the extracted attribute_ids
        staff_attribute_ids = [staff['attribute_id']
                               for staff in staff_objects]
        staff_query = Employee.objects.filter(id__in=staff_attribute_ids,status="Active")

        # Convert the Employee queryset to a list
        staff_objects_list.append(list(staff_query))

    services = Service.objects.filter(
        user=salon_details, branch=branch, id__in=services_id)

    service_time_taken = []
    for service in services:
        service_time_taken.append(service.time_for_each_service)

    if booking_platform == "BOOK APPOINTMENT":
        date_selected = date_selected
    else:
        booking_platform = "WALK IN"
        date_selected = datetime.date.today()

    # all Check-in Time & Check-out Time for Each Appointment
    start_time_slot = []
    end_time_slot = []
    for i in range(0, len(services)):
        time_till_now = sum(service_time_taken[0:i])
        start_time_slot.append(
            (start_time + timedelta(minutes=time_till_now)).strftime("%H:%M:%S"))
        end_time_slot.append(
            (start_time + timedelta(minutes=time_till_now + service_time_taken[i])).strftime("%H:%M:%S"))

    check_seat = check_seat_availability(
        request, branch, start_time_slot, end_time_slot, date_selected, staff_objects_list)
    response_data = check_seat.content.decode('utf-8')
    response = json.loads(response_data)

    if response['status'] != 200:
        return Response({
            'message': response['message'],
            'status': response['status']
        })
    else:
        return Response({
            'message': response['message'],
            'status': response['status']
        })


@api_view(['POST', 'PUT', 'GET', 'DELETE'])
@throttle_classes([SustainedRateThrottle])
@jwt_authentication_required
def getAllBookings(request, column_name=None, column_value=None):
    if request.method == 'GET':
        try:
            if column_value is None:
                request_args = request.GET
                salon_id = request_args['salon_id']
                branch_id = request_args['branch_id']

                if branch_id == '-1' and salon_id == '-1':
                    all_appointments = get_all_table_records(
                        request, Appointment)
                else:
                    salon = SalonDetails.objects.get(id=salon_id)
                    branch = Branch.objects.get(salon=salon, id=branch_id)
                    all_appointments = Appointment.objects.filter(branch=branch).order_by('-id')

                if 'customer_id' in request_args:
                    customer = Customer.objects.get(
                        id=request.GET['customer_id'])
                    all_appointments = all_appointments.filter(
                        user_id=customer.user_id)
                if 'employee_id' in request_args:
                    employee = Employee.objects.get(
                        id=request.GET['employee_id'],status="Active")
                    all_appointments = all_appointments.filter(
                        staff_assigned=employee)
                else:
                    pass

                final_appointments_list = apply_filters(Appointment, all_appointments, request_args)

                total_rows = all_appointments.count()
                all_invoice = set(Invoice.objects.filter(
                    appointment__in=final_appointments_list))
                invoice_serializer = InvoiceSerializer(all_invoice, many=True)

                # Call the custom_pagination function to get the paginated items.
                final_appointments_list = custom_pagination(request, final_appointments_list)

                serializer = AppointmentSerializer(final_appointments_list, many=True)
                # Return the serialized data in the response
                return Response({
                    "data": {
                        "count": total_rows,
                        "rows": serializer.data,
                        'invoice_rows': invoice_serializer.data
                    },
                    "message": APIMessages.ALL_BOOKING_RETRIEVED.value,
                    "status": SUCCESS_STATUS_CODE,
                })
            else:
                # Check if column_name is a valid field in the Appointment model
                valid_fields = [f.name for f in Appointment._meta.get_fields()]
                if column_name not in valid_fields:
                    return Response({"message": f"Invalid column name: {column_name}", "status": 400})

                # Build a dynamic filter using double-underscore notation
                filter_kwargs = {
                    f"{column_name}__exact": column_value} if column_name else {}
                
                invoice = Invoice.objects.get(**filter_kwargs)
                serializer = InvoiceSerializer(invoice, many=False)

                data = serializer.data

                main_data = serializer.data['appointment'][0]

                if datetime.datetime.strptime(main_data['start_time'], '%H:%M:%S') <= datetime.datetime.strptime('12:00', '%H:%M'):
                    start_time = '09:00 AM - 12:00 Noon'
                elif datetime.datetime.strptime(main_data['start_time'], '%H:%M:%S') <= datetime.datetime.strptime('18:00', '%H:%M'):
                    start_time = '12:00 Noon - 18:00 PM'
                else:
                    start_time = '18:00 PM - 21:00 PM'

                staff_list = []
                for staff in serializer.data['appointment']:
                    for stf in staff['staff_assigned']:
                        staff_data = {
                            'attribute_id': stf['id'],
                            'attribute_name': stf['first_name'] + " " + stf['last_name']
                        }
                        staff_list.append(staff_data)
                # Create a set of unique items based on 'attribute_id'
                unique_items = {item['attribute_id']
                    : item for item in staff_list}.values()

                # Convert the set back to a list
                staff_list = list(unique_items)

                service_list = []
                for service in serializer.data['appointment']:
                    for serv in service['service']:
                        service_data = {
                            'attribute_id': serv['id'],
                            'attribute_name': serv['name']
                        }
                        service_list.append(service_data)
                # Create a set of unique items based on 'attribute_id'
                unique_items = {item['attribute_id']
                    : item for item in service_list}.values()

                # Convert the set back to a list
                service_list = list(service_list)

                main_data = {
                    'id': data['id'],
                    'customer_id': main_data['customer_id'],
                    'customer_name': main_data['customer_name'],
                    'email': main_data['user']['email'],
                    'booking_date': main_data['booking_date'],
                    'start_time': start_time,
                    'booking_platform': main_data['booking_platform'],
                    'isPaid': bool(main_data['payment_status']),
                    'service': service_list,
                    'staff_assigned': staff_list
                }

                # Return the serialized data in the response
                return Response({
                    "data": {
                        "count": 1,
                        "rows": [main_data]
                    },
                    "message": APIMessages.BOOKING_RETRIEVED.value,
                    "status": SUCCESS_STATUS_CODE,
                })
        except Exception as e:
            log_error_with_api_endpoint(request, e)
            return Response({
                "message": APIMessages.INTERNAL_SERVER_ERROR.value,
                "status": FAILED_STATUS_CODE,
            })
    if request.method == "POST":
        data = request.data
        staff_list = []
        service_list = []
        start_time_list = []
        available_staff_list = []

        staff_objects_list = []

        for datas in data['slot']:
            for staff in data['slot'][datas]:
                if staff in staff_list:
                    pass
                else:
                    staff_list.append(staff)

        date_selected = request.data["booking_date"]

        if date_selected:
            date_selected = parse_datetime(date_selected)
        else:
            date_selected = datetime.datetime()

        if date_selected.date() < datetime.datetime.today().date():
            return Response({
                'message': f'Please select a future date. Please check date and time.',
                'status': 400
            })

        for main_data in data['slot']:
            available_staff = []
            time = []
            service_list.append(main_data)
            for staff in staff_list:
                for status in data['slot'][main_data][staff]:
                    if status['details']['status'] == 'True':
                        if date_selected.date() == datetime.datetime.today().date():
                            if datetime.datetime.strptime(status['details']['time'], '%H:%M').time() < datetime.datetime.now().time():
                                return Response({
                                            'message': f'You Cannot Select Invalid Time',
                                            'status': 400
                                        })
                        time.append(status['details']['time'])
                        available_staff.append(status['details']['id'])

            if len(set(time)) == 1:
                start_time_list.append(datetime.datetime.strptime(time[0], "%H:%M"))
                available_staff_list.append(available_staff)
            else:
                return Response({
                    'message': f'Please Select Same Time Slot for Each Staff in Service :- {main_data}',
                    'status': 500
                })

        customer_id = request.data['customer_id']
        customer_user = Customer.objects.get(id=customer_id).user
        booking_platform = str(request.data["booking_platform"]).upper()


        salon_id = request.data["salon_id"]
        user_id = request.data["user_id"]
        branch_id = request.data['branch_id']

        user = User.objects.get(id=user_id)
        salon = SalonDetails.objects.get(user=user)
        branch = Branch.objects.get(id=branch_id)
        salon_details = SalonDetails.objects.get(user=user, id=salon_id)

        services = Service.objects.filter(branch=branch, name__in=service_list)

        for staff_id in available_staff_list:
            staff_user_list = Employee.objects.filter(id__in=staff_id,status="Active")
            staff_objects_list.append(staff_user_list)

        service_time_taken = []
        for service in services:
            service_time_taken.append(service.time_for_each_service)

        total_price = 0.0
        for i in list(services):
            total_price += int(i.price)

        if booking_platform == "BOOK APPOINTMENT":
            booking_status = "Booked"
            is_paid = False
            date_selected = date_selected
        else:
            booking_platform = "WALK IN"
            date_selected = datetime.date.today()
            booking_status = "Availed"
            is_paid = True


        # all Check-in Time & Check-out Time for Each Appointment
        start_time_slot = []
        end_time_slot = []
        for i in range(0, len(services)):
            if (start_time_list[i] + timedelta(minutes=0)).strftime("%H:%M:%S") in start_time_slot:
                return Response({
                    'message': 'You have Selected same time for same staff in different service..... Please Select Different Time Slot for both Service for same Staff',
                    'status': 400
                })
            try:
                if (start_time_list[i] + timedelta(minutes=service_time_taken[i])).strftime("%H:%M:%S") > (start_time_list[i+1] + timedelta(minutes=0)).strftime("%H:%M:%S"):
                    return Response({
                        'message': 'You have Selected Wrong Start time.. Please Make Sure that End time of first service is always lesser than Start Time of second Service',
                        'status': 400
                    })
            except:
                pass
            start_time_slot.append(
                (start_time_list[i] + timedelta(minutes=0)).strftime("%H:%M:%S"))
            end_time_slot.append(
                (start_time_list[i] + timedelta(minutes=service_time_taken[i])).strftime("%H:%M:%S"))

        appointment_list = []
        order_id_list = []
        total_price = 0
        if date_selected == (datetime.datetime.today()).date():
            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M:%S")
            if current_time >= start_time_slot[0]:
                return Response({
                        'message': 'You have Selected Wrong Time.... Please Select Future Time',
                        'status': 400
                    }) 

        for staff, start_time_slots, end_time_slots, service in zip(staff_objects_list, start_time_slot, end_time_slot, services):
            res = ''.join(random.choices(string.ascii_uppercase +
                                            string.digits, k=12))
            create_order = Appointment(
                user=customer_user,
                salon=salon,
                branch=branch,
                totalPrice=service.price,
                order_id=str(res),
                isPaid=is_paid,
                date=date_selected,
                start_time=start_time_slots,
                end_time=end_time_slots,
                createdAt=datetime.datetime.now(),
                booking_platform=booking_platform,
                booking_status=booking_status,
            )
            create_order.save()
            create_order.service.add(service)
            for staff_assign in staff:
                create_order.staff_assigned.add(staff_assign)
                create_order.save()
            create_order.save()

            order_id_list.append(create_order.order_id)
            appointment_list.append(create_order)
            total_price += create_order.totalPrice

        transaction_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        
        if booking_platform == "WALK IN":
            invoice = Invoice(transaction="trans_"+transaction_id, 
                              date_created=datetime.datetime.today(),
                              date_updated=datetime.datetime.today(), 
                              total=total_price, 
                              status='Paid'
                            )
        else:
            invoice = Invoice(transaction="trans_"+transaction_id, date_created=timezone.now(
            ), date_updated=timezone.now(), total=total_price)

        invoice.save()

        # Adding Booked Appointment(*By User*) Into Created Invoice
        for appointment in appointment_list:
            invoice.appointment.add(appointment)
            invoice.save()

        # Parse the UTC date string
        try:
            utc_date = datetime.datetime.strptime(
                str(invoice.date_created), '%Y-%m-%d %H:%M:%S.%f%z')
        except Exception:
            utc_date = datetime.datetime.strptime(
                str(invoice.date_created), '%Y-%m-%d %H:%M:%S.%f')

        # Define the UTC timezone
        utc_timezone = pytz.timezone('UTC')

        # Convert the datetime object to UTC
        utc_date = utc_date.replace(tzinfo=utc_timezone)

        # Define the Indian Standard Time (IST) timezone
        ist_timezone = pytz.timezone('Asia/Kolkata')

        # Convert the datetime object to IST
        ist_date = utc_date.astimezone(ist_timezone)

        # month Name as a string
        month_name = str(ist_date.strftime('%B')).upper()

        # if booking_platform == "WALK IN":
        # staff_salary = staffSalary(request,invoice,month_name,ist_date,'ADD-SALARY')
        # start_time = f'{appointment.date} {start_time}'
        # end_time = f'{appointment.date} {end_time}'
        # start_time = str(datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=-5,minutes=-30)).replace(' ','T')
        # end_time =  str(datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=-5,minutes=-30)).replace(' ','T')

        ## Sending Email #
        # email_send(branch.branch_name,appointment.createdAt,appointment.user.username,','.join(services),str(total_price),appointment.mode_of_payment,appointment.date,start_time,end_time,appointment.branch.salon.user.email,appointment.user.email)
        ###

        # Adding Event #####
        # event = calendar_event(appointment.branch.address,','.join(services),appointment.date,start_time,end_time,appointment.branch.branch_name,appointment.branch.salon.user.email,appointment.user.email)
        # event = service_calendar.events().insert(calendarId='primary', sendNotifications=True, body=event).execute()
        serializer = AppointmentSerializer(appointment_list, many=True)

        return Response({
            "data": {
                "count": 1,
                "data": serializer.data,
                "invoice_id": invoice.id,
            },
            "message": "Successfully added Booking",
            "status": 200,
        })
        # except Exception as e:
        #     log_error_with_api_endpoint(request, e)
        #     return Response({
        #         "message": APIMessages.INTERNAL_SERVER_ERROR.value,
        #         "status": FAILED_STATUS_CODE,
        #     })
    if request.method == "PUT":
        try:
            data = request.data
            staff_list = []
            service_list = []
            start_time_list = []
            available_staff_list = []

            staff_objects_list = []

            for datas in data['slot']:
                for staff in data['slot'][datas]:
                    if staff in staff_list:
                        pass
                    else:
                        staff_list.append(staff)

            for main_data in data['slot']:
                available_staff = []
                time = []
                service_list.append(main_data)
                for staff in staff_list:
                    for status in data['slot'][main_data][staff]:
                        if status['details']['status'] == 'True':
                            time.append(status['details']['time'])
                            available_staff.append(status['details']['id'])

                if len(set(time)) == 1:
                    start_time_list.append(
                        datetime.datetime.strptime(time[0], "%H:%M"))
                    available_staff_list.append(available_staff)
                else:
                    return Response({
                        'message': f'Please Select Same Time Slot for Each Staff in Service :- {main_data}',
                        'status': 500
                    })

            customer_id = request.data['customer_id']
            customer = Customer.objects.get(id=customer_id)
            customer_user = customer.user
            booking_platform = str(request.data["booking_platform"]).upper()

            salon_id = request.data["salon_id"]
            user_id = request.data["user_id"]
            branch_id = request.data['branch_id']

            user = User.objects.get(id=user_id)
            salon = SalonDetails.objects.get(user=user)
            branch = Branch.objects.get(id=branch_id)
            salon_details = SalonDetails.objects.get(user=user, id=salon_id)

            services = Service.objects.filter(
                user=salon_details, branch=branch, name__in=service_list)

            for staff_id in available_staff_list:
                staff_user_list = Employee.objects.filter(id__in=staff_id,status="Active")
                staff_objects_list.append(staff_user_list)

            service_time_taken = []
            for service in services:
                service_time_taken.append(service.time_for_each_service)

            total_price = 0.0
            for i in list(services):
                total_price += int(i.price)

            if booking_platform == "BOOK APPOINTMENT":
                booking_status = "Booked"
                is_paid = False
            else:
                booking_platform = "WALK IN"
                booking_status = "Availed"
                is_paid = True

            # all Check-in Time & Check-out Time for Each Appointment
            start_time_slot = []
            end_time_slot = []
            for i in range(0, len(services)):
                start_time_slot.append(
                    (start_time_list[i] + timedelta(minutes=0)).strftime("%H:%M:%S"))
                end_time_slot.append(
                    (start_time_list[i] + timedelta(minutes=service_time_taken[i])).strftime("%H:%M:%S"))

            total_price = 0

            invoice = Invoice.objects.get(id=int(data['id']))
            for appointment, staff, start_time_slots, end_time_slots, service in zip(invoice.appointment.all(), staff_objects_list, start_time_slot, end_time_slot, services):
                appointment.user = customer_user
                appointment.totalPrice = service.price
                appointment.isPaid = is_paid
                appointment.start_time = start_time_slots
                appointment.end_time = end_time_slots
                appointment.booking_platform = booking_platform
                appointment.save()
                appointment.staff_assigned.clear()
                appointment.save()
                appointment.service.clear()
                appointment.save()

                for staff in staff:
                    appointment.staff_assigned.add(staff)
                    appointment.save()

                appointment.service.add(service)
                appointment.save()

                total_price += appointment.totalPrice

            invoice.total = total_price
            invoice.save()

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
            log_error_with_api_endpoint(request, e)
            return Response({
                "message": APIMessages.INTERNAL_SERVER_ERROR.value,
                "status": FAILED_STATUS_CODE,
            })
    elif request.method == "DELETE":
        appointment_id = request.GET.get('id')
        branch_id = int(request.GET.get('branch_id'))
        try:
            appointment = Appointment.objects.get(id=appointment_id)
            if appointment.branch.id == branch_id:
                ist_date = ist_converted_time(appointment.createdAt)
                month_name = str(ist_date.strftime('%B')).upper()
                staffSalary(request, appointment, month_name, None, 'DELETE-SALARY') #Remove Staff Salary
                invoice = Invoice.objects.get(appointment=appointment)
                
                appointment.booking_status = "Cancelled by salon"
                appointment.save()

                return Response({
                    'message': APIMessages.DELETE_ALL_BOOKINGS.value,
                    'status': SUCCESS_STATUS_CODE
                })
            else:
                return Response({
                    'message': APIMessages.ERROR.value,
                    'status': BAD_REQUEST_STATUS
                })
        except Exception:
            return Response({
                'message': APIMessages.BOOKING_NOT_FOUND.value,
                'status': BAD_REQUEST_STATUS
            })


@api_view(['POST', 'PUT', 'GET', 'DELETE'])
@throttle_classes([SustainedRateThrottle])
@jwt_authentication_required
def getCustomerBookingHistory(request, customer_id):
    data = request.GET
    try:
        branch = Branch.objects.get(id=data['branch_id'])
        user = Customer.objects.get(id=customer_id).user
        appointment = Appointment.objects.filter(branch=branch, user=user)
        serializer = AppointmentSerializer(appointment, many=True)

        all_invoice = set(Invoice.objects.filter(appointment__in=appointment))
        invoice_serializer = InvoiceSerializer(all_invoice, many=True)
        return Response({
            "data": {
                "count": len(serializer.data),
                "rows": serializer.data,
                'invoice_rows': invoice_serializer.data
            },
            "message": APIMessages.ALL_BOOKING_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        })
    except Exception:
        pass


@api_view(['POST'])
@jwt_authentication_required
def bookingAvailed(request):
    data = request.data
    try:
        id = request.GET.get('id')
        branch_id = int(data['branch_id'])
        branch = Branch.objects.get(id=branch_id)
        appointment = Appointment.objects.get(id=id)
        if appointment.branch.id == branch_id:
            appointment.isPaid = True
            appointment.booking_status = 'Availed'
            appointment.paidAt = datetime.datetime.now()
            appointment.save()
            invoice = Invoice.objects.get(appointment=appointment)
            if invoice.status != 'PAID':
                for apt in invoice.appointment.all():
                    if apt.isPaid == False:
                        return Response({
                            'message': APIMessages.BOOKING_AVAILED.value,
                            'status': SUCCESS_STATUS_CODE
                        })
                invoice.status = "PAID"
                invoice.save()

                ist_date = ist_converted_time(invoice.date_created)
                month_name = str(ist_date.strftime('%B')).upper()
                staff_salary = staffSalary(
                    request, invoice, month_name, ist_date, 'ADD-SALARY')
                
                send_review_notification_to_customer(request,branch,invoice.transaction,appointment.user)

                return Response({
                    'message': APIMessages.BOOKING_AVAILED.value,
                    'status': SUCCESS_STATUS_CODE
                })
            else:
                return Response({
                    'message': APIMessages.ERROR.value,
                    'status': BAD_REQUEST_STATUS
                })
        else:
            return Response({
                'message': APIMessages.ERROR.value,
                'status': BAD_REQUEST_STATUS
            })
    except:
        return Response({
            'message': APIMessages.ERROR.value,
            'status': BAD_REQUEST_STATUS
        })
