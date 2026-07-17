from django.http import HttpResponseBadRequest
from django.utils import timezone
from rest_framework.response import Response
from backend.models import (User, SalonDetails, Branch, Subscription,AllowedPath,
                            SubscriptionAccessKeyAssociation,SubscriptionType)
from api.constants import APIMessages
import json

PUBLIC_API_PATHS = {
    '/api/v3/login/',
    '/api/v3/signup/',
    '/api/v3/add-salon/',
    '/api/v3/send-email/',
    '/api/v3/assistant/ask/',
}


class AccessControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/v3/'):
            if request.path in PUBLIC_API_PATHS:
                return self.get_response(request)

            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                data = request.GET

            try:
                current_page = data.get('current_page', 'NULL')
            except KeyError:
                current_page = "NULL"

            # Get a list of allowed paths from the database
            allowed_path = list(AllowedPath.objects.all().values_list('path_name', flat=True))

            # Check if the path is allowed or user is an Admin
            if request.path in allowed_path or not data or data.get('group') == "Admin":
                pass
            else:
                # Check for subscription details
                if data.get('subscription_name', '').lower() in {'null', 'NULL'}:
                    return HttpResponseBadRequest("DO-NOT-HAVE-SUBSCRIPTION")
                try:
                    user = User.objects.get(id=data.get('user_id'))
                    salon = SalonDetails.objects.get(id=data.get('salon_id'))
                    branch = Branch.objects.get(id=data.get('branch_id'), salon=salon)
                    user_groups = user.groups.all()
                    user_group = [group.name for group in user_groups]
                except Exception as e:
                    print(e)
                    return HttpResponseBadRequest("DO-NOT-HAVE-SUBSCRIPTION")

                current_datetime = timezone.now()

                # Get a list of controls from the database
                controls = list(set(SubscriptionAccessKeyAssociation.objects.all()))

                control_group = []
                for control in controls:
                    for control_group_name in control.group.all():
                        control_group.append(control_group_name.name)

                    if str(control.key_name) == current_page and any(group in control_group for group in user_group):
                        try:
                            subscription = Subscription.objects.get(
                                paid=True,
                                salon=salon,
                                name_of_subscription=data.get('subscription_name'),
                                end_date__gt=current_datetime
                            )
                            subscription_type = SubscriptionType.objects.get(
                                subscription_type=subscription.name_of_subscription
                            )

                            if subscription_type in control.subscription.all():
                                pass
                            else:
                                return HttpResponseBadRequest("DO-NOT-HAVE-SUBSCRIPTION")
                        except Subscription.DoesNotExist:
                            return HttpResponseBadRequest("DO-NOT-HAVE-SUBSCRIPTION")
                    else:
                        control_group = []

        response = self.get_response(request)
        return response
    

    