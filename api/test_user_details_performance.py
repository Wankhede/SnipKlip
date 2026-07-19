from datetime import timedelta

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from api.views.user_profile import get_user_detail
from backend.models import Branch, Group, SalonDetails, Subscription, User


class UserDetailsPerformanceTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="owner@example.com",
            email="owner@example.com",
            password="test-password",
            name="Owner",
        )
        salon_group, _ = Group.objects.get_or_create(name="Salon")
        self.user.groups.add(salon_group)
        self.salon = SalonDetails.objects.create(
            user=self.user,
            name="Fast Salon",
            email="salon@example.com",
            reg_no="REG-1",
            contact_no="9999999999",
            owner_name="Owner",
            owner_email="owner@example.com",
        )
        self.branch = Branch.objects.create(
            salon=self.salon,
            branch_name="Main",
            owner_contact_no="9999999999",
            address="Address",
            locality="Locality",
            city="City",
            state="State",
            pincode="123456",
        )
        Subscription.objects.create(
            user=self.user,
            salon=self.salon,
            name_of_subscription="PREMIUM",
            paid=True,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30),
        )

    def test_owner_context_is_resolved_once_with_bounded_queries(self):
        request = self.factory.get(
            "/api/v3/user-details/",
            {"user_id": self.user.id},
        )
        force_authenticate(request, user=self.user)

        with CaptureQueriesContext(connection) as queries:
            response = get_user_detail(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["salon_id"], self.salon.id)
        self.assertEqual(response.data["data"]["branch_id"], self.branch.id)
        self.assertEqual(response.data["data"]["subscription_name"], "PREMIUM")
        self.assertLessEqual(
            len(queries),
            6,
            "User context should not repeat salon, branch, or subscription queries.",
        )
