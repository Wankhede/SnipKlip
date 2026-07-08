from django.test import TestCase
from django.contrib.auth.models import User
from ..models import UserType, SalonDetails

class UserTypeTest(TestCase):
    def setUp(self):
        UserType.objects.create(name='Test User Type')

    def test_user_type_name(self):
        user_type = UserType.objects.get(id=1)
        expected_name = f'{user_type.name}'
        self.assertEquals(expected_name, 'Test User Type')

class SalonDetailsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        SalonDetails.objects.create(
            user=self.user,
            name='Test Salon',
            email='test@test.com',
            reg_no='123456',
            contact_no='1234567890',
            owner_name='Test Owner',
            owner_email='owner@test.com'
        )

    def test_salon_details_name(self):
        salon = SalonDetails.objects.get(id=1)
        expected_name = f'{salon.name}'
        self.assertEquals(expected_name, 'Test Salon')

    def test_salon_details_owner_name(self):
        salon = SalonDetails.objects.get(id=1)
        expected_owner_name = f'{salon.owner_name}'
        self.assertEquals(expected_owner_name, 'Test Owner')
