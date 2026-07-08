from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
from backend.models import Branch, Expense
from api.views.expense import get_all_expenses

class CreateExpenseViewTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.branch = Branch.objects.create(branch_name='Test Branch')

    def test_create_expense_success(self):
        url = '/api/v3/expenses/'
        data = {
            'branch_id': self.branch.id,
            'description': 'Test Expense',
            'amount': 100.0,
        }
        request = self.factory.post(url, data, format='json')
        response = get_all_expenses(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Expense.objects.count(), 1)
        self.assertEqual(response.data['message'], 'Successfully Added Expense')

    # @patch('api.views.expense.Expense')  # Patch the Expense model in the views
    # def test_create_expense_exception(self, MockExpense):
    #     # Simulate an exception during expense creation
    #     mock_instance = MockExpense.objects.create.return_value
    #     mock_instance.save.side_effect = Exception('Mocked exception')

    #     url = '/api/v3/expenses/'
    #     data = {
    #         'branch_id': self.branch.id,
    #         'description': 'Test Expense',
    #         'amount': 100.0,
    #     }
    #     request = self.factory.post(url, data, format='json')
    #     response = get_all_expenses(request)

    #     self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    #     self.assertEqual(response.data['message'], 'Error')
    #     self.assertEqual(Expense.objects.count(), 0)
