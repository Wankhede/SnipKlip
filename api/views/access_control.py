from backend.models import *
from api.serializers import *
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.db.models import *
from api.constants import *
import json

@api_view(['GET'])
def get_data_grouped_by_tag(request):
    # Filter AccessKeyAssociation objects by salon_id
    salon_id = request.GET['salon_id']
    subscription_name = request.GET['subscription_name']
    branch_id = request.GET['branch_id']
    group = request.GET['group']

    if subscription_name == "NULL":
        keys = {
            "WEB_HEADER":[]
        }
    
    elif group == "Admin":
        # Read the access keys JSON file
        with open('defaults/data/access_control_keys.json', 'r') as f:
            access_keys_data = json.load(f)
        keys = {
            "WEB_HEADER":[]
        }
        for key in access_keys_data:
            key_name = key.get("access_key", "")
            keys['WEB_HEADER'].append(key_name)
    else:
        keys = {
            "WEB_HEADER":[]
        }
        try:
            subscription_buy = SubscriptionType.objects.get(subscription_type=subscription_name)
            branch = Branch.objects.get(id=branch_id)
            salon = SalonDetails.objects.get(id=salon_id)
            current_datetime = timezone.now()
            group = Group.objects.get(name=group)
            access_key = SubscriptionAccessKeyAssociation.objects.filter(group=group)

            if Subscription.objects.filter(name_of_subscription=subscription_buy.subscription_type,salon=salon,paid=True,end_date__gt=current_datetime):
                for key in access_key:  
                    if subscription_buy in key.subscription.all(): 
                        keys['WEB_HEADER'].append(key.key_name) 

        except Exception:
            return Response({
                'message':'Invalid Data',
                'status':400
            }) 

    
    return Response({
        'data':keys,
        'status':200
    })
