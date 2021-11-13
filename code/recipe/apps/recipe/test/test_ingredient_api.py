from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

import json

from recipe.apps.recipe.serializers import IngredientSerializer
from recipe.apps.core.models import (
    Ingredient,
    Recipe
)

User = get_user_model()
INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    """Return ingredient detail URL"""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


class PublicIngredientsApiTests(APITestCase):
    """Test the publically available ingredients API"""

    def test_get_all_ingredients_without_authentication(self):
        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_ingredient_without_authentication(self):
        response = self.client.post(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_ingredient_without_authentication(self):
        url = detail_url(99)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_ingredient_without_authentication(self):
        url = detail_url(99)
        response = self.client.put(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_ingredient_without_authentication(self):
        url = detail_url(99)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GetIngredientsTest(APITestCase):
    """Test module for GET all ingredients API"""

    def setUp(self):
        self.user = User.objects.create_user(
            'test@test.com',
            'testpass'
        )

        self.client.force_authenticate(self.user)

    def test_get_all_user_ingredients(self):
        user_2 = User.objects.create_user(
            'other@test.com',
            'testpass'
        )

        ingredients = [
            Ingredient(
                user=self.user,
                name='Kale'
            ),
            Ingredient(
                user=self.user,
                name='Salt'
            ),
            Ingredient(
                user=user_2,
                name='Vinegar'
            ),
            Ingredient(
                user=user_2,
                name='Tumeric'
            )
        ]

        Ingredient.objects.bulk_create(ingredients)

        response = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.filter(
            user=self.user
        ).order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_ingredients_assigned_to_recipes(self):
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Apples'
        )

        ingredients = [
            Ingredient(
                user=self.user,
                name='Kale'
            ),
            Ingredient(
                user=self.user,
                name='Salt'
            ),
            Ingredient(
                user=self.user,
                name='Vinegar'
            )
        ]

        Ingredient.objects.bulk_create(ingredients)

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

        recipe.ingredients.add(ingredient)
        recipe_2.ingredients.add(ingredient)

        response = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(response.data), 1)


class GetIngredientTest(APITestCase):
    """Test module for GET single ingredient API"""

    def setUp(self):
        self.user = User.objects.create_user(
            'test@test.com',
            'testpass'
        )

        self.client.force_authenticate(self.user)

    def test_get_valid_ingredient(self):
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Vinegar'
        )

        url = detail_url(ingredient.id)
        response = self.client.get(url)

        serializer = IngredientSerializer(ingredient)

        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_ingredient_from_another_user(self):
        user_2 = User.objects.create_user(
            'other@test.com',
            'testpass'
        )

        ingredient = Ingredient.objects.create(
            user=user_2,
            name='Vinegar'
        )

        url = detail_url(ingredient.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_invalid_ingredient(self):
        url = detail_url(99)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CreateIngredientTest(APITestCase):
    """ Test module for inserting a new ingredient """

    def setUp(self):
        self.user = User.objects.create_user(
            'test@test.com',
            'testpass'
        )

        self.client.force_authenticate(self.user)

    def test_create_valid_ingredient(self):
        payload = {'name': 'Cabbage'}

        response = self.client.post(
            INGREDIENTS_URL,
            data=json.dumps(payload),
            content_type='application/json'
        )

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(exists)

    def test_create_invalid_ingredient(self):
        payload = {'name': ''}

        response = self.client.post(
            INGREDIENTS_URL,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_ingredient_with_name_that_already_exists(self):
        Ingredient.objects.create(
            user=self.user,
            name='Cabbage'
        )

        payload = {'name': 'Cabbage'}

        response = self.client.post(
            INGREDIENTS_URL,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UpdateIngredientTest(APITestCase):
    """ Test module for updating an existing ingredient record """

    def setUp(self):
        self.user = User.objects.create_user(
            'test@test.com',
            'testpass'
        )

        self.ingredient = Ingredient.objects.create(
            user=self.user,
            name='Vinegar'
        )

        self.client.force_authenticate(self.user)

    def test_valid_update_ingredient(self):
        payload = {'name': 'Cabbage'}

        url = detail_url(self.ingredient.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_update_ingredient(self):
        payload = {'name': ''}

        url = detail_url(self.ingredient.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_ingredient_with_name_that_already_exists(self):
        Ingredient.objects.create(
            user=self.user,
            name='Cabbage'
        )

        payload = {'name': 'Cabbage'}

        url = detail_url(self.ingredient.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_ingredient_from_another_user(self):
        user_2 = User.objects.create_user(
            'other@test.com',
            'testpass'
        )

        ingredient = Ingredient.objects.create(
            user=user_2,
            name='Salt'
        )

        payload = {'name': 'Cabbage'}

        url = detail_url(ingredient.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DeleteIngredientTest(APITestCase):
    """ Test module for deleting an existing ingredient record """

    def setUp(self):
        self.user = User.objects.create_user(
            'test@test.com',
            'testpass'
        )

        self.client.force_authenticate(self.user)

    def test_valid_delete_ingredient(self):
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Vinegar'
        )

        url = detail_url(ingredient.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_invalid_delete_ingredient(self):
        url = detail_url(99)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_ingredient_from_another_user(self):
        user_2 = User.objects.create_user(
            'other@test.com',
            'testpass'
        )

        ingredient = Ingredient.objects.create(
            user=user_2,
            name='Salt'
        )

        url = detail_url(ingredient.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
