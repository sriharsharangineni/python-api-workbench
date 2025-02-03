"""
Serializers for the policy APIs
"""

from rest_framework import serializers
from core.models import Policy


class PolicySerializer(serializers.ModelSerializer):
    """
    Serializer for policy objects
    """

    class Meta:
        model = Policy
        fields = [
            'id', 'policy_number',
            'premium',
            'start_date', 'end_date',
            'link',
        ]
        read_only_fields = ['id']


class PolicyDetailSerializer(PolicySerializer):
    """
    Serialize a policy detail
    """

    class Meta(PolicySerializer.Meta):
        fields = PolicySerializer.Meta.fields + ['policy_type', 'image']


class PolicyImageSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading image to policy
    """

    class Meta:
        model = Policy
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}
