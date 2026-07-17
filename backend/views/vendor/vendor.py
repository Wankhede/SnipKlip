import calendar
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from backend.views.common.pagination import get_pagination
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Avg, Sum
from django.http import Http404, HttpResponseBadRequest, JsonResponse,HttpResponse
from django.shortcuts import render, redirect
from django.core import mail
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from backend.models import *
import json
from backend.views.common.conditions import group_match
from backend.views.message.mail import send_confirmation_mail
from datetime import datetime, date, timedelta
from backend.views.bookings.customer_side.order import TIME_RANGE
from backend.views.message.sms import sms
from backend.views.message.whatsapp import whatsApp
from .essentials import get_user_salon_branch_details, group_match, my_view
from django.db.models.functions import TruncDay
from rest_framework.exceptions import APIException
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404

class SalonList(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'admin-section/salon-list.html'
    queryset = SalonDetails.objects.filter()
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if group_match('Admin',request) == False:
            return redirect('/')
        branches = Branch.objects.all()
        context = {'branches':branches}
        return Response(context)

    def post(self, request):
        return Response({'message': ''})

class Calendar(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/calendar.html'
    queryset = SalonDetails.objects.filter()
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        A view that returns the bookings for a salon, based on the user's permissions and preferences.
        :param request: HTTP request object
        :return: HTTP response object with context variables
        """
        # import ipdb; ipdb.set_trace()
        # Check user permissions
        if not group_match('Admin', request) and not group_match('Salon', request) and not group_match('Manager', request):
            return redirect('/')

        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)

        # Get bookings information for today and upcoming bookings
        try:
            today_booking = Appointment.objects.filter(date=date.today(), branch=selected_branch)
            todays_booking = today_booking.count()
            todays_income = sum(list(today_booking.values_list('totalPrice', flat=True)))
            todays_walk_in_booking = len(list(Appointment.objects.filter(date=date.today(), branch=selected_branch, booking_platform="WALK IN")))
            todays_online_booking = len(list(Appointment.objects.filter(date=date.today(), branch=selected_branch, booking_platform="ONLINE")))
            upcoming_bookings = Appointment.objects.filter(date=date.today(), branch=selected_branch).order_by('start_time')
            staff_list = Employee.objects.filter(branch=selected_branch)
        except Exception as e:
            # Handle any exception that may occur while getting bookings information
            raise APIException('An error occurred while retrieving booking information.') from e

        # Get form details for booking search
        form_details = get_bookings(request)

        staff_set = list(set([staff.user for staff in staff_list]))

        # Define context variables
        context = {
            'todays_booking': todays_booking,
            'todays_income': todays_income,
            'todays_walk_in_booking': todays_walk_in_booking,
            'todays_online_booking': todays_online_booking,
            'upcoming_bookings': upcoming_bookings,
            'staff_set':staff_set,
            'staff_list': staff_list,
            'pk_id': pk_id,
            'user': user,
            'is_admin': is_admin,
            'branches': branches,
            'selected_branch': selected_branch,
            'time_range': form_details['time_range'],
            'service': form_details['service'],
            'customer': form_details['customer'],
            'staff': staff_list,
            'week_date': form_details['week_date'],
        }

        return Response(context)

    def post(self, request):
        return Response({'message': ''})

@csrf_exempt
def get_employee_bookings(request):
    if request.method != "POST":
        # Return an error response if the request method is not POST
        return JsonResponse({'message': 'Only POST requests are allowed.'}, status=405)

    try:
        # Parse the request body into a dictionary
        data = dict(request.POST)

        # Get user, salon, and branch details
        pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)

        # Find the employee associated with the given username
        employee = Employee.objects.filter(user__username=data['username']).first()

        # Find all staff bookings for the employee at the selected branch on the current day
        staff_bookings = Appointment.objects.filter(staff_assigned=employee, date=date.today(), branch=selected_branch)

        # Create a dictionary of staff bookings by time
        staff_bookings_by_time = {}
        for booking in staff_bookings:
            time = booking.start_time.strftime('%I-%p')
            staff_bookings_by_time[time] = {'hour': booking.start_time.hour, 'time_p': booking.start_time.strftime('%p'), 'status': 'Booked'}

        # Return a success response with the staff bookings by time
        return JsonResponse({'success': True, 'staff_bookings': staff_bookings_by_time})
    
    except KeyError as e:
        # Handle any missing or incorrect keys in the request body
        return JsonResponse({'message': f'Missing or invalid key: {e}'}, status=400)

    except Exception as e:
        # Handle any other exceptions that may occur
        return JsonResponse({'message': f'An error occurred: {e}'}, status=500)

class VendorDashboard(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/dashboard.html'
    queryset = SalonDetails.objects.filter()
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        A view that returns the bookings for a salon, based on the user's permissions and preferences.
        :param request: HTTP request object
        :return: HTTP response object with context variables
        """
        # import ipdb; ipdb.set_trace()
        # Check user permissions
        if not group_match('Admin', request) and not group_match('Salon', request) and not group_match('Manager', request):
            return redirect('/')

        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)
        google_key = settings.GOOGLE_CAPTCHA_KEY
        # Get bookings information for today and upcoming bookings
        # try:
        today_booking = Appointment.objects.filter(date=date.today(), branch=selected_branch)
        income = Appointment.objects.filter(date=date.today(),isPaid=True, branch=selected_branch)
        todays_booking = today_booking.count()
        todays_income = sum(list(income.values_list('totalPrice', flat=True)))
        todays_walk_in_booking = len(list(Appointment.objects.filter(date=date.today(), branch=selected_branch, booking_platform="WALK IN")))
        todays_online_booking = len(list(Appointment.objects.filter(date=date.today(), branch=selected_branch, booking_platform="ONLINE")))
        upcoming_bookings = Appointment.objects.filter(date=date.today(), branch=selected_branch).order_by('start_time')
        staff_list = Employee.objects.filter(branch=selected_branch)
        # except Exception as e:
        #     # Handle any exception that may occur while getting bookings information
        #     raise APIException('An error occurred while retrieving booking information.') from e

        # Get form details for booking search
        form_details = get_bookings(request)

        staff_set = staff_list

        # Define context variables
        context = {
            'todays_booking': todays_booking,
            'todays_income': todays_income,
            'todays_walk_in_booking': todays_walk_in_booking,
            'todays_online_booking': todays_online_booking,
            'upcoming_bookings': upcoming_bookings,
            'staff_set':staff_set,
            'staff_list': staff_list,
            'pk_id': pk_id,
            'user': user,
            'is_admin': is_admin,
            'branches': branches,
            'selected_branch': selected_branch,
            'time_range': form_details['time_range'],
            'service': form_details['service'],
            'customer': form_details['customer'],
            'staff': staff_list,
            'week_date': form_details['week_date'],
            'google_key':google_key
        }
        return Response(context)

    def post(self, request):
        return Response({'message': ''})



class OrderSummary(APIView): 
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'order-summary.html'
    queryset = SalonDetails.objects.filter()
    permission_classes = [AllowAny]

    def get_invoice(self, invoice_id):
        try:
            # Load the encryption key and decrypt the token
            key = load_key()
            f = Fernet(key)
            decrypted_token = f.decrypt(bytes(invoice_id[1:-1], 'UTF-8'))
            invoice_id_enc = decrypted_token.decode('utf-8')
            # Retrieve the Invoice object from the database
            return Invoice.objects.get(transaction=invoice_id_enc)
        except (ValueError, IndexError, KeyError, TypeError, Fernet.InvalidToken):
            # Return 404 if the token is invalid or if the Invoice is not found
            raise Http404('Invalid or expired invoice link')

    def get(self, request, invoice_id):
        invoice = self.get_invoice(invoice_id)

        # Calculate the total discount applied on the invoice
        total_discount = sum(
            appointment.discount_price if appointment.discount_price is not None else 0
            for appointment in invoice.appointment.all()
        )

        # Calculate the GST and the total amount
        gst = int(invoice.total * 0.18)
        total_amount = invoice.total - total_discount + gst

        # Retrieve the PaymentMode object Associated with this Invoice, if any
        if invoice.status:
            payment_mode = PaymentMode.objects.get(invoice=invoice)
        else:
            payment_mode = None

        return Response({
            'payment_mode': payment_mode,
            'gst_added': gst,
            'total_discount': total_discount,
            'message': '',
            'invoice': invoice,
            'total_amount': total_amount,
            'invoice_transaction': invoice_id,
        })

    def post(self, request, invoice_id):
        """
        Handle POST requests to the OrderSummary view.
        """
        # Load the encryption key
        key = load_key()
        f = Fernet(key)

        # Encrypt the invoice ID parameter
        encrypted_token = f.encrypt(invoice_id.encode('utf-8'))


        # Retrieve the Invoice object corresponding to the given invoice ID
        try:
            invoice = Invoice.objects.get(transaction=invoice_id)
        except Invoice.DoesNotExist:
            raise Http404('Invoice not found')
        
        if invoice.status:
            ##################### Send Notification ##########################
            share_invoice = request.POST.get('share_invoice_on')
            if share_invoice:
                if share_invoice == "DO_NOT_WANT_TO_SHARE":
                    pass
                else:
                    if share_invoice == "WHATSAPP":
                        pass  # TODO: send notification on WhatsApp
                    elif share_invoice == "EMAIL":
                        pass  # TODO: send notification on email
                    elif share_invoice == "SMS":
                        pass  # TODO: send notification on SMS
                    return render(request,'vendor/success_page.html',{'invoice':invoice,'encrypted_token':encrypted_token})
            ################# End Send Notification ##################

        else:
            # Parse and validate the user inputs
            method_count = request.POST.get('method_count')
            total_discount = float(request.POST.get('total_discount', 0))
            include_gst = request.POST.get('include_gst')
            tax_added = request.POST.get('tax')


            ############ (Start) Adding Payment Mode #############################
            payment_modes = {
                'UPI': 0,
                'CARD': 0,
                'CASH': 0,
                'OTHERS': 0,
            }
            
            for i in range(1,int(method_count)+1):
                selected_mode = request.POST.get(f'mode_of_payment_{i}')
                if request.POST.get(f'payment_recieved_{i}') == "None" or request.POST.get(f'payment_recieved_{i}') == "" or not request.POST.get(f'payment_recieved_{i}'):
                    payment_recieved = 0.0
                else:
                    payment_recieved = request.POST.get(f'payment_recieved_{i}')

                if selected_mode == "UPI":
                    payment_modes['UPI'] = payment_recieved

                if selected_mode == "CARD":
                    payment_modes['CARD'] = payment_recieved

                if selected_mode == "CASH":
                    payment_modes['CASH'] = payment_recieved

                if selected_mode == "OTHERS":
                    payment_modes['OTHERS'] = payment_recieved

            payment_mode = PaymentMode(
                        upi = payment_modes['UPI'],
                        card = payment_modes['CARD'],
                        cash = payment_modes['CASH'],
                        other = payment_modes['OTHERS'],
                        invoice = invoice
            )

            payment_mode.save()
            ############ (End) Adding Payment Mode #############################



            # All Payment Mode Amount
            all_mode = {'UPI':float(payment_mode.upi),'CASH':float(payment_mode.cash),'CARD':float(payment_mode.card),'OTHERS':float(payment_mode.other)}
            
            # Most Amount Recieved Method
            mode_of_payment = list(sorted(all_mode, key=all_mode.get, reverse=True))[0]

            #Sum of Payment Recieved on all Mode of Payment
            payment_recieved = (int(all_mode['UPI']) + int(all_mode['CASH']) + int(all_mode['CARD']) + int(all_mode['OTHERS']))



        ################# (Start) Updating Invoice ######################
            if include_gst == "on":
                include_gst = True
            else:
                include_gst = False

            invoice.tax_added = tax_added
            invoice.mode_of_payment = mode_of_payment
            invoice.discount_added = total_discount

            after_discount = (invoice.total - (total_discount/100*invoice.total)) # Amount(After Disocunt Added)
            gst = after_discount * 0.18   # Calculating GST (After Discount)

            if not include_gst:
                invoice.due_payment = after_discount - payment_recieved # Due Payment(Payment which is to be Paid)
                invoice.actual_amount = after_discount # Amount(After Discount Added, GST Not Included)
            else:
                invoice.due_payment = (after_discount + gst) - payment_recieved #(Payment which is to be Paid)
                invoice.actual_amount = after_discount + gst # Amount(After Discount Added, GST Included)
            invoice.save()
        #################### (End) Updating Invoice ######################


            now = datetime.now()
            month = str(calendar.month_name[now.month]).upper()


            #### (Start) Adding Discount Price To Appointment ################
            for appointment in invoice.appointment.all():
                if request.POST.get(f'discount-{appointment.id}') == "" or request.POST.get(f'discount-{appointment.id}') == None:
                    discount = 0
                else:
                    discount = int(request.POST.get(f'discount-{appointment.id}'))
                customer_appointment = Appointment.objects.get(id=appointment.id)
                customer_appointment.discount_price = discount
                customer_appointment.isPaid = True
                customer_appointment.booking_status = "Availed"
                customer_appointment.save()
            ################## (Ending) Adding Discount Price To Appointment #############
                

            ################ Adding Service Incentive to staff (Start) ############################
                staff_count = appointment.staff_assigned.count()
                for staff in appointment.staff_assigned.all():
                    stf = Employee.objects.get(id=staff.id)
                    service_incentive_amount = ((stf.service_incentive/staff_count)/100 * (int(customer_appointment.totalPrice) - (int(customer_appointment.discount_price))))
                    if Salary.objects.filter(employee=stf,month=month):
                        salary = Salary.objects.get(employee=stf,month=month)
                        salary.total_salary = int(service_incentive_amount) + int(salary.total_salary)
                        salary.service_incentive_amount = int(salary.service_incentive_amount) + int(service_incentive_amount)
                        salary.save()
                    else:
                        salary = Salary(employee=stf,month=month,total_salary=service_incentive_amount,service_incentive_amount=service_incentive_amount)
                        salary.save()
            ################ Adding Service Incentive to staff (End) ############################

            invoice.status = True
            invoice.save()


            #### Adding Branch to Customer Table #######
            appointment = invoice.appointment.first()
            customer_user = Customer.objects.get(user = appointment.user)
            if BranchCustomerMobile.objects.filter(branch=appointment.branch,customer_user=customer_user):
                pass
            else:
                branch_mobile = BranchCustomerMobile(branch=appointment.branch,customer_user=customer_user,mobile=customer_user.user.mobile)
                branch_mobile.save()

                customer_user.mobile_number.add(branch_mobile)
                customer_user.save()
            
        return redirect(f'/order-summary/{encrypted_token}')
    



class VendorEarnings(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/earnings.html'
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


        # Get the SalonDetails instance for the current user
        try:
            salon = SalonDetails.objects.get(user=user)
        except ObjectDoesNotExist:
            return Response({'error': 'SalonDetails not found for the current user'}, status=404)


        # Get the invoices associated with the branches
        bills = Invoice.objects.filter(appointment__branch = selected_branch)
        set_bills = set(bills)
        bills = list(set_bills)


        # get the current month and year
        now = datetime.now()
        month = now.month
        year = now.year

        # calculate the total Price in Invoice for the current month
        total = Invoice.objects.filter(appointment__branch = selected_branch,date_created__month=month, date_created__year=year, status=True).aggregate(Sum('total'))['total__sum']

        # if there are no invoices for the current month, set the total to 0
        if not total:
            total = 0.0

        # print the total

        # group the invoices by day and calculate the daily total
        daily_totals = Invoice.objects.filter(appointment__branch = selected_branch,status=True).annotate(day=TruncDay('date_created')).values('day').annotate(total=Sum('total')).order_by('day')


        # print the average daily total
        average_daily_total = daily_totals.aggregate(Avg('total'))['total__avg']

        # if there are no invoices, set the average daily total to 0
        if not average_daily_total:
            average_daily_total = 0.0



        # print the total appointments
        total_appointments = Appointment.objects.filter(branch=selected_branch,date__month=month, date__year=year).count()

        #Print Total Due Payment (All Time)
        all_appointment = Appointment.objects.filter(branch=selected_branch)
        related_invoice = Invoice.objects.filter(appointment__in=all_appointment).distinct()
        total_due_payments = sum(list(related_invoice.values_list('due_payment',flat=True)))
        
        #Payment Split Among all Payment Method
        upi = sum(list(Invoice.objects.filter(appointment__branch=selected_branch,mode_of_payment='UPI').values_list('actual_amount',flat=True)))
        cash = sum(list(Invoice.objects.filter(appointment__branch=selected_branch,mode_of_payment='CASH').values_list('actual_amount',flat=True)))
        card = sum(list(Invoice.objects.filter(appointment__branch=selected_branch,mode_of_payment='CARD').values_list('actual_amount',flat=True)))
        other = sum(list(Invoice.objects.filter(appointment__branch=selected_branch,mode_of_payment='OTHERS').values_list('actual_amount',flat=True)))
        
        
        ###################### Pagination ###################
        paginated_query = get_pagination(request,bills,10)
        ###############################


        # Return the response
        context = {
            'key': 'Billing',
            'bills': bills,
            'page': '',
            'pages': '',
            'pk_id': pk_id,
            'user': user,
            'is_admin': is_admin,
            'branches': branches,
            'selected_branch': selected_branch,
            'total':total,
            'average_daily_total':average_daily_total,
            'total_appointments':total_appointments,
            'total_due_payments':total_due_payments,
            'upi':upi,
            'card':card,
            'cash':cash,
            'others':other,
            'num_pages':paginated_query['num_pages'],
            'next_page':paginated_query['next_page'],
            'previous_page':paginated_query['previous_page'],
            'page_split':paginated_query['page_split'],
            'page_list':paginated_query['page_list'],
            'start_index':paginated_query['start_index'],
            'current_page':paginated_query['current_page'],
            'end_index':paginated_query['end_index'],
            'total_entries':paginated_query['total_entries'],
        }
        # Merge context dictionary with data dictionary returned by my_view
        return Response(context)


    def post(self, request):
        return Response({'message': ''})

class VendorReviews(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/reviews.html'
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


        total_reviews = len(Review.objects.filter(branch=selected_branch))
        if total_reviews == 0:
            total_reviews = 1
            total_reviewss = 0
        else:
            total_reviewss = total_reviews
            
        reviews = Review.objects.filter(branch=selected_branch)
        average_rating = sum(list(Review.objects.filter(branch=selected_branch).values_list('rating',flat=True)))/total_reviews
        rating_5 = (len(Review.objects.filter(branch=selected_branch,rating=5.0))/total_reviews)*100
        rating_4 = (len(Review.objects.filter(branch=selected_branch,rating=4.0))/total_reviews)*100
        rating_3 = (len(Review.objects.filter(branch=selected_branch,rating=3.0))/total_reviews)*100
        rating_2 = (len(Review.objects.filter(branch=selected_branch,rating=2.0))/total_reviews)*100
        rating_1 = (len(Review.objects.filter(branch=selected_branch,rating=1.0))/total_reviews)*100
        if total_reviewss == 0:
            total_reviews = 0
        else:
            total_reviews = total_reviews
        context = {'rating_5':rating_5,"rating_4":rating_4,'rating_3':rating_3,'rating_2':rating_2,'rating_1':rating_1,'average_rating':average_rating,'total_review':total_reviews,'key':'Reviews','reviews': reviews, 'page': '', 'pages': '','pk_id':pk_id, 'user':user, 'is_admin':is_admin,
                    'selected_branch':selected_branch, 'branches':branches}
        # Call custom view function to process employee data
        data = my_view(request, reviews)
        # Merge context dictionary with data dictionary returned by my_view
        context = {**context, **data}
        return Response(context)

    def post(self, request):
        return Response({'message': ''})

class AddListings(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/add-listings.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.filter()

    def get(self, request):
        if group_match('Salon',request) == False:
            return redirect('/')
        return Response({'key': 'Add Listings', 'data': '', 'page': '', 'pages': ''})

    def post(self, request):
        if group_match('Salon',request) == False:
            return redirect('/')
        return Response({'message': ''})

class AddLeave(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/add-leave.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.filter()


    def get(self, request):
        if group_match('Salon',request) == False:
            return redirect('/')
        return Response({'key': 'Add Leave', 'data': '', 'page': '', 'pages': ''})

    def post(self, request):
        if group_match('Salon',request) == False:
            return redirect('/')
        name = request.POST.get('name')
        days = request.POST.get('days')
        date_selected = request.POST.get('date_selected')
        reason = request.POST.get('reason')
        mail.send_mail(f"Request for Leave Approval",f"Hello,\n\n{name} wants leave for {days} days.\nReason: {reason}\n\nTeam {settings.COMPANY_NAME}",
                settings.DEFAULT_FROM_EMAIL,[settings.DEFAULT_EMAIL])
        messages.success(request,"Leave request sent.")
        return redirect(request.path)

class ManagerView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/leave-requests.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.filter()

    def get(self, request):
        # Retrieve all leave requests from the database
        leave_requests = Leave.objects.all()
        return render(request, self.template_name, {'leave_requests': leave_requests})

    def post(self, request):
        # Get the ID of the leave request that was approved or rejected
        leave_request_id = request.POST.get('leave_request_id')
        leave_request = Leave.objects.get(pk=leave_request_id)
        if 'approve' in request.POST:
            # Approve the leave request
            leave_request.status = 'approved'
            leave_request.save()
            messages.success(request, f"Leave request {leave_request.id} approved!")
        elif 'reject' in request.POST:
            # Reject the leave request
            leave_request.status = 'rejected'
            leave_request.save()
            messages.warning(request, f"Leave request {leave_request.id} rejected!")
        # Redirect to the manager view
        return redirect('manager_view')

class SalarySlip(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'salary-slip.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.all()

    def get(self, request, first_name, last_name, username, month):
        # Validate the request
        if not group_match('Salon', request):
            return redirect('/')
        
        try:
            # Retrieve user information
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)
        
        # Retrieve employee and salary information
        if User.objects.filter(username=username, first_name=first_name, last_name=last_name):
            emp_user = User.objects.get(username=username, first_name=first_name, last_name=last_name)
        else:
            return render(request,'error.html')
        
        employee = Employee.objects.get(user=emp_user)
        if Salary.objects.filter(employee=employee, month=month):
            salaryDetails = Salary.objects.get(employee=employee, month=month)
        else:
            return render(request,'error.html')
        
        # Return the response
        return Response({
            'key': 'Add Salary',
            'data': '',
            'page': '',
            'pages': '',
            'pk_id': pk_id,
            'user': user,
            'is_admin': is_admin,
            'selected_branch': selected_branch,
            'emp_user': emp_user,
            'employee': employee,
            'salaryDetails': salaryDetails,
        })

class AddSalary(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/add-salary.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.all()

    def get(self, request,employee_id,branch_id):

        # Validate the request
        if not group_match('Salon', request):
            return redirect('/')
        
        # Retrieve user and employee information
        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
            staff_list = Employee.objects.filter(branch=selected_branch)
        except Exception as e:
            # Handle exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)
        
        try:
            branch = Branch.objects.get(id=branch_id)
            employee = Employee.objects.get(id=employee_id,branch=branch)
            base_salary = employee.base_salary
        except Exception:
            return redirect(f'/employee/?branch={selected_branch.id}')        
        
        # Retrieve the months for which salaries are not paid
        MONTH = list(set(Salary.objects.filter(employee=employee,paid=False).values_list('month', flat=True)))
        
        # if len(MONTH) == 0:
        #     messages.error(request,'Already Paid Payment For All Month')
        #     return redirect(f'/employee-detail/{employee.user.id}/{employee.user.username}/?branch={selected_branch.id}')
        
        # Return the response
        return Response({
            'key': 'Add Salary',
            'data': '',
            'page': '',
            'pages': '',
            'pk_id': pk_id,
            'user': user,
            'is_admin': is_admin,
            'selected_branch': selected_branch,
            'employee_list': staff_list,
            'branches': branches,
            'month': MONTH,
            'employee':employee,
            'base_salary':base_salary,
        })

    def post(self, request,employee_id,branch_id):
        # Validate the request
        if not group_match('Salon', request):
            return redirect('/')
        
        try:
            # Retrieve user and employee information
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
            staff_list = Employee.objects.filter(branch=selected_branch)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)


        selected_month = request.POST.get('selected_month')
        basic_salary = request.POST.get('basic-salary')
        message = request.POST.get('message')
        
        if not all([employee_id, selected_month, basic_salary]):
            # If any required fields are missing, return a bad request response
            return HttpResponseBadRequest('Missing required fields')

        try:
            employee = Employee.objects.get(id=employee_id, branch=selected_branch)
            salary = Salary.objects.filter(employee=employee, month=selected_month, paid=False)
            if salary.exists():
                salary = salary.first()
                salary.paid = True
                salary.basic = basic_salary
                salary.note = message
                salary.total_salary += int(basic_salary)
                salary.date_issued = date.today()
                salary.save()
                mail.send_mail(f"Salary of {salary} added to your account",
                                f"Hello {employee.user.first_name},\n\nSalary of {salary} added to your account.\n\nTeam {settings.COMPANY_NAME}",
                                settings.DEFAULT_FROM_EMAIL,[settings.DEFAULT_EMAIL])
                messages.success(request, 'Payment Done For Selected Month')
            else:
                messages.error(request, 'Already Provided Payment For This Month')

        except ObjectDoesNotExist:
            # Handle the case where the employee or selected branch does not exist
            return HttpResponseBadRequest('Invalid employee or branch')

        return redirect(f'/add-salary/{employee_id}/{branch_id}?branch={selected_branch.id}')

def ShowIncentive(request):
    if request.method == 'POST':
        # Validate the selected_option and selected_month
        selected_option = request.POST.get('selected_option')
        month = request.POST.get('selected_month')
        if not (selected_option and month):
            response_data = {
                'service_incentive': '<span>Select Both (User and Month)</span>',
                'product_incentive': '<span>Select Both (User and Month)</span>'
            }
            return JsonResponse(response_data)
        
        # Get the employee based on the selected_option
        try:
            employee = Employee.objects.get(id=selected_option)
        except Employee.DoesNotExist:
            response_data = {
                'service_incentive': f'<span>₹0</span>',
                'product_incentive': f'<span>₹0</span>'
            }
            return JsonResponse(response_data)
        
        # Get the salary of the employee for the selected month
        try:
            salary = Salary.objects.get(employee=employee, paid=False, month=month)
        except Salary.DoesNotExist:
            response_data = {
                'service_incentive': f'<span>₹0</span>',
                'product_incentive': f'<span>₹0</span>'
            }
            return JsonResponse(response_data)
        
        # Build the response_data object with the service_incentive and product_incentive
        service_incentive = salary.service_incentive_amount
        product_incentive = salary.product_incentive_amount
        response_data = {
            'service_incentive': f'<span>₹{service_incentive}</span><br><a href="/service-incentive-split/{selected_option}/{month}" target="__blank">Click Here</a>',
            'product_incentive': f'<span>₹{product_incentive}</span>'
        }
        return JsonResponse(response_data)

def ShowBaseSalary(request):
    if request.method == 'POST':
        # Validate the selected_option
        selected_option = request.POST.get('selected_option')
        if not selected_option:
            response_data = {
                'result': 0,
            }
            return JsonResponse(response_data)
        
        # Get the salary of the employee based on the selected_option
        try:
            employee = Employee.objects.get(id=selected_option)
        except Employee.DoesNotExist:
            response_data = {
                'result': 0,
            }
            return JsonResponse(response_data)
        
        # Build the response_data object with the base_salary of the employee
        salary = employee.base_salary
        response_data = {
            'result': f'{salary}',
        }
        return JsonResponse(response_data)

def ServiceIncentiveSplit(request, employee_id, month):
    # Check if the user is authorized to access this page
    if not (group_match('Salon', request) or group_match('Manager', request)):
        return redirect('/')
    
    try:
        # Retrieve the user information
        pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        staff_list = Employee.objects.filter(branch=selected_branch)
    except Exception as e:
        # Handle any exceptions that may occur while retrieving user information
        return    
    if Employee.objects.filter(id=employee_id):
        employee = Employee.objects.get(id=employee_id)
        if not Salary.objects.filter(employee=employee,month=month,paid=False):
            messages.error(request,'Amount is Already Paid! or Salary Details Does Not Exist')
            return redirect(f'/add-salary/?branch={employee.branch.id}')
        else:
            service_incentive = []
            date = []
            service_incentive_amount = []

            total_service_incentive = Salary.objects.get(employee=employee,month=month,paid=False).service_incentive_amount
            month_number = datetime.strptime(month, '%B').month
            total_service = len(Appointment.objects.filter(staff_assigned=employee,isPaid=True,date__month=month_number))
            all_appointment_done = Appointment.objects.filter(staff_assigned=employee,isPaid=True,date__month=month_number)
            for appointment in all_appointment_done:
                service_incentive.append(appointment.service.first())
                date.append(appointment.date)
                service_incentive_amount.append((employee.service_incentive/appointment.staff_assigned.count())/100 * (int(appointment.totalPrice) - (int(appointment.discount_price))))
            context = {
                'total_service_incentive':total_service_incentive,
                'total_service':total_service,
                'pk_id': pk_id,
                'user': user,
                'is_admin': is_admin,
                'selected_branch': selected_branch,
                'employee_list':staff_list,
                'branches':branches,
                'service_incentive':service_incentive,
                'date':date,
                'service_incentive_amount':service_incentive_amount
                }
    return render(request,'vendor/Service-Incentive-Split.html',context)

def DuePayments(request, branch_id, month):
    # Check if the user is authorized to access this page
    if not (group_match('Salon', request) or group_match('Manager', request)):
        return redirect('/')
    
    try:
        # Retrieve the user information
        pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        staff_list = Employee.objects.filter(branch=selected_branch)
    except Exception as e:
        # Handle any exceptions that may occur while retrieving user information
        return
    
    if month == "ALL-TIME":
        branch = Branch.objects.get(id=branch_id)
        all_appointment= list(Appointment.objects.filter(branch=branch))

        list_of_due_invoice = []

        invoices = Invoice.objects.filter(appointment__in=all_appointment).distinct()

        for inv in invoices:
            if inv.due_payment == 0:
                pass
            else:
                list_of_due_invoice.append(inv)

        total_due_payments = sum(list(invoices.values_list('due_payment',flat=True)))


    else:
        return render(request,'error.html')
    
    # due_payment_service_name = list(Appointment.objects.filter(branch=branch_id, isPaid=False).values_list('service', flat=True))


    # total_due_payments = [{'name':Service.objects.get(id=k), 'date':i.createdAt, 'amount':int(i.totalPrice)} for i, k in zip(total_due_payments, due_payment_service_name)]

    context = {
        'total_due_payments':total_due_payments,
        'pk_id': pk_id,
        'user': user,
        'is_admin': is_admin,
        'selected_branch': selected_branch,
        'employee_list':staff_list,
        'branches':branches,
        'list_of_due_invoice':list_of_due_invoice
        }
    
    
    return render(request,'vendor/due-payments.html', context)



class AddProducts(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/add-products.html'
    queryset = SalonDetails.objects.filter()
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Check user permissions
        if not group_match('Admin', request) and not group_match('Vendor', request) and not group_match('Salon', request) and not group_match('Manager', request):
            return redirect('/')

        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)

        return Response({'key': 'Purchase', 'data': '', 'page': '', 'pages': '',
                'pk_id': pk_id,
                'user': user,
                'is_admin': is_admin,
                'selected_branch': selected_branch,
                'branches':branches
                })

    # Handling POST request
    def post(self, request):
        # try:
        # Getting data from POST request
        product_name = request.POST.get('product_name')
        product_price = request.POST.get('product_price')
        product_descrition = request.POST.get('product_description')
        product_sku = request.POST.get('product_sku')
        product_availablity = request.POST.get('product_availablity')
        product_weight = request.POST.get('product_weight')
        product_weight_unit = request.POST.get('product_weight_unit')
        product_price_currency = request.POST.get('product_price_currenry')
        product_vendor = request.POST.get('product_vendor')
        product_category = request.POST.get('product_category')
        product_collection = request.POST.get('product_collection')
        product_tag = request.POST.get('product_tag')
        product_image = request.FILES.get('product_image')
        product_quantity = request.POST.get('product_quantity')
        user = User.objects.get(id=request.user.id)
        salon_associate = SalonDetails.objects.get(user=user)

        # Converting product availability to boolean
        product_availablity = True if product_availablity == "on" else False

        # Creating Product object with data from POST request
        product_save = Product(
            salon=salon_associate,
            name=product_name,
            price=product_price,
            vendor=product_vendor,
            sku=product_sku,
            description=product_descrition,
            weight=product_weight,
            weight_unit=product_weight_unit,
            currency=product_price_currency,
            category=product_category,
            collection=product_collection,
            tag=product_tag,
            image=product_image,
            availablity=product_availablity,
            quantity = product_quantity
        )
        # Saving the Product object
        product_save.full_clean()
        product_save.save()

        # Returning successful response and redirecting to the same page
        messages.success(request, 'Successfully Product Added')
        return redirect(request.path)
        # except Exception as e:
        #     # Handling exceptions and returning error response
        #     messages.error(request, 'Error occurred while adding product: {}'.format(str(e)))
        #     return JsonResponse({'status': 'error', 'message': 'Error occurred while adding product: {}'.format(str(e))})


class SaleProducts(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/sale-products.html'
    queryset = SalonDetails.objects.filter()
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Check user permissions
        if not group_match('Admin', request) and not group_match('Vendor', request) and not group_match('Salon', request) and not group_match('Manager', request):
            return redirect('/')

        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)

        return Response({'key': 'Sale', 'data': '', 'page': '', 'pages': '',
                'pk_id': pk_id,
                'user': user,
                'is_admin': is_admin,
                'selected_branch': selected_branch,
                'branches':branches
                })

    # Handling POST request
    def post(self, request):
        # try:
        # Getting data from POST request
        product_name = request.POST.get('product_name')
        product_price = request.POST.get('product_price')
        product_descrition = request.POST.get('product_description')
        product_sku = request.POST.get('product_sku')
        product_availablity = request.POST.get('product_availablity')
        product_weight = request.POST.get('product_weight')
        product_weight_unit = request.POST.get('product_weight_unit')
        product_price_currency = request.POST.get('product_price_currenry')
        product_vendor = request.POST.get('product_vendor')
        product_category = request.POST.get('product_category')
        product_collection = request.POST.get('product_collection')
        product_tag = request.POST.get('product_tag')
        product_image = request.FILES.get('product_image')
        product_quantity = request.POST.get('product_quantity')
        user = User.objects.get(id=request.user.id)
        salon_associate = SalonDetails.objects.get(user=user)

        # Converting product availability to boolean
        product_availablity = True if product_availablity == "on" else False

        # Creating Product object with data from POST request
        product_save = Product(
            salon=salon_associate,
            name=product_name,
            price=product_price,
            vendor=product_vendor,
            sku=product_sku,
            description=product_descrition,
            weight=product_weight,
            weight_unit=product_weight_unit,
            currency=product_price_currency,
            category=product_category,
            collection=product_collection,
            tag=product_tag,
            image=product_image,
            availablity=product_availablity,
            quantity = product_quantity
        )
        # Saving the Product object
        product_save.full_clean()
        product_save.save()

        # Returning successful response and redirecting to the same page
        messages.success(request, 'Successfully Product Added')
        return redirect(request.path)
        # except Exception as e:
        #     # Handling exceptions and returning error response
        #     messages.error(request, 'Error occurred while adding product: {}'.format(str(e)))
        #     return JsonResponse({'status': 'error', 'message': 'Error occurred while adding product: {}'.format(str(e))})



class Products(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/products.html'
    queryset = SalonDetails.objects.filter()
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Check user permissions
            if not group_match('Admin', request) and not group_match('Vendor', request) and not group_match('Salon', request) and not group_match('Manager', request):
                return redirect('/')

            try:
                pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
            except Exception as e:
                # Handle any exceptions that may occur while retrieving user information
                return Response({'message': 'An error occurred while retrieving user information.'}, status=500)

            
            # Get the salon details associated with the user
            salon_associate = SalonDetails.objects.get(user=user)
            
            # Get a list of products associated with the salon
            product = list(Product.objects.filter(salon=salon_associate))
            product.reverse()

            vendor_set = [i.vendor for i in product]
            vendor_set = list(set(vendor_set))
            
            # Call the my_view function to get additional data
            data = my_view(request, product)
            
            # Create a context dictionary with the necessary data
            context = {
                'product': product,
                'pk_id': pk_id,
                'user': user,
                'is_admin': is_admin,
                'selected_branch': selected_branch,
                'vendor_set':vendor_set,
                'branches':branches
            }
            
            # Add any additional data obtained from the my_view function to the context dictionary
            context = {**context, **data}
            
            # Return a response with the context data
            return Response(context)
        
        # Catch any exceptions and return an appropriate response
        except SalonDetails.DoesNotExist:
            return Response({'error': 'SalonDetails not found for user'}, status=status.HTTP_404_NOT_FOUND)
        except Product.DoesNotExist:
            return Response({'error': 'No products found for salon'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        return Response({'message': ''})




class ProductDetail(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/product-detail.html'
    queryset = SalonDetails.objects.filter()
    permission_classes = [IsAuthenticated]

    def get(self, request,product_name,product_id):
        if not group_match('Salon', request):
            return redirect('/')
        user = User.objects.get(id=request.user.id)
        salon = SalonDetails.objects.get(user=user)
        if Product.objects.filter(salon=salon,name=product_name,id=product_id):
            product = Product.objects.filter(salon=salon,name=product_name,id=product_id)
        else:
            return render(request,'error.html')
        context = {'product':product}
        return Response(context)
    
    def post(self,request):
        pass



class Support(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/support.html'
    queryset = SalonDetails.objects.filter()
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'key': 'Support', 'data': '', 'page': '', 'pages': ''})

    def post(self, request):
        return Response({'message': ''})

class Tutorial(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/tutorial.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.filter()

    def get(self, request):
        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)
        return Response({'key': 'Tutorial', 'data': '', 'page': '', 'pages': '',
                        'pk_id': pk_id,
                        'user': user,
                        'is_admin': is_admin,
                        'selected_branch': selected_branch,
                        'branches':branches})

    def post(self, request):
        return Response({'message': ''})

class Support(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/support.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.filter()

    def get(self, request):
        return Response({'key': 'Support', 'data': '', 'page': '', 'pages': ''})

    def post(self, request):
        return Response({'message': ''})


class BillingView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/billing.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.filter()

    def get(self, request):
        invoices = Invoice.objects.filter().order_by('invoice__date_created')
        return Response({'key': 'Billing', 'invoices': invoices, 'page': '', 'pages': ''})

    def post(self, request):
        return Response({'message': ''})

class InvoiceView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/invoice.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.filter()

    def get(self, request):
        invoices = Invoice.objects.filter().order_by('invoice__date_created')
        return Response({'key': 'Invoice', 'invoices': invoices, 'page': '', 'pages': ''})

    def post(self, request):
        return Response({'message': ''})
from django.db.models import Count 
from decimal import Decimal

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
    


class SalonBranches(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/show_branch.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.filter()

    def get(self, request):
        if group_match('Salon',request) == False and group_match('Manager') == False:
            return redirect('/')

        try:
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)

        services = list(Service.objects.all().values_list('name', flat=True))
        services = set(services)
        try:
            salon = SalonDetails.objects.get(user=user)
        except Exception:
            salon = None
        all_salon_services = []
        if salon:
            salon = SalonDetails.objects.get(user=user)
            show = True
            message = ""
            branches = Branch.objects.filter(salon=salon)
            rating = []
            for s in branches:
                serv = Service.objects.filter(branch=s)
                all_salon_services.append(list(serv)[0:3])
                ratings = list(Review.objects.filter(branch=s).values_list('rating', flat=True))
                if len(ratings) == 0:
                    rating.append(0)
                else:
                    rating.append(round(abs(sum(ratings) / len(ratings)), 2))
            average_rating = rating
        elif not branches and salon:
            show = False
            message = """
                        <center><h2>You have Not Register Your Branches Yet!</h2><br><a href='/add_branch/'>
                        <button class='btn btn-success'>Register Your Branch</button></a></center>
                    """
            average_rating = None
        elif not salon:
            show = False
            message = """
                        <center><h2>You have Not Register Your Salon Yet!</h2><br><a href='/add_salon/'>
                        <button class='btn btn-success'>Register Your Salon</button></a></center>
                    """
            average_rating = None
        else:
            pass
        context = {'branch':branches,'show':show,'message':message,'services':all_salon_services,'all_service':services,'average_rating':average_rating,
                    'pk_id': pk_id,
                    'user': user,
                    'is_admin': is_admin,
                    'branches': branches,
                    'selected_branch': selected_branch}
        return Response(context)

    def post(self, request):
        return Response({'message': ''})

class Data(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/settings.html'
    queryset = SalonDetails.objects.filter()
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'key': 'Customers', 'data': '', 'page': '', 'pages': ''})

    def post(self, request):
        return Response({'message': ''})

def createInvoice(request):
    # import ipdb;ipdb.set_trace()
    if request.method == "POST":
        transaction = request.POST.get('transaction','2123')
        customer = request.POST.get('customer', 'Swapnil Wankhede')
        total = request.POST.get('total',123)
        # invoice=request.POST.get('invoice','')
        # product = request.POST.get('product','')
        tax = request.POST.get('tax',12)
        rate = request.POST.get('rate',12)
        quantity=request.POST.get('quantity',11)
        price = request.POST.get('price',11)
        if True:
            product = Product.objects.get(id=1)
            stock = ProductItem.objects.get(id=1)
            
            invoice = Invoice(transaction = transaction,
                            customer = customer,
                            total = total).save()
            inv = Invoice.objects.get(id=1)
            invoiceitem = ProductInvoiceItem(invoice = inv,
                            product = product,
                            stock = stock,
                            price = price,
                            quantity = quantity,
                            status = True,
                            rate = rate,
                            tax = tax,
                        ).save()
            messages.success(request,"Welcome, You Have Created a Invoice")
            return redirect('/billings')
        else:
            messages.error(request,'Please verify Yourself')
            return redirect('/signup')

def updatestaff(request, order_id):
    if request.method == "POST":
        user = request.POST.get('selected_option')
        u = User.objects.get(id=user)
        staff_assigned = Employee.objects.get(user=u)
        app = Appointment.objects.get(order_id=order_id)
        app.staff_assigned=staff_assigned
        app.save()
    return True


def UpdateQuantity(request,product_id):
    if request.method == "POST":
        quantity = request.POST.get("quantity")
        product = Product.objects.get(id=product_id)
        product.quantity = int(quantity)
        product.save()
        return True

def updatepayment(request, order_id):
    if request.method == "POST":
        param = request.POST.get('message')
        if param == "Paid Paid Paid":
            appointment = Appointment.objects.get(order_id=order_id)
            appointment.isPaid=True
            appointment.booking_status="Availed"
            appointment.save()
            invoice = Invoice.objects.get(appointment=appointment)
            for appointment in invoice.appointment.all():
                if not appointment.isPaid:
                    pass
                else:
                    invoice.status = True
                    invoice.save()
            send_notification(appointment, invoice)
    return True

def encrypt_transaction(transaction):
    # key is generated
    key = load_key()
    # Create a Fernet object with the key
    f = Fernet(key)
    # Encrypt the transaction parameter
    encrypted_token = f.encrypt(transaction.encode('utf-8'))
    return encrypted_token


from cryptography.fernet import Fernet

from backend.crypto_utils import load_fernet_key

def load_key():
    return load_fernet_key()

def get_bookings(request):
    WEEK_DATE = []
    try:
        # Get user and salon details
        user = User.objects.get(id=request.user.id)
        salon_detail = SalonDetails.objects.get(user=user)
    except ObjectDoesNotExist:
        # User or salon details not found
        raise NotFound()

    for x in range(0, 15):
        base = date.today()
        WEEK_DATE.append(base + timedelta(days=x))

    if group_match('Salon', request) and group_match('Manager', request):
        try:
            # Get all branches managed by the user
            branches = list(Branch.objects.filter(manager=user))
            # Get all services offered by those branches
            SERVICE_OFFERED = list(Service.objects.filter(branch__in=branches))
            # Count of all branches
            branch_count = len(branches)
        except ObjectDoesNotExist:
            # Branches or services not found
            raise NotFound()
    elif group_match('Salon', request):
        # Get all branches of the salon
        branches = Branch.objects.filter(salon=salon_detail)
        # Get all services offered by those branches
        SERVICE_OFFERED = list(Service.objects.filter(branch__in=branches))
        # Count of all branches
        branch_count = len(branches)
    else:
        # Get all branches managed by the user
        branches = Branch.objects.filter(manager=user)
        # Get all services offered by those branches
        SERVICE_OFFERED = list(Service.objects.filter(branch__in=branches))
        # Count of all branches
        branch_count = len(branches)

    CUSTOMER = list(User.objects.filter(groups__name__in=['Customer']).values_list('id',flat=True))
    # Return response with required details
    return {
        'branch_count':branch_count,
        'branches':branches,
        'week_date':WEEK_DATE,
        'time_range': TIME_RANGE,
        'service': SERVICE_OFFERED,
        'page': '',
        'pages': '',
        'customer':CUSTOMER,
    }






@login_required
def after_cancel(request,appoint):
    from datetime import datetime
    import calendar
    now = datetime.now()
    month = str(calendar.month_name[now.month]).upper()

    invoice = Invoice.objects.get(appointment=appoint)
    if appoint.isPaid:
        ############ (Start) Updating Service Incentive of Staff and Deleting All Appointment Associated To Invoice #################
        for appoint in invoice.appointment.all():
            staff_count = appoint.staff_assigned.count()
            for staff in appoint.staff_assigned.all():
                stf = Employee.objects.get(id=staff.id)
                service_incentive_amount = ((stf.service_incentive/staff_count)/100 * (int(appoint.totalPrice) - int(appoint.discount_price)))
                if Salary.objects.filter(employee=stf,month=month):
                    salary = Salary.objects.get(employee=stf,month=month)
                    salary.total_salary = salary.total_salary - service_incentive_amount
                    salary.service_incentive_amount = salary.service_incentive_amount - service_incentive_amount
                    salary.save()
                else:
                    return redirect(f'/bookings/?branch={appoint.branch.id}')
            appoint.delete()
        invoice.delete()
        messages.success(request, 'Successfully Deleted All Appointment Which You have Booked')
        return redirect(f'/bookings/?branch={appoint.branch.id}')
        ################## (End) Updating Appointment Table #########################
    else:
        invoice.appointment.remove(appoint)
        invoice.total = float(invoice.total) - float(appoint.totalPrice)
        invoice.save()
        ############ (Start) Updating Service Incentive of Staff and Deleting All Appointment Associated To Invoice #################
        for staff in appoint.staff_assigned.all():
            stf = Employee.objects.get(id=staff.id)
            service_incentive_amount = ((stf.service_incentive/staff_count)/100 * (int(appoint.totalPrice) - int(appoint.discount_price)))
            if Salary.objects.filter(employee=stf,month=month):
                salary = Salary.objects.get(employee=stf,month=month)
                salary.total_salary = salary.total_salary - service_incentive_amount
                salary.service_incentive_amount = salary.service_incentive_amount - service_incentive_amount
                salary.save()
            else:
                return redirect(f'/bookings/?branch={appoint.branch.id}')
        appoint.delete()

        if len(invoice.appointment.all()) >= 1:
            appoint.delete()
        else:
            invoice.delete()
        ################## (End) Updating Service Incentive of Staff and Deleting All Appointment Associated To Invoice #########################



@login_required
def CancelAppointment(request,user_id,user_name,order_id):
    if Appointment.objects.filter(order_id=order_id):
        customer = User.objects.get(id=user_id,username=user_name)
        appointment = Appointment.objects.get(order_id=order_id,user=customer)
        branch_id = appointment.branch.id
        user = User.objects.get(id=request.user.id)
        if SalonDetails.objects.filter(user=user):
            salon = SalonDetails.objects.get(user=user)
            if appointment.salon != salon:
                messages.error(request,'Some Problem Occured')
                return redirect(f'/bookings/?branch={branch_id}')
            else:
                after_cancel(request,appointment)
                messages.error(request,'Some Problem Occured')
                return redirect(f'/bookings/?branch={branch_id}')
        else:
            if Branch.objects.filter(manager=user):
                branch = Branch.objects.get(manager=user)
                if appointment.branch != branch:
                    messages.error(request,'Some Problem Occured')
                    return redirect(f'/bookings/?branch={branch_id}')
                else:
                    after_cancel(request,appointment)
                    messages.error(request,'Some Problem Occured')
                    return redirect(f'/bookings/?branch={branch_id}')
            else:
                messages.error(request,'Some Problem Occured')
                return redirect(f'/bookings/?branch={branch_id}')
    else:
        messages.error(request,'Some Problem Occured')
        return redirect(f'/bookings/?branch={branch_id}')




class Membership(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/membership.html'
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
        return Response({'selected_branch':selected_branch,'branches':branches,'pk_id': pk_id,'user': user,'is_admin': is_admin})

    def post(self, request):
        return Response({'message': ''})

class AddMembership(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/add-membership.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.filter()


    def get(self, request):
        if group_match('Salon',request) == False:
            return redirect('/')
        return Response({'key': 'Add Customers', 'data': '', 'page': '', 'pages': ''})

    def post(self, request):
        if group_match('Salon',request) == False:
            return redirect('/')
        return Response({'message': ''})

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
        
import csv

@login_required
def ExportData(request):
    try:
        pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
    except Exception as e:
        # Handle any exceptions that may occur while retrieving user information
        return Response({'message': 'An error occurred while retrieving user information.'}, status=500)
    
    if request.method == "POST":
        if request.POST.get('message') == 'EXPORT-DATA':
            customer = list(Customer.objects.filter(branch=selected_branch, status='Active').values_list('user', flat=True))
            
            # Initialize lists to hold the data for each customer
            unique_customer = []
            all_customer = []
            
            # Loop through each customer and get their data
            for c in customer:
                #Get User
                customer_user = c

                # Get the customer's user object and add it to the list of unique customers
                unique_customer.append(Customer.objects.get(user=customer_user))
                all_customer.append(Customer.objects.get(user=customer_user))

            # Retrieve the data you want to export as CSV
            data = all_customer

            # Create the HttpResponse object with CSV header
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="data.csv"'

            # Create a CSV writer
            writer = csv.writer(response)

            # Write headers (optional)
            writer.writerow(['Name', 'Email', 'Mobile'])  # Replace with your field names

            # Write data rows
            for item in data:
                writer.writerow([item.username, item.email, item.mobile])  # Replace with your field names

            return response
        else:
            return redirect(f'/customers/?branch={selected_branch.id}')
    else:
        return redirect(f'/customers/?branch={selected_branch.id}')
    

############################ Invoice-Generator(Booking) #########################################
class Changelogs(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'vendor/changelog.html'
    permission_classes = [IsAuthenticated]
    queryset = SalonDetails.objects.filter()
    
    def get(self, request):
        # Ensure user has necessary permissions
        if not group_match('Admin', request) and not group_match('Salon', request) and not group_match('Manager', request):
            return redirect('/')

        try:
            # Get user, salon, and branch details
            pk_id, user, is_admin, salon, selected_branch, branches = get_user_salon_branch_details(request)
        except Exception as e:
            # Handle any exceptions that may occur while retrieving user information
            return Response({'message': 'An error occurred while retrieving user information.'}, status=500)

        # add a check to verify if user is Salon owner or not

        changelogs = list(ChangeLog.objects.all())
        users = list(set([i.user for i in changelogs]))
        
        changelogs = []
        for k in users:
            logs = list(ChangeLog.objects.filter(user=k))
            changelogs.append({'user':k, 'logs':logs})


        # Return response with necessary data
        return Response({'action':True, 'entries':changelogs})
