import os

from celery import Celery

# Устанавливаем переменную окружения, чтобы Celery знал, где находятся настройки Django.
# 'config.settings' указывает на файл backend/config/settings.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Создаем экземпляр приложения Celery.
# 'config' - это имя текущего проекта.
app = Celery("config")

# Загружаем конфигурацию для Celery из настроек Django.
# Мы будем хранить все настройки Celery в settings.py с префиксом CELERY_.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически находить и регистрировать асинхронные задачи
# из всех файлов tasks.py в установленных приложениях Django.
app.autodiscover_tasks(related_name='api_tasks')
app.autodiscover_tasks()
