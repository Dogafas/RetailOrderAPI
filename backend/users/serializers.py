# backend\users\serializers.py
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from .models import Client, Supplier, User


class CustomUserCreateSerializer(UserCreateSerializer):
    """
    Кастомный сериализатор для создания пользователя.
    Добавляет поле user_type и логику создания профиля.
    """

    # Добавляем явное определение поля, чтобы можно было добавить валидацию
    user_type = serializers.ChoiceField(
        choices=User.UserType.choices,
        write_only=True,  # Поле нужно только для создания, не для отображения
        required=True,
    )
    # Поле для названия компании поставщика, необязательное при регистрации
    company_name = serializers.CharField(
        max_length=100, required=False, write_only=True  # Делаем поле необязательным
    )

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "user_type",
            "company_name",
        )

    def validate(self, data):
        """
        Проверяем, что для поставщика указано название компании,
        и убираем кастомные поля перед передачей в родительский валидатор.
        """

        if data.get("user_type") == User.UserType.SUPPLIER and not data.get(
            "company_name"
        ):
            raise serializers.ValidationError(
                "Для типа пользователя 'Поставщик' необходимо указать 'company_name'."
            )

        self.context["user_type"] = data.pop("user_type")
        self.context["company_name"] = data.pop("company_name", None)

        validated_data = super().validate(data)

        return validated_data

    def create(self, validated_data):
        """
        Переопределяем метод для создания пользователя и связанного профиля.
        Данные для профиля берутся из self.context, куда мы их положили на этапе валидации.
        """

        user_type = self.context.get("user_type")
        company_name = self.context.get("company_name")

        # Создаем пользователя с помощью родительского метода Djoser
        user = super().create(validated_data)
        user.user_type = user_type
        user.save()

        # Создаем связанный профиль в зависимости от user_type
        if user_type == User.UserType.CLIENT:
            Client.objects.create(user=user)
        elif user_type == User.UserType.SUPPLIER:
            Supplier.objects.create(user=user, name=company_name)

        return user


class CustomUserSerializer(UserSerializer):
    """
    Кастомный сериализатор для просмотра данных пользователя.
    Отображает информацию о текущем пользователе (/users/me/).
    """

    class Meta(UserSerializer.Meta):
        model = User
        # Добавляем user_type, чтобы пользователь видел свой тип
        fields = ("id", "email", "first_name", "last_name", "user_type")
