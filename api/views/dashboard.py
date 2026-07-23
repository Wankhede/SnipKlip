from datetime import datetime,date
from api.decorators import jwt_authentication_required
from api.throttles import SustainedRateThrottle
from rest_framework.throttling import UserRateThrottle
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from backend.models import Branch, Service, Customer, Appointment, Salary, Expense, Employee, Invoice, BranchCustomerMobile, SalonDetails, User
from api.constants import *

@api_view(['GET'])
@throttle_classes([SustainedRateThrottle])
@jwt_authentication_required
def getDashboardDetails(request):
    if request.method == "GET":
        selected_branch_id = request.GET.get('branch_id') or request.data.get('branch_id')
        user_id = request.GET.get('user_id') or request.data.get('user_id')
        if selected_branch_id in (None, '', 'null', 'undefined') or user_id in (None, '', 'null', 'undefined'):
            return Response({
                "message": APIMessages.USER_OR_BRANCH_NOT_EXISTS.value,
                "status": BAD_REQUEST_STATUS,
            }, status=BAD_REQUEST_STATUS)

        # Get bookings information for today and upcoming bookings
        try:
            todays_booking = Appointment.objects.filter(date=date.today(), branch_id=selected_branch_id).count()
            todays_income = sum(list(Appointment.objects.filter(date=date.today(),isPaid=True, branch_id=selected_branch_id).values_list('totalPrice', flat=True)))
            todays_walk_in_booking = len(list(Appointment.objects.filter(date=date.today(), branch_id=selected_branch_id, booking_platform="WALK IN")))
            todays_online_booking = len(list(Appointment.objects.filter(date=date.today(), branch_id=selected_branch_id, booking_platform="ONLINE")))

            # upcoming_bookings = Appointment.objects.filter(date=date.today(), branch_id=selected_branch_id).order_by('start_time')
            staff_list = Employee.objects.filter(branch_id=selected_branch_id,status="Active")
            appointment = Appointment.objects.filter(isPaid=False,branch_id=selected_branch_id,date=date.today())
            upcoming_bookings = []
            for appoint in appointment:
                upcoming_bookings.append({'id':appoint.id,
                                          'first_name':appoint.user.first_name if appoint.user else '',
                                          'last_name':appoint.user.last_name if appoint.user else '',
                                          'staff_assigned':User.objects.filter(id__in=appoint.staff_assigned.all().values_list('user',flat=True)).values_list('username',flat=True),
                                          'booking_platform':appoint.booking_platform,
                                          'date':appoint.date,
                                          'order_id':appoint.order_id,
                                          'total_price':appoint.totalPrice,
                                          'service':appoint.service.all().values_list('name',flat=True),
                                          'discount_price':appoint.discount_price,
                                          'start_time':appoint.start_time,
                                          'end_time':appoint.end_time
                                        })
        except Exception:
            return Response({
                "message": APIMessages.INTERNAL_SERVER_ERROR.value,
                "status": FAILED_STATUS_CODE,
            }, status=FAILED_STATUS_CODE)

        # Return the serialized data in the response
        return Response({
            "data": {
                'todaysBooking': todays_booking,
                'todaysIncome': todays_income,
                'todaysWalkInBooking': todays_walk_in_booking,
                'todaysOnlineBooking': todays_online_booking,
                'upcomingBookings': upcoming_bookings,
            },
            "message": APIMessages.ALL_BOOKING_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        })
