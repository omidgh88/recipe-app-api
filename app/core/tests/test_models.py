from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTest(TestCase):
    def test_create_user_with_email_successful(self):
        """ create an user with only email and password """
        email = "omid@gmail.com"
        password = "omid1234"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """test the email of new users is normalized
        (domain case insensitive)"""
        email = 'omid@GMAIL.COM'
        user = get_user_model().objects.create_user(email, 'omid1234')

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'omid1234')

    def test_create_new_super_user(self):
        """test if we can create new superuser"""
        user = get_user_model().objects.create_superuser(
            'omid@gmail.com',
            'omid1234'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
