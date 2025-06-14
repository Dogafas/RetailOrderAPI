from django.apps import AppConfig


class ShopConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shop"

    def ready(self):
        """
        Этот метод вызывается, когда приложение готово.
        Импортируем сигналы здесь.
        """
        from . import signals
