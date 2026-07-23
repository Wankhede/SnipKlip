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

        # Ensure every group referenced by the JSON exists
        for key in access_keys_data:
            for group_name in key.get('group', []) or []:
                Group.objects.get_or_create(name=group_name)

        for key in access_keys_data:
            key_name = key.get("access_key", "")
            if not key_name:
                continue

            tag = key.get("tag", "")
            section_name = key.get("section_name", "")
            description = key.get("description", "")
            subscription_names = key.get('subscription', []) or []
            group_names = key.get('group', []) or []

            accesskey, _created = SubscriptionAccessKeyAssociation.objects.get_or_create(
                key_name=key_name,
                defaults={
                    'tag': tag,
                    'section_name': section_name,
                    'description': description,
                },
            )
            # Keep metadata fresh for already-seeded keys
            accesskey.tag = tag
            accesskey.section_name = section_name
            accesskey.description = description
            accesskey.save()

            desired_subscriptions = []
            for subscription_name in subscription_names:
                subscription, _ = SubscriptionType.objects.get_or_create(
                    subscription_type=subscription_name,
                    defaults={'price': 100},
                )
                desired_subscriptions.append(subscription)
            accesskey.subscription.set(desired_subscriptions)

            desired_groups = [Group.objects.get(name=group_name) for group_name in group_names]
            accesskey.group.set(desired_groups)

        return Response({
            "message": 'Successully Loaded Data',
            "status": 200,
        })
    except Exception as e:
        return Response({
            "data": {},
            "message": str(e),
            "status": 500,
        })

