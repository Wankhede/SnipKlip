from django.test import TestCase
from api.views.employee import get_all_employees
from rest_framework.test import APIRequestFactory
from rest_framework.response import Response
from rest_framework import status
from backend.models import User
from backend.models import Branch, SalonDetails, Employee
from random import randint

class CreateEmployeeViewTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.salon_user = User.objects.create(username='salon_owner', password='password')
        self.salon_branch = SalonDetails.objects.create(user=self.salon_user)
        self.branch = Branch.objects.create(branch_name='Test Branch', salon=self.salon_branch)

    def test_create_employee_success(self):
        url = '/api/v3/employees/'
        data = {
            'user_id': self.salon_user.id,
            'branch_id': self.branch.id,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'mobile': '1234567890',
            'employee_type': 'Manager',
            'product_incentive': 10,
            'service_incentive': 15,
            'base_salary': 2000,
            'status': 'Active',
        }
        request = self.factory.post(url, data, format='json')
        response = get_all_employees(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Change to your expected status code
        self.assertEqual(Employee.objects.count(), 0)
        self.assertEqual(response.data['message'], 'Successfully retrieved all customers')

    def test_create_employee_existing_mobile(self):
        # Create a user with the same mobile number
        User.objects.create(username='existing_user', password='password', mobile='1234567890')

        url = '/api/v3/employees/'
        data = {
            'user_id': self.salon_user.id,
            'branch_id': self.branch.id,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'mobile': '1234567890',
            'employee_type': 'Employee',
            'product_incentive': 5,
            'service_incentive': 7,
            'base_salary': 1500,
            'status': 'Active',
        }
        request = self.factory.post(url, data, format='json')
        response = get_all_employees(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Mobile Numner Already Exists')
        self.assertEqual(Employee.objects.count(), 0)

    # Add more test cases as needed
