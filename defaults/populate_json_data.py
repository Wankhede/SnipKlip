import json
from backend.models import AccessKeyRemove, SubscriptionAccessKeyAssociation, SubscriptionType,Group,AllowedPath
from rest_framework.decorators import api_view
from rest_framework.response import Response
import pandas as pd

def load_JSON_data():
    load_Subscription_Types()
    load_Access_Control_Keys()
    load_Allowed_Path()
    return Response({
        'message':"Successully Loaded All Essentials",
        'status':200
    })

def load_Subscription_Types():
    try:
        # Read the access keys JSON file
        with open('defaults/data/subscription_types.json', 'r') as f:
            subscription_type_data = json.load(f)

        # Get a set of existing access keys from the database
        existing_subscription_types = list(set(SubscriptionType.objects.values_list('subscription_type', flat=True)))

        # Iterate over the JSON data and add new keys to the database
        for subscription_type in subscription_type_data:

            # Check if the subscription_type is not in the set of existing keys to avoid duplicates
            if subscription_type and subscription_type not in existing_subscription_types:
                subscriptionType = SubscriptionType(
                                    subscription_type=subscription_type,
                                    price=100
                                    )
                subscriptionType.save()

        return Response({
            "data": {},
            "message": '',
            "status": '',
        })
    except Exception as e:
        return Response({
            "data": {},
            "message": '',
            "status": '',
        })


def load_Allowed_Path():
    try:
        # Add Allowed Path Data From Json File
        with open('defaults/data/allowed_path.json', 'r') as f:
            allowed_path_data = json.load(f)

        allowed_path = list(set(AllowedPath.objects.all().values_list('path_name',flat=True)))
        
        for path_name in allowed_path_data:
            if path_name and path_name not in allowed_path:
                path = AllowedPath(
                    path_name = path_name
                )
                path.save()

        return Response({
            "data": {},
            "message": '',
            "status": '',
        })   
    except Exception as e:
        return Response({
            "data": {},
            "message": '',
            "status": '',
        })
        

def load_Access_Control_Keys():
    try:
        # Read the access keys JSON file
        with open('defaults/data/access_control_keys.json', 'r') as f:
            access_keys_data = json.load(f)

        # Get a set of existing access keys from the database
        existing_access_keys = list(SubscriptionAccessKeyAssociation.objects.all().values_list('key_name',flat=True))

        for key in access_keys_data:
            key_name = key.get("access_key", "")
            tag = key.get("tag", "")
            section_name = key.get("section_name", "")
            description = key.get("description", "")
            subscription_name = key.get('subscription', '')
            group_name = key.get('group','')

            if key_name and key_name not in existing_access_keys:
                accesskey = SubscriptionAccessKeyAssociation(
                    key_name=key_name,
                    tag=tag,
                    section_name=section_name,
                    description=description
                    )
                accesskey.save()

                for subscription in subscription_name:
                    subscription = SubscriptionType.objects.get(subscription_type=subscription)
                    accesskey.subscription.add(subscription)
                    accesskey.save()

                for group in group_name:
                    group = Group.objects.get(name=group)
                    accesskey.group.add(group)
                    accesskey.save()

        return Response({
            "message": 'Successully Loaded Data',
            "status": 200,
        })  
    except Exception as e:
        return Response({
            "data": {},
            "message": '',
            "status": '',
        })  
