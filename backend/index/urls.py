from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IndexProfileViewSet

router = DefaultRouter()
router.register(r'profiles', IndexProfileViewSet, basename='index-profile')

urlpatterns = [
    path('', include(router.urls)),
]

