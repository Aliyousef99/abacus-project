from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FactionViewSet, FactionLeverageView

router = DefaultRouter()
router.register(r'factions', FactionViewSet, basename='faction')

urlpatterns = [
    path('', include(router.urls)),
    path('factions/<int:id>/leverage/', FactionLeverageView.as_view(), name='faction-leverage'),
]