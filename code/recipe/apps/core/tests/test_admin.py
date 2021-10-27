from rest_framework import status

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import (
    TestCase,
    Client
)

User = get_user_model()


class AdminSiteTests(TestCase):

    def setUp(self):
        self.client = Client()

        admin_user = User.objects.create_superuser(
            email='admin@dev.com',
            password='password123'
        )

        self.client.force_login(admin_user)

        self.user = User.objects.create_user(
            email='test@dev.com',
            password='password123',
            name='Foo bar',
        )

    def test_users_listed(self):
        """Test that users are listed on the user page"""

        url = reverse('admin:core_user_changelist')
        response = self.client.get(url)

        self.assertContains(response, self.user.name)
        self.assertContains(response, self.user.email)

    def test_user_page_change(self):
        """Test that the user edit page works"""

        url = reverse(
            'admin:core_user_change',
            args=[self.user.id]
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_user_page(self):
        """Test that the create user page works"""

        url = reverse('admin:core_user_add')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
