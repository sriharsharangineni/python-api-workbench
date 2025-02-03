"""
Views for the policy APIs
"""

from rest_framework import (
    viewsets,
    status,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Policy
from policy import serializers


class PolicyViewSet(viewsets.ModelViewSet):
    """
    Views for Manage policies APIs
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Policy.objects.all()
    serializer_class = serializers.PolicyDetailSerializer

    def get_queryset(self):
        """
        Return policies for the current authenticated user only
        """
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """
        Return appropriate serializer class
        """
        if self.action == 'list':
            return serializers.PolicySerializer
        elif self.action == 'upload_image':
            return serializers.PolicyImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """
        Create a new policy
        """
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """
        Upload an image to policy
        """
        policy = self.get_object()
        serializer = self.get_serializer(policy, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
