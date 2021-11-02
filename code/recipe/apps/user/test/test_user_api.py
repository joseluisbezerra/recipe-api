from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')

User = get_user_model()


def create_user(**params):
    """Helper function to create new user"""
    return User.objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating using with a valid payload is successful"""

        payload = {
            'email': 'test@test.com',
            'password': 'testpass',
            'name': 'name'
        }

        response = self.client.post(CREATE_USER_URL, payload)

        user = User.objects.get(**response.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', response.data)

    def test_user_exists(self):
        """Test creating a user that already exists fails"""

        payload = {
            'email': 'test@test.com',
            'password': 'testpass',
            'name': 'Test'
        }

        create_user(**payload)

        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that password must be more than 5 characters"""

        payload = {
            'email': 'test@test.com',
            'password': 'pw',
            'name': 'Test'
        }

        response = self.client.post(CREATE_USER_URL, payload)

        user_exists = User.objects.filter(email=payload['email']).exists()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that a token is created for the user"""

        payload = {
            'email': 'test@test.com',
            'password': 'testpass'
        }

        create_user(**payload)

        response = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Test that token is not created if invalid credentials are given"""

        create_user(email='test@test.com', password='testpass')

        payload = {
            'email': 'test@test.com',
            'password': 'wrong'
        }

        response = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test that token is not created if user doens't exist"""

        payload = {
            'email': 'test@test.com',
            'password': 'testpass'
        }

        response = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """Test that email and password are required"""

        payload = {
            'email': 'one',
            'password': ''
        }

        response = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)