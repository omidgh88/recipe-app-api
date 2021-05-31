from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required_for_retrieving_tags(self):
        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            password='testTEST12345',
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        response = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_tags_limited_to_user(self):
        self.user2 = get_user_model().objects.create_user(
            email='test2@gmail.com',
            password='testTEST123452',
        )
        tag = Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user2, name='Dessert')

        response = self.client.get(TAGS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        payload = {
            'name': 'Test Tag'
        }
        self.client.post(TAGS_URL, payload)
        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()
        self.assertTrue(exists)

    def test_create_tag_invalid_empty_name(self):
        payload = {
            'name': ''
        }
        response = self.client.post(TAGS_URL, payload)
        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()
        self.assertFalse(exists)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
