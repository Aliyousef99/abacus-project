from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CodexEntryViewSet

router = DefaultRouter()
router.register(r'entries', CodexEntryViewSet, basename='codex-entry')

urlpatterns = [
    path('', include(router.urls)),
]