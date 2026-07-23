from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from api.services.service_config import ServiceConfigError, parse_service_config, synchronize_services
from backend.models import Branch, SalonDetails, Service, User


class ServiceConfigUploadTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="config-owner", password="test")
        self.salon = SalonDetails.objects.create(
            user=self.owner,
            name="Config Salon",
            email="config@example.com",
            reg_no="CONFIG-1",
            contact_no="9999999999",
            owner_name="Config Owner",
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
        self.client = APIClient()
        token = RefreshToken.for_user(self.owner).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_invalid_json_reports_location_and_writes_nothing(self):
        uploaded = SimpleUploadedFile("services.json", b'[{"service_name": }]', content_type="application/json")

        with self.assertRaisesRegex(ServiceConfigError, r"line 1, column"):
            parse_service_config(uploaded)

        self.assertFalse(Service.objects.exists())

    def test_valid_yaml_creates_and_matches_services(self):
        uploaded = SimpleUploadedFile(
            "services.yml",
            (
                b"- service_name: Haircut\n"
                b"  price: 350\n"
                b"  duration_in_minutes: 45\n"
                b"- service_name: Beard Trim\n"
                b"  price: 150.50\n"
                b"  duration_in_minutes: 20\n"
            ),
            content_type="application/yaml",
        )

        result = synchronize_services(self.branch, parse_service_config(uploaded))
        self.assertEqual(result, {"created": 2, "updated": 0, "total": 2})

        updated = SimpleUploadedFile(
            "services.json",
            b'[{"service_name":"haircut","price":400,"duration_in_minutes":50}]',
            content_type="application/json",
        )
        result = synchronize_services(self.branch, parse_service_config(updated))
        self.assertEqual(result, {"created": 0, "updated": 1, "total": 1})
        self.assertEqual(Service.objects.get(branch=self.branch, name="haircut").price, 400)

    def test_invalid_row_identifies_its_index(self):
        uploaded = SimpleUploadedFile(
            "services.yaml",
            b"- service_name: Haircut\n  price: free\n  duration_in_minutes: 30\n",
            content_type="application/yaml",
        )

        with self.assertRaisesRegex(ServiceConfigError, r"Service 1: price"):
            parse_service_config(uploaded)

    def test_upload_endpoint_returns_clean_error_and_success_payloads(self):
        invalid_response = self.client.post(
            "/api/v3/services/upload-config/",
            {
                "branch_id": self.branch.id,
                "file": SimpleUploadedFile("services.json", b"[invalid"),
            },
            format="multipart",
        )
        self.assertEqual(invalid_response.status_code, 400)
        self.assertIn("line 1, column", invalid_response.data["message"])

        valid_response = self.client.post(
            "/api/v3/services/upload-config/",
            {
                "branch_id": self.branch.id,
                "file": SimpleUploadedFile(
                    "services.json",
                    b'[{"service_name":"Facial","price":500,"duration_in_minutes":60}]',
                ),
            },
            format="multipart",
        )
        self.assertEqual(valid_response.status_code, 200)
        self.assertEqual(valid_response.data["data"]["created"], 1)
        self.assertTrue(Service.objects.filter(branch=self.branch, name="Facial").exists())
