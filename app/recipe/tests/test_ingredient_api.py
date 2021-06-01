from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required_for_retrieving_ingredients(self):
        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            password='testTEST12345',
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Salt')

        response = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        self.user2 = get_user_model().objects.create_user(
            email='test2@gmail.com',
            password='testTEST123452',
        )
        ingredient = Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user2, name='Salt')

        response = self.client.get(INGREDIENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        payload = {
            'name': 'Test Ingredient'
        }
        self.client.post(INGREDIENTS_URL, payload)
        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()
        self.assertTrue(exists)

    def test_create_ingredient_invalid_empty_name(self):
        payload = {
            'name': ''
        }
        response = self.client.post(INGREDIENTS_URL, payload)
        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()
        self.assertFalse(exists)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assign_to_recipes(self):
        ingredient1 = Ingredient.objects.create(user=self.user, name='Salt')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Sugar')
        recipe = Recipe.objects.create(
            title='Eggs and Toast',
            time_minutes=5,
            price=5.00,
            user=self.user
        )
        recipe.ingredients.add(ingredient1)
        response = self.client.get(INGREDIENTS_URL, {
            'assigned_only': 1
        })
        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)
