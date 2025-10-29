from django.contrib import admin
from django.urls import path, include

# Custom JWT View
from users.views import MyTokenObtainPairView

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- API URL Patterns ---

    # JWT Authentication endpoints
    path('api/auth/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # App-specific API endpoints
    path('api/lineage/', include('lineage.urls')),
    path('api/scales/', include('scales.urls')),
    path('api/codex/', include('codex.urls')),
    path('api/loom/', include('loom.urls')),
    path('api/audit/', include('audit.urls')),
    path('api/users/', include('users.urls')),
    path('administration/', include('administration.urls')),
    # path('api/bastion/', include('bastion.urls')), # Add when ready
]
