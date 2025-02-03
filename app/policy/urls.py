"""
URLs for the policy app
"""

from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from policy import views

router = DefaultRouter()
router.register('policy', views.PolicyViewSet)

app_name = 'policy'

urlpatterns = [
    path('', include(router.urls)),
]
