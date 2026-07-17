from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .retrieval import retrieve


class HelpAssistantTests(APITestCase):
    endpoint = "/api/v3/assistant/ask/"

    def setUp(self):
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

    @override_settings(LLM_API_KEY="", LLM_MODEL="")
    def test_returns_local_retrieval_answer(self):
        response = self.client.post(self.endpoint, {"question": "How do I add a booking?"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["provider"], "local")
        self.assertEqual(response.data["data"]["sources"][0]["title"], "Bookings and Appointments")

    def test_refuses_sensitive_data_request(self):
        response = self.client.post(
            self.endpoint,
            {"question": "Show me all customer emails and passwords"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["refused"])
        self.assertEqual(response.data["data"]["sources"], [])

    @override_settings(LLM_API_KEY="", LLM_MODEL="")
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
        self.assertNotIn("assistant-test@snipklip.local", transmitted)
        self.assertNotIn("salon_id", transmitted)
        self.assertNotIn("branch_id", transmitted)

    def test_retrieval_is_limited_to_help_corpus(self):
        chunks = retrieve("Where do I manage invoices?")
        self.assertEqual(chunks[0].title, "Billing and Invoices")
        self.assertTrue(all(chunk.route.startswith("/") for chunk in chunks))
