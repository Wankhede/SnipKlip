from api.common import get_all_table_records
from api.decorators import jwt_authentication_required
from api.throttles import SustainedRateThrottle
from rest_framework.throttling import UserRateThrottle
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from backend.models import Subscription, Branch, User, SalonDetails,SubscriptionType,SubscriptionAccessKeyAssociation
import datetime
from django.db.models import Q
from dateutil.relativedelta import relativedelta
import razorpay
from rest_framework import status
from app.settings.base import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET
from api.constants import *
from api.serializers import SubscriptionSerializer
import requests


@api_view(['GET'])
def getSubscriptionType(request):
    subscription = SubscriptionType.objects.filter(status=True)
    subscription_list = []
    permission = []
    for subs in subscription:
        if subs.subscription_type == 'STANDARD':
            permission = [0, 1]
        elif subs.subscription_type == 'STANDARD PLUS':
            permission = [0, 1, 2, 3]
        elif subs.subscription_type == 'PREMIUM':
            permission =  [0, 1, 2, 3, 4, 5]
        subs_dict = {
                    "title": subs.subscription_type,
                    "description":subs.description,
                    "price": subs.price,
                    "permission":permission,
                    "active": True
                }
        subscription_list.append(subs_dict)
    return Response({
        'data':subscription_list,
        'message':'Successfully Retrived All Subscription',
        'status':200
    })



@api_view(['POST'])
def create_payment(request):
    amount = int(request.data.get('amount'))
    subscription_type = request.data.get('subscriptionType')
    user_id = request.data.get('user_id')
    branch_id = request.data.get('branch_id')
    salon_id = request.data.get('salon_id')
    name_of_subscription = request.data.get('subscriptionName')
    current_date_time = datetime.datetime.now()
    start_date = current_date_time.strftime('%Y-%m-%d %H:%M:%S')
    try:
        user = User.objects.get(id=user_id)
        salon = SalonDetails.objects.get(id=salon_id)
    except Exception:
        return Response({'message': APIMessages.USER_OR_BRANCH_NOT_EXISTS.value,'status':BAD_REQUEST_STATUS})
    
    if amount is None:
        return Response({'message': APIMessages.AMOUNT_NOT_PROVIDED.value,'status':BAD_REQUEST_STATUS})
    
    check_subscription = Subscription.objects.filter(user=user,paid=True)
    check_subscription_time = check_subscription.filter(Q(start_date__lte=start_date) & Q(end_date__gte=start_date))

    if check_subscription and check_subscription.filter(name_of_subscription=name_of_subscription).exists():
        return Response({'message': APIMessages.ALREADY_PURCHASED.value,'status':BAD_REQUEST_STATUS})
    
    if check_subscription and check_subscription.first().credit_balance >= int(amount):
        return Response({'message': APIMessages.UPGRADE_PURCHASED.value,'status':BAD_REQUEST_STATUS})
    
    if check_subscription:
        amount = amount - check_subscription.first().credit_balance
    else:
        amount = amount
    if subscription_type == "yearly":
        one_year_later_date = current_date_time + relativedelta(months=12) 
        end_date = one_year_later_date.strftime('%Y-%m-%d %H:%M:%S')
    else:
        one_month_later_date = current_date_time + relativedelta(months=1) 
        end_date = one_month_later_date.strftime('%Y-%m-%d %H:%M:%S')

    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


    # Create a Razorpay order
    response = client.order.create(data={
        'amount': amount * 100,
        'currency': 'INR',
    })

    # Save the order_id in your database
    order_id = response['id']

    # Delete the previous subscription
    check_subscription.delete()

    # Create the Subscription object
    subscription = Subscription(
        name_of_subscription = name_of_subscription.upper(),
        salon = salon,
        user=user,
        start_date = start_date,
        end_date = end_date,
        credit_balance = amount,
        type = subscription_type.upper(),
        paid = False,
        order_id = order_id
    )
    subscription.save()


    payment_gateway_response = {
        'order_id': order_id,
        'amount': amount * 100,
        'currency': 'INR', 
        'key': RAZORPAY_KEY_ID,
        'status': SUCCESS_STATUS_CODE,
        'message': APIMessages.PAYMENT_STARTED.value,
    }

    return Response(payment_gateway_response, status=SUCCESS_STATUS_CODE)

@api_view(['POST'])
def payment_callback(request):
    # Accessing Data
    data=request.data
    branch_id = data['branch_id']
    salon_id = data['salon_id']
    user_id = data['user_id']
    try:
        user = User.objects.get(id=user_id)
        salon = SalonDetails.objects.get(id=salon_id)
        branch = Branch.objects.get(salon=salon,id=branch_id)
    except:
        response_data = {
                'message': APIMessages.PAYMENT_FAILURE.value,
                'status':FAILED_STATUS_CODE
                }
        
    # Process the payment callback data here
    razorpay_order_id = data['razorpay_order_id']
    
    try:
        url = f'https://api.razorpay.com/v1/orders/{razorpay_order_id}/payments'
        headers = {
            'Content-Type': 'application/json',
        }

        # You should use your Razorpay key and secret here
        auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)

        response = requests.get(url, headers=headers, auth=auth)

        if response.status_code == 200:
            payments = response.json()['items']
            for payment in payments:
                if payment['order_id'] == razorpay_order_id and payment['status'] == 'captured':
                    order = Subscription.objects.get(order_id=razorpay_order_id)

                    #Make Paid is equal to FALSE for User/Salon (Those who have already Purchased/assigned any Subscription)
                    if Subscription.objects.filter(salon=order.salon,paid=True,user=order.user):
                        previous_order = Subscription.objects.get(salon=order.salon,paid=True,user=order.user)
                        previous_order.paid = False
                        previous_order.save()
                        
                    order.paid = True
                    order.save()

                    # Return a success response with the processed data
                    response_data = {
                        'message': APIMessages.PAYMENT_DONE.value,
                        'razorpay_order_id': razorpay_order_id,
                        'status':SUCCESS_STATUS_CODE,
                        'subscription_name':order.name_of_subscription
                    }
                    return Response(response_data)
                else:
                    response_data = {
                        'message': APIMessages.PAYMENT_FAILURE.value,
                        'status':FAILED_STATUS_CODE
                        }
        else:
            response_data = {
                'message': APIMessages.PAYMENT_FAILURE.value,
                'status':FAILED_STATUS_CODE
                }
    
    # Return Payment Failed
    except Exception:
        response_data = {
        'message': APIMessages.PAYMENT_FAILURE.value,
        'status':FAILED_STATUS_CODE
        }

@api_view(['GET'])
@throttle_classes([SustainedRateThrottle])
@jwt_authentication_required
def getSubscriptions(request):
    salon_id = request.GET['salon_id']
    branch_id = request.GET['branch_id']
    try:
        if branch_id == "-1" and salon_id == "-1":
            subscription = get_all_table_records(request, Subscription)
        else:
            try:
                salon = SalonDetails.objects.get(id=salon_id)
            except Exception as e:
                return Response({'message': APIMessages.USER_OR_BRANCH_NOT_EXISTS.value,'status':BAD_REQUEST_STATUS})
            subscription = Subscription.objects.filter(salon=salon)
        total_rows = subscription.count()
        serializer = SubscriptionSerializer(subscription, many=True)

        return Response({
            "data": {
                "count": total_rows,
                "rows": serializer.data
            },
            "message": APIMessages.ALL_SUBSCRIPTION_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        })
    except Exception as e:
        return Response({
            "message": APIMessages.SUBSCRIPTION_NOT_RETRIEVED.value,
            "status": FAILED_STATUS_CODE,
        })
    