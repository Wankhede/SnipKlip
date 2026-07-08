from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
'''
python manage.py test backend
python manage.py test backend.tests.testviews
'''

class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

    def test_reports_view(self):
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 200)

    def test_listings_view(self):
        response = self.client.get(reverse('listings'))
        self.assertEqual(response.status_code, 200)

    def test_add_listings_view(self):
        response = self.client.get(reverse('add_listings'))
        self.assertEqual(response.status_code, 200)

    def test_add_bookings_view(self):
        response = self.client.get(reverse('add_bookings'))
        self.assertEqual(response.status_code, 200)

    def test_add_customers_view(self):
        response = self.client.get(reverse('add_customers'))
        self.assertEqual(response.status_code, 200)

    def test_add_staff_view(self):
        response = self.client.get(reverse('add_staff'))
        self.assertEqual(response.status_code, 200)

    def test_customer_detail_view(self):
        response = self.client.get(reverse('customer_detail'))
        self.assertEqual(response.status_code, 200)

    def test_staff_detail_view(self):
        response = self.client.get(reverse('staff_detail'))
        self.assertEqual(response.status_code, 200)

    def test_add_products_view(self):
        response = self.client.get(reverse('add_products'))
        self.assertEqual(response.status_code, 200)

    def test_products_view(self):
        response = self.client.get(reverse('products'))
        self.assertEqual(response.status_code, 200)

    def test_support_view(self):
        response = self.client.get(reverse('support'))
        self.assertEqual(response.status_code, 200)

    def test_data_view(self):
        response = self.client.get(reverse('data'))
        self.assertEqual(response.status_code, 200)

    def test_customers_view(self):
        response = self.client.get(reverse('customers'))
        self.assertEqual(response.status_code, 200)

    def test_staff_view(self):
        response = self.client.get(reverse('staff'))
        self.assertEqual(response.status_code, 200)
