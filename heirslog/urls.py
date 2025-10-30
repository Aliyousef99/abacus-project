from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HeirsLogEntryViewSet

router = DefaultRouter()
# Expose list/create at /api/heirs-log/ directly
router.register(r'', HeirsLogEntryViewSet, basename='heirs-log')

urlpatterns = [
    path('', include(router.urls)),
]
