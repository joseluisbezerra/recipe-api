import tempfile
import json
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from recipe.apps.core.models import (
    Tag,
    Recipe,
    Ingredient
)

from recipe.apps.recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
)


RECIPES_URL = reverse('recipe:recipe-list')
User = get_user_model()


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main course'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinnamon'):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00,
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipesApiTests(APITestCase):
    """Test the publically available recipes API"""

    def test_get_all_recipes_without_authentication(self):
        response = self.client.get(RECIPES_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_recipe_without_authentication(self):
        response = self.client.post(RECIPES_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_recipe_without_authentication(self):
        url = detail_url(99)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_recipe_without_authentication(self):
        url = detail_url(99)
        response = self.client.put(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_recipe_without_authentication(self):
        url = detail_url(99)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GetRecipesTest(APITestCase):
    """Test module for GET all recipes API"""

    def setUp(self):
        self.user = User.objects.create_user(
            'test@test.com',
            'testpass'
        )

        self.client.force_authenticate(self.user)

    def test_get_all_user_recipes(self):
        user_2 = User.objects.create_user(
            'other@test.com',
            'password123'
        )

        sample_recipe(user=user_2)
        sample_recipe(user=self.user)

        response = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, serializer.data)

    def test_filter_recipes_by_tags(self):
        recipe = sample_recipe(user=self.user, title='Thai vegetable curry')
        recipe_2 = sample_recipe(user=self.user, title='Aubergine with tahini')
        recipe_3 = sample_recipe(user=self.user, title='Fish and chips')

        tag = sample_tag(user=self.user, name='Vegan')
        tag_2 = sample_tag(user=self.user, name='Vegetarian')

        recipe.tags.add(tag)
        recipe_2.tags.add(tag_2)

        response = self.client.get(
            RECIPES_URL,
            {'tags': f'{tag.id},{tag_2.id}'}
        )

        serializer = RecipeSerializer(recipe_3)

        self.assertEqual(len(response.data), 2)
        self.assertNotIn(serializer.data, response.data)

    def test_filter_recipes_by_ingredients(self):
        recipe = sample_recipe(user=self.user, title='Posh beans on toast')
        recipe_2 = sample_recipe(user=self.user, title='Chicken cacciatore')
        recipe_3 = sample_recipe(user=self.user, title='Steak and mushrooms')

        ingredient = sample_ingredient(user=self.user, name='Feta cheese')
        ingredient_2 = sample_ingredient(user=self.user, name='Chicken')

        recipe.ingredients.add(ingredient)
        recipe_2.ingredients.add(ingredient_2)

        response = self.client.get(
            RECIPES_URL,
            {'ingredients': f'{ingredient.id},{ingredient_2.id}'}
        )

        serializer = RecipeSerializer(recipe_3)

        self.assertEqual(len(response.data), 2)
        self.assertNotIn(serializer.data, response.data)


class GetRecipeTest(APITestCase):
    """Test module for GET single recipe API"""

    def setUp(self):
        self.user = User.objects.create_user(
            'test@test.com',
            'testpass'
        )

        self.client.force_authenticate(self.user)

    def test_get_valid_recipe(self):
        recipe = sample_recipe(user=self.user)

        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        response = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_recipe_from_another_user(self):
        user_2 = User.objects.create_user(
            'other@test.com',
            'testpass'
        )

        recipe = sample_recipe(user=user_2)

        url = detail_url(recipe.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_invalid_recipe(self):
        url = detail_url(99)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CreateRecipeTest(APITestCase):
    """ Test module for inserting a new recipe """

    def setUp(self):
        self.user = User.objects.create_user(
            'test@test.com',
            'testpass'
        )

        self.client.force_authenticate(self.user)

    def test_create_basic_recipe(self):
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': 5.00
        }

        response = self.client.post(
            RECIPES_URL,
            data=json.dumps(payload),
            content_type='application/json'
        )

        exists = Recipe.objects.filter(
            user=self.user,
            title=payload['title']
        ).exists()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(exists)

    def test_create_recipe_with_tags(self):
        tag = sample_tag(user=self.user, name='Vegan')
        tag_2 = sample_tag(user=self.user, name='Dessert')

        payload = {
            'title': 'Avocado lime cheesecake',
            'tags': [tag.id, tag_2.id],
            'time_minutes': 60,
            'price': 20.00
        }

        response = self.client.post(
            RECIPES_URL,
            data=json.dumps(payload),
            content_type='application/json'
        )

        recipe = Recipe.objects.get(id=response.data['id'])
        tags = recipe.tags.all()

        self.assertEqual(tags.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_recipe_with_ingredients(self):
        ingredient = sample_ingredient(user=self.user, name='Prawns')
        ingredient_2 = sample_ingredient(user=self.user, name='Ginger')

        payload = {
            'title': 'Thai prawn red curry',
            'ingredients': [ingredient.id, ingredient_2.id],
            'time_minutes': 20,
            'price': 7.00
        }

        response = self.client.post(
            RECIPES_URL,
            data=json.dumps(payload),
            content_type='application/json'
        )

        recipe = Recipe.objects.get(id=response.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_recipe_with_image(self):
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)

            payload = {
                'title': 'Thai prawn red curry',
                'image': ntf,
                'time_minutes': 20,
                'price': 7.00
            }

            response = self.client.post(
                RECIPES_URL,
                data=payload,
                format='multipart'
            )

        recipe = Recipe.objects.get(id=response.data.get('id'))

        self.assertIn('image', response.data)
        self.assertTrue(os.path.exists(recipe.image.path))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_recipe_with_invalid_title(self):
        payload = {
            'title': '',
            'time_minutes': 30,
            'price': 5.00
        }

        response = self.client.post(
            RECIPES_URL,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_title_that_already_exists(self):
        Recipe.objects.create(
            user=self.user,
            title='Chocolate cheesecake',
            time_minutes=20,
            price=8.00
        )

        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': 5.00
        }

        response = self.client.post(
            RECIPES_URL,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_invalid_time_minutes(self):
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': -5,
            'price': 5.00
        }

        response = self.client.post(
            RECIPES_URL,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_invalid_price(self):
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': -6
        }

        response = self.client.post(
            RECIPES_URL,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_invalid_tags(self):
        tag = sample_tag(user=self.user, name='Vegan')

        payload = {
            'title': 'Avocado lime cheesecake',
            'tags': [tag.id, 99],
            'time_minutes': 60,
            'price': 20.00
        }

        response = self.client.post(
            RECIPES_URL,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_tags_from_another_user(self):
        user_2 = User.objects.create_user(
            'other@test.com',
            'testpass'
        )

        tag = sample_tag(user=user_2, name='Vegan')

        payload = {
            'title': 'Avocado lime cheesecake',
            'tags': [tag.id],
            'time_minutes': 60,
            'price': 20.00
        }

        response = self.client.post(
            RECIPES_URL,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_invalid_ingredients(self):
        ingredient = sample_ingredient(user=self.user, name='Prawns')

        payload = {
            'title': 'Thai prawn red curry',
            'ingredients': [ingredient.id, 99],
            'time_minutes': 20,
            'price': 7.00
        }

        response = self.client.post(
            RECIPES_URL,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_ingredients_from_another_user(self):
        user_2 = User.objects.create_user(
            'other@test.com',
            'testpass'
        )

        ingredient = sample_ingredient(user=user_2, name='Prawns')

        payload = {
            'title': 'Thai prawn red curry',
            'ingredients': [ingredient.id],
            'time_minutes': 20,
            'price': 7.00
        }

        response = self.client.post(
            RECIPES_URL,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_invalid_image(self):
        payload = {
            'title': 'Thai prawn red curry',
            'image': 'notimage',
            'time_minutes': 20,
            'price': 7.00
        }

        response = self.client.post(
            RECIPES_URL,
            data=payload,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UpdateRecipeTest(APITestCase):
    """ Test module for updating an existing recipe record """

    def setUp(self):
        self.user = User.objects.create_user(
            'test@test.com',
            'testpass'
        )

        self.recipe = sample_recipe(user=self.user)
        self.recipe.tags.add(sample_tag(user=self.user))
        self.recipe.ingredients.add(sample_ingredient(user=self.user))

        self.client.force_authenticate(self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_update_recipe(self):
        payload = {
            'title': 'Spaghetti carbonara',
            'time_minutes': 25,
            'price': 5.00
        }

        url = detail_url(self.recipe.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.recipe.refresh_from_db()
        tags = self.recipe.tags.all()
        ingredients = self.recipe.ingredients.all()

        self.assertEqual(self.recipe.title, payload['title'])
        self.assertEqual(self.recipe.price, payload['price'])
        self.assertEqual(self.recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(tags.count(), 1)
        self.assertEqual(ingredients.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partial_update_recipe(self):
        new_tag = sample_tag(user=self.user, name='Curry')

        payload = {
            'title': 'Chicken tikka',
            'tags': [new_tag.id]
        }

        url = detail_url(self.recipe.id)
        response = self.client.patch(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.recipe.refresh_from_db()
        tags = self.recipe.tags.all()

        self.assertIn(new_tag, tags)
        self.assertEqual(self.recipe.title, payload['title'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_recipe_with_tags(self):
        tag = sample_tag(user=self.user, name='Vegan')
        tag_2 = sample_tag(user=self.user, name='Dessert')

        payload = {
            'title': 'Avocado lime cheesecake',
            'tags': [tag.id, tag_2.id],
            'time_minutes': 60,
            'price': 20.00
        }

        url = detail_url(self.recipe.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.recipe.refresh_from_db()
        tags = self.recipe.tags.all()

        self.assertEqual(tags.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_recipe_with_ingredients(self):
        ingredient = sample_ingredient(user=self.user, name='Prawns')
        ingredient_2 = sample_ingredient(user=self.user, name='Ginger')

        payload = {
            'title': 'Thai prawn red curry',
            'ingredients': [ingredient.id, ingredient_2.id],
            'time_minutes': 20,
            'price': 7.00
        }

        url = detail_url(self.recipe.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.recipe.refresh_from_db()
        ingredients = self.recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_recipe_with_image(self):
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)

            payload = {
                'title': 'Thai prawn red curry',
                'image': ntf,
                'time_minutes': 20,
                'price': 7.00
            }

            url = detail_url(self.recipe.id)
            response = self.client.put(
                url,
                data=payload,
                format='multipart'
            )

        self.recipe.refresh_from_db()

        self.assertIn('image', response.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_recipe_from_another_user(self):
        user_2 = User.objects.create_user(
            'other@test.com',
            'testpass'
        )

        recipe = sample_recipe(user=user_2)

        payload = {
            'title': 'Spaghetti carbonara',
            'time_minutes': 25,
            'price': 5.00
        }

        url = detail_url(recipe.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_recipe_with_invalid_title(self):
        payload = {
            'title': '',
            'time_minutes': 30,
            'price': 5.00
        }

        url = detail_url(self.recipe.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_recipe_with_title_that_already_exists(self):
        Recipe.objects.create(
            user=self.user,
            title='Chocolate cheesecake',
            time_minutes=20,
            price=8.00
        )

        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': 5.00
        }

        url = detail_url(self.recipe.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_recipe_with_invalid_time_minutes(self):
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': -5,
            'price': 5.00
        }

        url = detail_url(self.recipe.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_recipe_with_invalid_price(self):
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': -6
        }

        url = detail_url(self.recipe.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_recipe_with_invalid_tags(self):
        tag = sample_tag(user=self.user, name='Vegan')

        payload = {
            'title': 'Avocado lime cheesecake',
            'tags': [tag.id, 99],
            'time_minutes': 60,
            'price': 20.00
        }

        url = detail_url(self.recipe.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_recipe_with_tags_from_another_user(self):
        user_2 = User.objects.create_user(
            'other@test.com',
            'testpass'
        )

        tag = sample_tag(user=user_2, name='Vegan')

        payload = {
            'title': 'Avocado lime cheesecake',
            'tags': [tag.id],
            'time_minutes': 60,
            'price': 20.00
        }

        url = detail_url(self.recipe.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_recipe_with_invalid_ingredients(self):
        ingredient = sample_ingredient(user=self.user, name='Prawns')

        payload = {
            'title': 'Thai prawn red curry',
            'ingredients': [ingredient.id, 99],
            'time_minutes': 20,
            'price': 7.00
        }

        url = detail_url(self.recipe.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_recipe_with_ingredients_from_another_user(self):
        user_2 = User.objects.create_user(
            'other@test.com',
            'testpass'
        )

        ingredient = sample_ingredient(user=user_2, name='Prawns')

        payload = {
            'title': 'Thai prawn red curry',
            'ingredients': [ingredient.id],
            'time_minutes': 20,
            'price': 7.00
        }

        url = detail_url(self.recipe.id)
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_recipe_with_invalid_image(self):
        payload = {
            'title': 'Thai prawn red curry',
            'image': 'notimage',
            'time_minutes': 20,
            'price': 7.00
        }

        url = detail_url(self.recipe.id)
        response = self.client.put(
            url,
            data=payload,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DeleteRecipeTest(APITestCase):
    """ Test module for deleting an existing recipe record """

    def setUp(self):
        self.user = User.objects.create_user(
            'test@test.com',
            'testpass'
        )

        self.client.force_authenticate(self.user)

    def test_valid_delete_recipe(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_invalid_delete_recipe(self):
        url = detail_url(99)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_recipe_from_another_user(self):
        user_2 = User.objects.create_user(
            'other@test.com',
            'testpass'
        )

        recipe = sample_recipe(user=user_2)
        recipe.tags.add(sample_tag(user=user_2))
        recipe.ingredients.add(sample_ingredient(user=user_2))

        url = detail_url(recipe.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
