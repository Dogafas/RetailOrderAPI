from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Кастомная модель пользователя.
    Аутентификация производится по email.
    """

    # Перечисляем возможные типы пользователей для поля 'type'
    class UserType(models.TextChoices):
        CLIENT = "client", "Клиент"
        SUPPLIER = "supplier", "Поставщик"
        ADMIN = "admin", "Администратор"

    email = models.EmailField(
        verbose_name="Email",
        unique=True,
        help_text="Required. Inform a valid email address.",
    )
    user_type = models.CharField(
        verbose_name="Тип пользователя",
        choices=UserType.choices,
        max_length=8,
        default=UserType.CLIENT,
    )

    # Указываем, что поле email будет использоваться для входа
    USERNAME_FIELD = "email"
    # Указываем обязательные поля при создании суперпользователя
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("email",)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Client(models.Model):
    """
    Профиль клиента, связанный с пользователем.
    """

    user = models.OneToOneField(
        User,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="client_profile",
    )

    class Meta:
        verbose_name = "Профиль клиента"
        verbose_name_plural = "Профили клиентов"

    def __str__(self):
        return f"Клиент: {self.user}"


class Supplier(models.Model):
    """
    Профиль поставщика, связанный с пользователем.
    """

    user = models.OneToOneField(
        User,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="supplier_profile",
    )
    name = models.CharField(verbose_name="Название компании", max_length=100)
    is_active = models.BooleanField(
        verbose_name="Принимает заказы",
        default=True,
        help_text="Отметьте, если поставщик готов принимать заказы.",
    )

    class Meta:
        verbose_name = "Профиль поставщика"
        verbose_name_plural = "Профили поставщиков"

    def __str__(self):
        return f"Поставщик: {self.name}"


class Contact(models.Model):
    """
    Контактная информация, связанная с клиентом.
    Один клиент может иметь несколько контактов (адресов доставки).
    """

    client = models.ForeignKey(
        Client, verbose_name="Клиент", on_delete=models.CASCADE, related_name="contacts"
    )
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    patronymic = models.CharField(max_length=50, verbose_name="Отчество", blank=True)
    email = models.EmailField(max_length=254, verbose_name="Email")
    phone_number = models.CharField(max_length=20, verbose_name="Телефон")
    address = models.CharField(max_length=255, verbose_name="Адрес")
    city = models.CharField(max_length=100, verbose_name="Город")
    street = models.CharField(max_length=100, verbose_name="Улица")
    house = models.CharField(max_length=10, verbose_name="Дом")
    building = models.CharField(max_length=10, verbose_name="Корпус", blank=True)
    structure = models.CharField(max_length=10, verbose_name="Строение", blank=True)
    apartment = models.CharField(max_length=10, verbose_name="Квартира", blank=True)

    class Meta:
        verbose_name = "Контакт"
        verbose_name_plural = "Контакты"

    def __str__(self):
        return f"{self.last_name} {self.first_name} - {self.city}, {self.address}"
