from backend.models import *
from api.serializers import *
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.db.models import *
from api.constants import *
from django.utils import timezone
import json


def _keys_from_json_for_group(group_name: str, subscription_name: str | None = None):
    """Fallback from defaults JSON when DB associations are incomplete."""
    keys = {"WEB_HEADER": []}
    try:
        with open('defaults/data/access_control_keys.json', 'r') as f:
            access_keys_data = json.load(f)
    except Exception:
        return keys

    for key in access_keys_data:
        key_name = key.get("access_key", "")
        groups = key.get("group", []) or []
        subscriptions = key.get("subscription", []) or []
        if group_name not in groups:
            continue
        if subscription_name and subscription_name not in ("NULL", "None", "") and subscription_name not in subscriptions:
            # Allow PREMIUM-like casing mismatches
            if subscription_name.upper() not in [s.upper() for s in subscriptions]:
                continue
        if key_name:
            keys["WEB_HEADER"].append(key_name)
    return keys


@api_view(['GET'])
def get_data_grouped_by_tag(request):
    salon_id = request.GET.get('salon_id')
    subscription_name = request.GET.get('subscription_name') or "NULL"
    branch_id = request.GET.get('branch_id')
    group = request.GET.get('group') or ""

    if group == "Admin":
        keys = _keys_from_json_for_group("Admin")
        return Response({'data': keys, 'status': 200})

    if not group:
        return Response({'data': {"WEB_HEADER": []}, 'status': 200})

    keys = {"WEB_HEADER": []}

    try:
        group_obj = Group.objects.get(name=group)
        access_key_qs = SubscriptionAccessKeyAssociation.objects.filter(group=group_obj)

        # Prefer DB associations when populated
        if access_key_qs.exists():
            if subscription_name in ("NULL", "None", "", None):
                # During onboarding/trial, still expose group defaults for the plan-agnostic keys
                keys = _keys_from_json_for_group(group, None)
            else:
                try:
                    subscription_buy = SubscriptionType.objects.get(subscription_type=subscription_name)
                except SubscriptionType.DoesNotExist:
                    # Case-insensitive fallback
                    subscription_buy = SubscriptionType.objects.filter(
                        subscription_type__iexact=subscription_name
                    ).first()

                if subscription_buy is None:
                    keys = _keys_from_json_for_group(group, subscription_name)
                else:
                    salon = SalonDetails.objects.filter(id=salon_id).first() if salon_id else None
                    current_datetime = timezone.now()
                    has_active = False
                    if salon is not None:
                        has_active = Subscription.objects.filter(
                            name_of_subscription=subscription_buy.subscription_type,
                            salon=salon,
                            paid=True,
                            end_date__gt=current_datetime,
                        ).exists()
                        # Also accept subscription name case variants stored on Subscription rows
                        if not has_active:
                            has_active = Subscription.objects.filter(
                                name_of_subscription__iexact=subscription_buy.subscription_type,
                                salon=salon,
                                paid=True,
                                end_date__gt=current_datetime,
                            ).exists()

                    if has_active or salon is None:
                        for key in access_key_qs:
                            if subscription_buy in key.subscription.all():
                                keys['WEB_HEADER'].append(key.key_name)

                    if not keys['WEB_HEADER']:
                        keys = _keys_from_json_for_group(group, subscription_buy.subscription_type if subscription_buy else subscription_name)
        else:
            keys = _keys_from_json_for_group(group, None if subscription_name in ("NULL", "None", "") else subscription_name)

    except Exception as exc:
        keys = _keys_from_json_for_group(group, None if subscription_name in ("NULL", "None", "") else subscription_name)
        if not keys['WEB_HEADER']:
            return Response({
                'message': f'Invalid Data: {exc}',
                'status': 400
            })

    return Response({
        'data': keys,
        'status': 200
    })
