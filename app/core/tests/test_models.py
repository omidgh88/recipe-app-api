from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def sample_user(email='test@gmail.com', password='testTEST12345'):
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email_succeful(self):
        email = 'test@gmail.com'
        password = 'testTEST12345'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        email = 'test@GMAIL.COM'
        user = get_user_model().objects.create_user(
            email=email,
            password='testTEST12345',
        )
        self.assertEqual(user.email, email.lower())

    def test_new_user_with_invalid_email(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email=None,
                password='testTEST12345'
            )

    def test_create_new_superuser(self):
        user = get_user_model().objects.create_superuser(
            email='test@gmail.com',
            password='testTEST12345',
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_string_representation(self):
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Vegan',
        )
        self.assertEqual(str(tag), tag.name)
