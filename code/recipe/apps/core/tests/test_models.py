from django.test import TestCase
from django.contrib.auth import get_user_model


User = get_user_model()


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful"""

        email = 'test@dev.com'
        password = 'Password123'

        user = User.objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized"""

        email = 'test@LONDONAPPDEV.com'

        user = User.objects.create_user(
            email=email,
            password='test123'
        )

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating user with no email raises error"""

        with self.assertRaises(ValueError):
            User.objects.create_user(
                email=None,
                password='test12345'
            )

    def test_create_new_superuser(self):
        """Test creating a new superuser"""

        user = User.objects.create_superuser(
            email='teste@dev.com',
            password='Test12345'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
