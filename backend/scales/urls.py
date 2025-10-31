from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FactionViewSet, AgentViewSet

router = DefaultRouter()
router.register(r'factions', FactionViewSet, basename='faction')
router.register(r'agents', AgentViewSet, basename='scales-agent')

urlpatterns = [
    path('', include(router.urls)),
    # Top-level alias for network map (detail=False action on FactionViewSet)
    path('network/', FactionViewSet.as_view({'get': 'network'}), name='scales-network'),
]
