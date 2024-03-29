import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main Course'):
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinnamon'):
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    defaults = {
        'title': 'Sample Recipe',
        'time_minutes': 10,
        'price': 5.00,
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipesApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required_for_retrieving_recipes(self):
        response = self.client.get(RECIPES_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipesApiTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            password='testTEST12345',
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        response = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_recipes_limited_to_user(self):
        self.user2 = get_user_model().objects.create_user(
            email='test2@gmail.com',
            password='testTEST123452',
        )
        sample_recipe(user=self.user)
        sample_recipe(user=self.user2)

        response = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, serializer.data)

    def test_view_recipe_detail(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        response = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(response.data, serializer.data)

    def test_create_basic_recipe_successful(self):
        payload = {
            'title': 'Choclate Cheesecake',
            'time_minutes': 10,
            'price': 5.00,
        }
        response = self.client.post(RECIPES_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Dessert')
        payload = {
            'title': 'Avocado Lime Cheesecake',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 10,
            'price': 5.00,
        }
        response = self.client.post(RECIPES_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        ingredient1 = sample_ingredient(user=self.user, name='Salt')
        ingredient2 = sample_ingredient(user=self.user, name='Sugar')
        payload = {
            'title': 'Avocado Lime Cheesecake',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 10,
            'price': 5.00,
        }
        response = self.client.post(RECIPES_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='Lunch')

        payload = {
            'title': 'Chicken tikka',
            'tags': [new_tag.id]
        }
        self.client.patch(detail_url(recipe.id), payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        payload = {
            'title': 'Chicken tikka',
            'time_minutes': 25,
            'price': 5.00,
        }
        self.client.put(detail_url(recipe.id), payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)


class RecipeImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user('test@gmail.com', 'testpass12345')
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            response = self.client.post(url, {'image': ntf})
        self.recipe.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('image', response.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.recipe.id)
        response = self.client.post(url, {'image': 'badimage'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filer_recipe_by_tags(self):
        recipe1 = sample_recipe(user=self.user, title='Thai Vegetable Curry')
        recipe2 = sample_recipe(user=self.user, title='Aunergine with tahini')
        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Vegetarian')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = sample_recipe(user=self.user, title='Fish and Chips')
        response = self.client.get(
            RECIPES_URL,
            {
                'tags': f'{tag1.id},{tag2.id}',
            }
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, response.data)
        self.assertIn(serializer2.data, response.data)
        self.assertNotIn(serializer3.data, response.data)

    def test_filer_recipe_by_ingredients(self):
        recipe1 = sample_recipe(user=self.user, title='Thai Vegetable Curry')
        recipe2 = sample_recipe(user=self.user, title='Aunergine with tahini')
        ingredient1 = sample_ingredient(user=self.user, name='Salt')
        ingredient2 = sample_ingredient(user=self.user, name='Sugar')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = sample_recipe(user=self.user, title='Fish and Chips')
        response = self.client.get(
            RECIPES_URL,
            {
                'ingredients': f'{ingredient1.id},{ingredient2.id}',
            }
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, response.data)
        self.assertIn(serializer2.data, response.data)
        self.assertNotIn(serializer3.data, response.data)
