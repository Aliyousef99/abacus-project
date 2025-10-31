from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CodexEntryViewSet, EchoViewSet, TaskViewSet, VaultItemViewSet, PropertyDossierViewSet, VehicleViewSet, BulletinViewSet, NotificationViewSet, codex_categories, codex_set_category_cover

router = DefaultRouter()
router.register(r'entries', CodexEntryViewSet, basename='codex-entry')
router.register(r'echoes', EchoViewSet, basename='echo')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'vault/properties', PropertyDossierViewSet, basename='vault-properties')
router.register(r'vault/vehicles', VehicleViewSet, basename='vault-vehicles')
router.register(r'vault', VaultItemViewSet, basename='vault')
router.register(r'bulletins', BulletinViewSet, basename='bulletin')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('categories/', codex_categories, name='codex-categories'),
    path('categories/set-cover/', codex_set_category_cover, name='codex-set-category-cover'),
]


