# backend\config\settings.py

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Берем ключ из переменных окружения
SECRET_KEY = os.getenv("SECRET_KEY", "default-insecure-key-for-local-dev")

# Режим DEBUG управляется через переменные окружения
# `os.getenv('DEBUG', '0') == '1'` вернет True, если DEBUG=1, иначе False
DEBUG = os.getenv("DEBUG", "0") == "1"

# Список хостов берется из переменных окружения
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "djoser",
    "django_filters",
    'drf_spectacular',
    "users.apps.UsersConfig",
    "shop.apps.ShopConfig",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST"),
        "PORT": os.getenv("POSTGRES_PORT"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CELERY SETTINGS
CELERY_BROKER_URL = (
    f"amqp://{os.getenv('RABBITMQ_DEFAULT_USER')}:"
    f"{os.getenv('RABBITMQ_DEFAULT_PASS')}@rabbitmq:5672/"
)
CELERY_RESULT_BACKEND = f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/0"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Moscow"
CELERY_ENABLE_UTC = True


# AUTHENTICATION
AUTH_USER_MODEL = "users.User"

# DJANGO REST FRAMEWORK SETTINGS
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # использовать django-filter по умолчанию
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],

    # пагинация по умолчанию для всех ViewSet
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,  # Количество элементов на странице

    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}


# DJOSER SETTINGS
DJOSER = {
    "PASSWORD_RESET_CONFIRM_URL": "auth/password/reset/confirm/{uid}/{token}",
    "ACTIVATION_URL": "auth/activate/{uid}/{token}",
    "LOGIN_FIELD": "email",
    "SERIALIZERS": {
        "user_create": "users.serializers.CustomUserCreateSerializer",
        "current_user": "users.serializers.CustomUserSerializer",
    },
}




# EMAIL SETTINGS
if DEBUG:
    # В режиме разработки выводим письма в консоль, где запущен Django
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # В продакшене используется реальный SMTP-сервер
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'

# Email администратора, берется из .env
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'default-admin@example.com')


# DRF-SPECTACULAR SETTINGS (API DOCS)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Retail Order API',
    'DESCRIPTION': 'API для сервиса заказа товаров для розничных сетей.',
    'VERSION': '1.0.0',
    # Не встраивать схему в саму страницу, а обслуживать ее отдельно
    'SERVE_INCLUDE_SCHEMA': False,
}


# SIMPLE JWT SETTINGS

from datetime import timedelta

SIMPLE_JWT = {
    # Время жизни access-токена (короткое)
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    # Время жизни refresh-токена (длинное)
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    
    # Разрешает обновлять refresh-токены
    'ROTATE_REFRESH_TOKENS': True,
    # Если True, то после обновления refresh-токена старый будет добавлен в черный список
    'BLACKLIST_AFTER_ROTATION': True,

    # Алгоритм подписи
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY, # Используем секретный ключ Django

    # Тип токена в заголовке Authorization
    'AUTH_HEADER_TYPES': ('Bearer',), # Стандарт для JWT - 'Bearer'
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    
    # Поле в модели пользователя, которое будет использоваться как идентификатор
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    # Класс для аутентификации пользователя
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    # Тип токена
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}