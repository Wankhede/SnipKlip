from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from ...models import *
from ...forms import AppointmentForm
import requests
import backend.views.bookings.salon_side.add_bookings
from backend.views.common.conditions import group_match


# user = get_object_or_404(User, pk=request.user.pk)
# payload = {'head': 'Booking added succesfully!', 'body': 'Salon appointment added!'}
# send_user_notification(user=user, payload=payload, ttl=1000)
# Adding Event #####
# event = calendar_event(branch_taken.address,','.join(service_selected),date_selected,start_time,end_time,branch_taken.branch_name,service.branch.salon.user.email,user_booked.email)
# event = service_calendar.events().insert(calendarId='primary', sendNotifications=True, body=event).execute()
#######

def calendar(request):
    return render(request, 'calendar.html')

def get_events(request):
    user = User.objects.get(id=request.user.id)
    if group_match('Manager', request):
        branch = Branch.objects.filter(manager=user)
        appointments = Appointment.objects.filter(branch__in=branch)
    else:
        salon = SalonDetails.objects.get(user=user)
        appointments = Appointment.objects.filter(salon=salon)
    events = []
    try:
        # API endpoint for Indian holidays
        url = "https://date.nager.at/api/v3/PublicHolidays/2023/IN"

        # Fetching data from API
        response = requests.get(url)

        # Parsing JSON data
        data = response.json()
        # Creating list of holidays with required format
        holidays = []
        for holiday in data:
            holiday_date = holiday["date"]
            holiday_title = holiday["name"]
            holidays.append({
                "title": holiday_title,
                "start": holiday_date
            })
    except:
        holidays = [    {        "title": "New Year's Day",        "start": "2023-01-01"    },    {        "title": "Makar Sankranti",        "start": "2023-01-14"    },    {        "title": "Republic Day",        "start": "2023-01-26"    },    {        "title": "Holi",        "start": "2023-03-10"    },    {        "title": "Good Friday",        "start": "2023-04-14"    },    {        "title": "Eid al-Fitr",        "start": "2023-05-29"    },    {        "title": "Independence Day",        "start": "2023-08-15"    },    {        "title": "Gandhi Jayanti",        "start": "2023-10-02"    },    {        "title": "Diwali",        "start": "2023-10-20"    },    {        "title": "Christmas Day",        "start": "2023-12-25"    }]

    for appointment in appointments:
        if appointment.booking_status == 'Booked':
            color = '#007bff'  # blue color for booked appointments
        elif appointment.booking_status == 'Availed':
            color = '#28a745'  # green color for availed appointments
        else:
            color = '#dc3545'  # red color for cancelled appointments
            
        if appointment.booking_platform == 'ONLINE':
            booking_platform = 'Online'
        elif appointment.booking_platform == 'WALK IN':
            booking_platform = 'Walk-in'
        else:
            booking_platform = 'Book Appointment'
        event = {
            "title": appointment.service.first().name,
            "start": str(appointment.date) + "T" + str(appointment.start_time),
            "end": str(appointment.date) + "T" + str(appointment.end_time),
            "color": color,
            "id": appointment.id,
            "booking_status": appointment.booking_status,
            "booking_platform": booking_platform,
            "staff_assigned": str(appointment.staff_assigned) if appointment.staff_assigned else None
        }
        events.append(event)
    events.extend(holidays)
    return JsonResponse(events, safe=False)

def create_event(request):
    appointment = add_bookings.AddBooking(request)
    return JsonResponse({"success": True})

def update_event(request, event_id):
    appointment = get_object_or_404(Appointment, pk=event_id)
    form = AppointmentForm(request.POST or None, instance=appointment)
    if form.is_valid():
        appointment = form.save(commit=False)
        appointment.updated_by = request.user
        appointment.updated_at = timezone.now()
        appointment.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})

def delete_event(request, event_id):
    appointment = get_object_or_404(Appointment, pk=event_id)
    if request.method == "POST":
        appointment.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})
