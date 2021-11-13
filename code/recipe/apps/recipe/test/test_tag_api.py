from recipe.apps.recipe.serializers import TagSerializer
from recipe.apps.core.models import (
    Tag,
    Recipe
)

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

import json


User = get_user_model()
TAGS_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    """Return tag detail URL"""
    return reverse('recipe:tag-detail', args=[tag_id])


class PublicTagsApiTests(APITestCase):
    """Test the publically available tags API"""

    def test_get_all_tags_without_authentication(self):
        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_tag_without_authentication(self):
        response = self.client.post(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_tag_without_authentication(self):
        url = detail_url(99)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_tag_without_authentication(self):
        url = detail_url(99)
        response = self.client.put(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_tag_without_authentication(self):
        url = detail_url(99)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GetTagsTest(APITestCase):
    """Test module for GET all tags API"""

    def setUp(self):
        self.user = User.objects.create_user(
            'test@test.com',
            'testpass'
        )

        self.client.force_authenticate(self.user)

    def test_get_all_user_tags(self):
        user_2 = User.objects.create_user(
            'other@test.com',
            'testpass'
        )

        tags = [
            Tag(
                user=self.user,
                name='Vegan'
            ),
            Tag(
                user=self.user,
                name='Dessert'
            ),
            Tag(
                user=user_2,
                name='Fruity'
            ),
            Tag(
                user=user_2,
                name='Comfort Food'
            )
        ]

        Tag.objects.bulk_create(tags)

        response = self.client.get(TAGS_URL)

        tags = Tag.objects.filter(
            user=self.user
        ).order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_tags_assigned_to_recipes(self):
        tag = Tag.objects.create(
            user=self.user,
            name='Vegan'
        )

        tags = [
            Tag(
                user=self.user,
                name='Dessert'
            ),
            Tag(
                user=self.user,
                name='Fruity'
            ),
            Tag(
                user=self.user,
                name='Comfort Food'
            )
        ]

        Tag.objects.bulk_create(tags)

        recipe = Recipe.objects.create(
            title='Foo Bar',
            time_minutes=10,
            price=5,
            user=self.user
        )

        recipe_2 = Recipe.objects.create(
            title='Bar Foo',
            time_minutes=5,
            price=10,
            user=self.user
        )

        recipe.tags.add(tag)
        recipe_2.tags.add(tag)

        response = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(response.data), 1)


class GetTagTest(APITestCase):
    """Test module for GET single tag API"""

    def setUp(self):
        self.user = User.objects.create_user(
            'test@test.com',
            'testpass'
        )

        self.client.force_authenticate(self.user)

    def test_get_valid_tag(self):
        tag = Tag.objects.create(
            user=self.user,
            name='Vegan'
        )

        url = detail_url(tag.id)
        response = self.client.get(url)

        serializer = TagSerializer(tag)

        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_tag_from_another_user(self):
        user_2 = User.objects.create_user(
            'other@test.com',
            'testpass'
        )

        tag = Tag.objects.create(
            user=user_2,
            name='Vegan'
        )

        url = detail_url(tag.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_invalid_tag(self):
        url = detail_url(99)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CreateTagTest(APITestCase):
    """ Test module for inserting a new tag """

    def setUp(self):
        self.user = User.objects.create_user(
            'test@test.com',
            'testpass'
        )

        self.client.force_authenticate(self.user)

    def test_create_valid_tag(self):
        payload = {'name': 'Vegan'}

        response = self.client.post(
            TAGS_URL,
            data=json.dumps(payload),
            content_type='application/json'
        )

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(exists)

    def test_create_invalid_tag(self):
        payload = {'name': ''}

        response = self.client.post(
            TAGS_URL,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_tag_with_name_that_already_exists(self):
        Tag.objects.create(
            user=self.user,
            name='Dessert'
        )

        payload = {'name': 'Dessert'}

        response = self.client.post(
            TAGS_URL,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UpdateTagTest(APITestCase):
    """ Test module for updating an existing tag record """

    def setUp(self):
        self.user = User.objects.create_user(
            'test@test.com',
            'testpass'
        )

        self.tag = Tag.objects.create(
            user=self.user,
            name='Vegan'
        )

        self.client.force_authenticate(self.user)

    def test_valid_update_tag(self):
        payload = {'name': 'Dessert'}

        url = detail_url(self.tag.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_update_tag(self):
        payload = {'name': ''}

        url = detail_url(self.tag.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_tag_with_name_that_already_exists(self):
        Tag.objects.create(
            user=self.user,
            name='Dessert'
        )

        payload = {'name': 'Dessert'}

        url = detail_url(self.tag.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_tag_from_another_user(self):
        user_2 = User.objects.create_user(
            'other@test.com',
            'testpass'
        )

        tag = Tag.objects.create(
            user=user_2,
            name='Fruity'
        )

        payload = {'name': 'Dessert'}

        url = detail_url(tag.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DeleteTagTest(APITestCase):
    """ Test module for deleting an existing tag record """

    def setUp(self):
        self.user = User.objects.create_user(
            'test@test.com',
            'testpass'
        )

        self.client.force_authenticate(self.user)

    def test_valid_delete_tag(self):
        tag = Tag.objects.create(
            user=self.user,
            name='Vegan'
        )

        url = detail_url(tag.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_invalid_delete_tag(self):
        url = detail_url(99)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_tag_from_another_user(self):
        user_2 = User.objects.create_user(
            'other@test.com',
            'testpass'
        )

        tag = Tag.objects.create(
            user=user_2,
            name='Fruity'
        )

        url = detail_url(tag.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
