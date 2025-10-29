from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OperationViewSet, AssetViewSet, AssetRequisitionViewSet

router = DefaultRouter()
router.register(r'operations', OperationViewSet)
router.register(r'assets', AssetViewSet, basename='asset')
router.register(r'requisitions', AssetRequisitionViewSet, basename='asset-requisition')

urlpatterns = [
    path('', include(router.urls)),
]
