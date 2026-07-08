from mailbox import Mailbox
from pyexpat.errors import messages

from django.shortcuts import redirect
from requests import Response
from backend.models import *
import datetime
import httplib2
from apiclient import discovery
from django.conf import settings
from sendgrid import SendGridAPIClient
from django.http import JsonResponse
from backend.views.vendor.essentials import get_user_salon_branch_details, group_match
import json
from cryptography.fernet import Fernet

# authorize razorpay client with API Keys.
credentials = get_credentials()
http = credentials.authorize(httplib2.Http())
service_calendar = discovery.build('calendar', 'v3', http=http)
User = get_user_model()
# 0 2 * * * wget --quiet -O -> /home/ubuntu/logs/booking.log "127.0.0.1:8083/daily-mail/?type=booking&token=dx6QJHqEDSGfG7XqKHdp"

def EmployeeBookingMail(request):
    if not group_match('Admin', request) and not group_match('Salon', request) and not group_match('Manager', request):
            return redirect('/')

    try:
        # Get user, salon, and branch details
        pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
    except Exception as e:
        # Handle any exceptions that may occur while retrieving user information
        return Response({'message': 'An error occurred while retrieving user information.'}, status=500)
    
    branch = selected_branch
    assotiated_employee = Employee.objects.filter(branch=branch,status="Active")
    current_month_number = datetime.datetime.now().month
    month_name_uppercase = datetime.date(2023, current_month_number, 1).strftime('%B').upper()
    for employee in assotiated_employee:
        todays_booking = Appointment.objects.filter(date=datetime.date.today(),isPaid=True,staff_assigned=employee)
        till_now_earning = Salary.objects.get(month=month_name_uppercase,employee=employee)


        # Send email
        subject = f"Today's Earning {datetime.date.today()}"
        data = f"Your Todays Booking no. -- {len(todays_booking)}\nTill now earning in this month ({month_name_uppercase}:- {till_now_earning.service_incentive_amount})"
        message_employee = f"Name: {employee.user.username}\nEmail: {employee.user.email}\nPhone: {employee.user.mobile}\n\n{data}"
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [f'{employee.user.email}']  # Replace with the appropriate recipient email

        try:
            message = Mailbox(
                from_email=from_email,
                to_emails=recipient_list,
                subject=subject,
                plain_text_content=message_employee
            )
            sg = SendGridAPIClient(api_key=settings.EMAIL_HOST_PASSWORD)
            response = sg.send(message)

            messages.error(request,'message Sent Successfully')
            return redirect('/employee')
        except Exception as e:
            messages.error(request,f'Error - {e}')
            return redirect('/employee')

# @csrf_exempt
def dailyEmail(request):
    try:
        if 'token' in request.GET:
            if request.GET['token'] == 'dx6QJHqEDSGfG7XqKHdp':
                if request.GET['type'] == 'booking':
                    current_time = utc_to_local(datetime.today())
                    date = str(current_time.day) + '/' + str(current_time.month)
                    user = User.objects.get(username='USERNAME')
                    sys = Appointment.objects.filter(appointment_user=user, submetering_level=0, is_active=True)
                    html_content = '''Hello Team,<br><br>Booking Status:<br><br>
                            <table>
                            <tr>
                                <th> Employee Name </th>
                                <th> Bookings </th>
                            </tr>'''
                    for appointment in sys:
                        appointment_id_data, skip = utility_meter(appointment, user, 1)
                        html_content = html_content + '<tr><td> {} </td><td> {} </td><td> {} </td><td> {} </td><td> {} </td></tr>'.format(
                            appointment.name,
                            str(appointment.data_received_date)[
                            :16], appointment_id_data['kwh'], appointment_id_data['kvah'], appointment_id_data['pf'])
                    html_content = html_content + '</table><br><br>Regards,<br> {} <br>Contact: {}'.format(settings.COMPANY_NAME, settings.DEFAULT_FROM_EMAIL)
                    desc = '🔔 {} Booking Status  {}'.format(settings.COMPANY_NAME, date)
                    subject = '🔔 {} Booking Status {}'.format(settings.COMPANY_NAME, date)
                    from_email = '{} <{}>'.format(settings.COMPANY_NAME, settings.DEFAULT_FROM_EMAIL)
                    msg = EmailMultiAlternatives(subject, desc, from_email, [settings.DEFAULT_FROM_EMAIL],
                                                 headers={'Reply-To': '{} <{}>'.format(settings.COMPANY_NAME, settings.DEFAULT_FROM_EMAIL)})
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()
                    return JsonResponse({'status': 'success', }, status=200)

                else:
                    return JsonResponse({'status': 'failure', 'error': 'incorrect type in request'}, status=500)
            else:
                return JsonResponse({'status': 'failure', 'error': 'invalid token'}, status=500)
        else:
            return JsonResponse({'status': 'failure', 'error': 'no token in request'}, status=500)

    except Exception as e:
        return JsonResponse({'status': 'failure', 'error': str('3: ') + str(e)}, status=500)
