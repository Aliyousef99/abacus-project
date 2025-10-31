from django.urls import path
from .views import administration_panel

urlpatterns = [
    path('panel/', administration_panel, name='administration-panel'),
]
