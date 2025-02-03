"""
Tests for policy API's
"""
from decimal import Decimal
from datetime import datetime
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Policy

from policy.serializers import (
    PolicySerializer,
    PolicyDetailSerializer,
)


POLICY_URL = reverse('policy:policy-list')


def detail_url(policy_id):
    """
    Return policy detail URL
    """
    return reverse('policy:policy-detail', args=[policy_id])


def image_upload_url(policy_id):
    """
    Create and return a Policy detail URL.
    """
    return reverse('policy:policy-upload-image', args=[policy_id])


def create_policy(user, **params):
    """
    Create and return a sample policy
    """
    defaults = {
        'policy_number': '123456',
        'policy_type': 'Home',
        'premium': Decimal('100.00'),
        'start_date': '2021-01-01',
        'end_date': '2022-01-01',
        'link': 'https://example.com/policy.pdf',
    }
    defaults.update(params)

    policy = Policy.objects.create(user=user, **defaults)

    return policy


def create_user(**params):
    """
    Create and return a new user
    """
    return get_user_model().objects.create_user(**params)


class PublicPolicyApiTests(TestCase):
    """
    Test unauthenticated policy API access
    """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """
        Test auth is required for retrieving policies to call API
        """
        res = self.client.get(POLICY_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatePolicyApiTests(TestCase):
    """
    Test authenticated policy API access
    """

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com',
            password='test123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_policies(self):
        """
        Test retrieving policies
        """
        create_policy(user=self.user)
        create_policy(user=self.user)

        res = self.client.get(POLICY_URL)

        policies = Policy.objects.all().order_by('-id')
        serializer = PolicySerializer(policies, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_policies_limited_to_user(self):
        """
        Test that policies returned are for the authenticated user
        """
        other_user = create_user(
            email='other@example.com',
            password='test123',
        )
        create_policy(user=other_user)
        create_policy(user=self.user)

        res = self.client.get(POLICY_URL)

        policies = Policy.objects.filter(user=self.user)
        serializer = PolicySerializer(policies, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_policy_detail(self):
        """
        Test viewing a policy detail
        """
        policy = create_policy(user=self.user)

        url = detail_url(policy.id)
        res = self.client.get(url)

        serializer = PolicyDetailSerializer(policy)
        self.assertEqual(res.data, serializer.data)

    def test_create_policy(self):
        """
        Test Create a policy
        """
        payload = {
            'policy_number': '123456',
            'premium': Decimal('100.00'),
            'policy_type': 'Home',
            'start_date': '2021-01-01',
            'end_date': '2022-01-01',
        }
        res = self.client.post(POLICY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        policy = Policy.objects.get(id=res.data['id'])
        for k, v in payload.items():
            if k in ['start_date', 'end_date']:
                v = datetime.strptime(v, '%Y-%m-%d').date()
            self.assertEqual(getattr(policy, k), v)
        self.assertEqual(policy.user, self.user)

    def test_partial_update(self):
        """
        Test updating a policy with patch
        """
        original_link = "https://example.com/policy.pdf"
        policy = create_policy(
            user=self.user,
            policy_number='123456',
            link=original_link,
        )
        payload = {'policy_number': '123457'}
        url = detail_url(policy.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        policy.refresh_from_db()
        self.assertEqual(policy.policy_number, payload['policy_number'])
        self.assertEqual(policy.link, original_link)
        self.assertEqual(policy.user, self.user)

    def test_full_update(self):
        """
        Test full update of policy.
        """
        policy = create_policy(
            user=self.user,
            policy_number='123456',
            policy_type='Home',
            link="https://example.com/policy.pdf",
        )

        payload = {
            'policy_number': '123456',
            'policy_type': 'Home',
            'start_date': '2021-01-01',
            'end_date': '2022-01-01',
            'premium': Decimal('100.00'),
            'link': 'https://example.com/policy.pdf',
        }
        url = detail_url(policy.id)
        res = self. client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        policy.refresh_from_db()
        for k, v in payload.items():
            if k in ['start_date', 'end_date']:
                v = datetime.strptime(v, '%Y-%m-%d').date()
            self.assertEqual(getattr(policy, k), v)
        self.assertEqual(policy.user, self.user)

    def test_update_user_returns_error(self):
        """
        Test changing the policy user results in error
        """
        new_user = create_user(email='user2@example.com', password='test123')
        policy = create_policy(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(policy.id)
        self.client.patch(url, payload)

        policy.refresh_from_db()
        self.assertEqual(policy.user, self.user)

    def test_delete_policy(self):
        """
        Test deleting a policy succsessful.
        """
        policy = create_policy(user=self.user)

        url = detail_url(policy.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Policy.objects.filter(id=policy.id).exists())

    def test_delete_other_users_policy_error(self):
        """
        Test trying to delete another usre policy gives error.
        """
        new_user = create_user(email='user2@example.com', password='test123')
        policy = create_policy(user=new_user)

        url = detail_url(policy.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Policy.objects.filter(id=policy.id).exists())


class ImageUploadTests(TestCase):
    """
    Tests for the image upload API.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password123',
        )
        self.client.force_authenticate(self.user)
        self.policy = create_policy(user=self.user)

    def tearDown(self):
        self.policy.image.delete()

    def test_upload_image(self):
        """
        Test uploading an image to a policy
        """
        url = image_upload_url(self.policy.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.policy.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.policy.image.path))

    def test_upload_image_bad_request(self):
        """
        Test uploading invalid image
        """
        url = image_upload_url(self.policy.id)
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
