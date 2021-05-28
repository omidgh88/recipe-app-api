from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'testTEST12345',
            'name': 'Test Name',
        }
        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**response.data)
        self.assertTrue(user.check_password)

    def test_user_exists_failed(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'testTEST12345',
            'name': 'Test Name',
        }
        create_user(**payload)
        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_with_short_password(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'sh',
            'name': 'Test Name',
        }
        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'testTEST12345',
        }
        create_user(**payload)
        response = self.client.post(TOKEN_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_create_token_invalid_credentials_failed(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'testTEST12345',
        }
        create_user(**payload)
        payload_wrong_password = {
            'email': 'test@gmail.com',
            'password': 'wrongpassword',
        }
        response = self.client.post(TOKEN_URL, payload_wrong_password)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)

    def test_create_token_no_user_failed(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'testTEST12345',
        }
        response = self.client.post(TOKEN_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)

    def test_create_token_empty_password_failed(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'testTEST12345',
        }
        create_user(**payload)
        payload_empty_password = {
            'email': 'test@gmail.com',
            'password': '',
        }
        response = self.client.post(TOKEN_URL, payload_empty_password)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
