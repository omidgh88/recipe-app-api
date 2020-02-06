from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """test the users api public"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """test creating user with valid payload is successful"""
        payloads = {
            'email': 'test@gmail.com',
            'password': 'test1234',
            'name': 'Test user name',
        }
        res = self.client.post(CREATE_USER_URL, payloads)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payloads['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """test creating user that already exists fail"""
        payloads = {
            'email': 'test@gmail.com',
            'password': 'test1234',
        }
        create_user(**payloads)

        res = self.client.post(CREATE_USER_URL, payloads)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """test that password must be more that 5 characters"""
        payloads = {
            'email': 'test@gmail.com',
            'password': 'pw',
        }
        res = self.client.post(CREATE_USER_URL, payloads)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(
            email=payloads['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """test that a token is created for a user"""
        payload = {'email': 'omidgholami88@gmail.com', 'password': 'omid1234'}
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credential(self):
        """test that token is not created if credentials is not valid"""
        create_user(email='omidgholami88@gmail.com', password='omid1234')
        payload = {'email': 'omidgholami88@gmail.com',
                   'password': 'wrong pass'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """test that token is not created if user doesn't exist"""
        payload = {'email': 'omidgholami88@gmail.com', 'passwod': 'omid1234'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """test that token is not created if a field is missing"""
        payload = {'email': 'omidgholami88@gmail.com', 'passwod': ''}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
