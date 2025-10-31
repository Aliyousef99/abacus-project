from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- API URL Patterns ---

    # JWT Authentication endpoints
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # App-specific API endpoints
    path('api/lineage/', include('lineage.urls')),
    path('api/scales/', include('scales.urls')),
    path('api/codex/', include('codex.urls')),

]
