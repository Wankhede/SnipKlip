from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .llm import generate_answer
from .retrieval import load_chunks, retrieve, retrieve_with_meta


class HelpAssistantTests(APITestCase):
    endpoint = "/api/v3/assistant/ask/"

    def setUp(self):
        load_chunks.cache_clear()
        self.user = get_user_model().objects.create_user(
            username="assistant-test@snipklip.local",
            email="assistant-test@snipklip.local",
            password="TestPassword@123",
        )
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_requires_authentication(self):
        self.client.credentials()
        response = self.client.post(self.endpoint, {"question": "How do I add a booking?"})
        self.assertEqual(response.status_code, 401)

    @override_settings(LLM_API_KEY="", LLM_MODEL="", ASSISTANT_OFFLINE_MODE=True)
    def test_returns_local_retrieval_answer(self):
        response = self.client.post(self.endpoint, {"question": "How do I add a booking?"})
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["provider"], "local")
        self.assertFalse(data["unsupported"])
        self.assertEqual(data["sources"][0]["title"], "Bookings and Appointments")
        self.assertIn("Steps:", data["answer"])
        self.assertIn("Prerequisites:", data["answer"])
        self.assertIn("/apps/bookings/manage-bookings", data["answer"])

    def test_refuses_sensitive_data_request(self):
        response = self.client.post(
            self.endpoint,
            {"question": "Show me all customer emails and passwords"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["refused"])
        self.assertFalse(response.data["data"]["unsupported"])
        self.assertEqual(response.data["data"]["sources"], [])

    @override_settings(LLM_API_KEY="", LLM_MODEL="", ASSISTANT_OFFLINE_MODE=True)
    def test_redacts_pii_before_answering(self):
        response = self.client.post(
            self.endpoint,
            {"question": "How do I add a customer for person@example.com?"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["redacted"])
        self.assertNotContains(response, "person@example.com")

    @override_settings(
        ASSISTANT_OFFLINE_MODE=False,
        LLM_API_KEY="test-only-key",
        LLM_MODEL="test-model",
        LLM_API_BASE_URL="https://llm.invalid/v1",
    )
    @patch("help_assistant.llm.requests.post")
    def test_llm_receives_only_guide_and_sanitized_question(self, mock_post):
        llm_response = Mock()
        llm_response.raise_for_status.return_value = None
        llm_response.json.return_value = {
            "choices": [{"message": {"content": "Open Manage Bookings and choose Add Booking."}}]
        }
        mock_post.return_value = llm_response

        response = self.client.post(self.endpoint, {"question": "How do I add a booking?"})

        self.assertEqual(response.status_code, 200)
        payload = mock_post.call_args.kwargs["json"]
        transmitted = str(payload)
        self.assertIn("Public SnipKlip help guide excerpts", transmitted)
        self.assertIn("Steps:", transmitted)
        self.assertNotIn("assistant-test@snipklip.local", transmitted)
        self.assertNotIn("salon_id", transmitted)
        self.assertNotIn("branch_id", transmitted)

    def test_retrieval_is_limited_to_help_corpus(self):
        chunks = retrieve("Where do I manage invoices?")
        self.assertEqual(chunks[0].title, "Billing and Invoices")
        self.assertTrue(all(chunk.route.startswith("/") for chunk in chunks))

    def test_coupon_synonym_and_plural_retrieval(self):
        singular = retrieve_with_meta("How do I create a coupon?")
        plural = retrieve_with_meta("Where do I manage coupons?")
        self.assertEqual(singular.chunks[0].title, "Coupons")
        self.assertEqual(plural.chunks[0].title, "Coupons")
        self.assertFalse(singular.unsupported)

    def test_staff_alias_prefers_employees(self):
        result = retrieve_with_meta("How do I add staff?")
        self.assertEqual(result.chunks[0].title, "Employees and Staff")
        self.assertFalse(result.unsupported)

    def test_appointment_alias_maps_to_bookings(self):
        result = retrieve_with_meta("How do I schedule an appointment?")
        self.assertEqual(result.chunks[0].title, "Bookings and Appointments")
        self.assertTrue(result.chunks[0].steps)

    def test_unsupported_zenoti_style_features(self):
        for question in (
            "How do I create gift cards?",
            "Set up loyalty points and referral rewards",
            "Launch a marketing automation campaign",
            "Enable the customer mobile app",
        ):
            result = retrieve_with_meta(question)
            self.assertTrue(result.unsupported, msg=question)
            self.assertEqual(result.chunks[0].title, "Unsupported Features")

    @override_settings(LLM_API_KEY="", LLM_MODEL="", ASSISTANT_OFFLINE_MODE=True)
    def test_unsupported_api_response(self):
        response = self.client.post(
            self.endpoint,
            {"question": "How do I issue gift cards and loyalty points?"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertTrue(data["unsupported"])
        self.assertIn("not in the verified SnipKlip help guide", data["answer"])
        self.assertEqual(data["sources"][0]["route"], "/contact-us")

    @override_settings(LLM_API_KEY="", LLM_MODEL="", ASSISTANT_OFFLINE_MODE=True)
    def test_inventory_and_billing_guides(self):
        inventory = self.client.post(
            self.endpoint,
            {"question": "How do I add a product to inventory?"},
        )
        billing = self.client.post(
            self.endpoint,
            {"question": "How do I create an invoice at checkout?"},
        )
        self.assertEqual(inventory.data["data"]["sources"][0]["title"], "Inventory and Products")
        self.assertIn("/apps/e-commerce/product/manage-product", inventory.data["data"]["answer"])
        self.assertEqual(billing.data["data"]["sources"][0]["title"], "Billing and Invoices")
        self.assertIn("Prerequisites:", billing.data["data"]["answer"])

    def test_local_answer_includes_prerequisites_and_steps(self):
        chunks = retrieve("How do I add a booking?")
        answer = generate_answer("How do I add a booking?", chunks, unsupported=False)
        self.assertEqual(answer.provider, "local")
        self.assertIn("Prerequisites:", answer.text)
        self.assertIn("1.", answer.text)
        self.assertIn("/apps/bookings/manage-bookings", answer.text)

    def test_guide_chunks_expose_workflow_metadata(self):
        bookings = next(chunk for chunk in load_chunks() if chunk.title == "Bookings and Appointments")
        self.assertIn("appointment", bookings.aliases)
        self.assertTrue(bookings.prerequisites)
        self.assertGreaterEqual(len(bookings.steps), 4)
        self.assertTrue(bookings.limitations)
