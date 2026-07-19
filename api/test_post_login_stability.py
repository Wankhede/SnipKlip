from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from api.common import login
from api.serializers import BranchSerializer
from api.views.salon import add_branch_api
from backend.models import Branch, Group, SalonDetails, Subscription, User


class PostLoginStabilityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="owner2@example.com",
            email="owner2@example.com",
            password="test-password",
            name="Owner Two",
        )
        salon_group, _ = Group.objects.get_or_create(name="Salon")
        self.user.groups.add(salon_group)
        self.salon = SalonDetails.objects.create(
            user=self.user,
            name="Stable Salon",
            email="stable@example.com",
            reg_no="REG-2",
            contact_no="8888888888",
            owner_name="Owner Two",
            owner_email="owner2@example.com",
        )
        Branch.objects.create(
            salon=self.salon,
            branch_name="Main",
            owner_contact_no="8888888888",
            address="Address",
            locality="Locality",
            city="City",
            state="State",
            pincode="123456",
            manager=None,
        )
        now = timezone.now()
        Subscription.objects.create(
            user=self.user,
            salon=self.salon,
            name_of_subscription="PREMIUM",
            paid=True,
            start_date=now - timedelta(days=2),
            end_date=now + timedelta(days=5),
        )
        Subscription.objects.create(
            user=self.user,
            salon=self.salon,
            name_of_subscription="STANDARD",
            paid=True,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=10),
        )

    def test_branch_serializer_handles_null_manager(self):
        branch = Branch.objects.filter(salon=self.salon).first()
        payload = BranchSerializer(branch).data
        self.assertIsNone(payload["manager"])
        self.assertIsNone(payload["manager_name"])

    def test_login_survives_multiple_active_subscriptions(self):
        request = self.factory.post(
            "/api/v3/login/",
            {"username": "owner2@example.com", "password": "test-password"},
            format="json",
        )
        response = login(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["status"])
        self.assertEqual(response.data["data"]["salon_id"], self.salon.id)
        self.assertIn(response.data["data"]["subscription_name"], ("PREMIUM", "STANDARD"))

    def test_add_branch_does_not_create_duplicate_trial(self):
        request = self.factory.post(
            "/api/v3/add-branch/",
            {
                "user_id": self.user.id,
                "basicData": {
                    "salonName": "Second",
                    "address": "Addr",
                    "contactNumber": "7777777777",
                    "city": "City",
                    "state": "State",
                    "pinCode": "654321",
                    "locality": "Local",
                    "latitude": 1.1,
                    "longitude": 2.2,
                },
                "salonData": {
                    "salonType": "UNISEX",
                    "NoOfSeat": 4,
                    "NoOfStaff": 2,
                },
            },
            format="json",
        )
        force_authenticate(request, user=self.user)
        before = Subscription.objects.filter(salon=self.salon, paid=True).count()
        response = add_branch_api(request)
        after = Subscription.objects.filter(salon=self.salon, paid=True).count()
        self.assertEqual(response.data.get("status"), 200)
        self.assertEqual(before, after)
