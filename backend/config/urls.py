# backend/config/urls.py
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # API V1 URLS
    # Эндпоинты для аутентификации и управления пользователями
    path("api/v1/auth/", include("djoser.urls")),
    # Эндпоинты для магазина.
    path('api/v1/', include('shop.urls')),
 
    # JWT TOKEN URLS
    # Эндпоинт для получения пары токенов (access и refresh)
    path('api/v1/auth/jwt/create/', TokenObtainPairView.as_view(), name='jwt-create'),
    # Эндпоинт для обновления access-токена с помощью refresh-токена
    path('api/v1/auth/jwt/refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),
    # Эндпоинт для проверки валидности токена
    path('api/v1/auth/jwt/verify/', TokenVerifyView.as_view(), name='jwt-verify'),

    # API DOCS URLS
    # Эндпоинт для скачивания файла schema.yml
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Эндпоинт для Swagger UI
    path(
        'api/v1/schema/swagger-ui/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    # Эндпоинт для ReDoc
    path(
        'api/v1/schema/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc',
    ),
]
