from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Client, Contact, Supplier, User


# Мы хотим видеть связанные профили (клиента и поставщика) прямо в админке пользователя.
# Для этого используем StackedInline.
class ClientInline(admin.StackedInline):
    model = Client
    can_delete = False
    verbose_name_plural = "Профиль клиента"


class SupplierInline(admin.StackedInline):
    model = Supplier
    can_delete = False
    verbose_name_plural = "Профиль поставщика"


# Расширяем стандартную админку для пользователей
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Добавляем инлайны
    inlines = (ClientInline, SupplierInline)
    # Указываем, какие поля отображать в списке пользователей
    list_display = ("email", "first_name", "last_name", "user_type", "is_staff")
    # Добавляем фильтр по типу пользователя
    list_filter = ("user_type", "is_staff", "is_superuser", "is_active")


# Регистрируем модель контактов.
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("client", "last_name", "first_name", "email", "phone_number")
    search_fields = ("last_name", "first_name", "client__user__email")
