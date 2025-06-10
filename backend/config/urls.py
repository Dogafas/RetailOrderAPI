# backend/config/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # =========================================================================
    # API V1 URLS
    # =========================================================================
    # Эндпоинты для аутентификации и управления пользователями от Djoser.
    # djoser.urls включает: /users/, /users/me/, /users/confirm/ и т.д.
    # djoser.urls.authtoken включает: /token/login/, /token/logout/.
    # Мы размещаем их под общим префиксом /api/v1/auth/.
    path("api/v1/auth/", include("djoser.urls")),
    path("api/v1/auth/", include("djoser.urls.authtoken")),
    # Эндпоинты для магазина.
    
    path('api/v1/', include('shop.urls')),
]
