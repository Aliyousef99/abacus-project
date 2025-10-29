from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

# Register the UserViewSet at the root so that:
# - GET /api/users/ returns user profiles (Protector only)
# - POST /api/users/grant-mantle/ grants mantle (Protector only)
# - GET /api/users/mantle-status/ returns mantle status (any authenticated)
router = DefaultRouter()
router.register(r'', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
]
