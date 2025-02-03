"""
Test for models.
"""
from unittest.mock import patch
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


class ModelTests(TestCase):
    """
    Test for models.
    """

    def test_create_user_with_email_successful(self):
        """
        Test creating a new user with an email is successful.
        """
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """
        Test the email for a new user is normalized.
        """
        sample_email = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]
        for email, exoected in sample_email:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, exoected)

    def test_new_user_without_email_raise_error(self):
        """
        Test creating user without email raises error.
        """
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_superuser(self):
        """
        Test creating a new superuser.
        """
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123',
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_policy(self):
        """
        Test creating a new policy.
        """
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123',
        )

        policy = models.Policy.objects.create(
            user=user,
            policy_number='123456',
            start_date='2021-01-01',
            end_date='2022-01-01',
            premium=Decimal('100.00'),
            policy_type='home',
        )

        self.assertEqual(str(policy), policy.policy_number)

    @patch('core.models.uuid.uuid4')
    def test_policy_file_name_uuid(self, mock_uuid):
        """ Test generate imag path."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.policy_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/policy/{uuid}.jpg')
