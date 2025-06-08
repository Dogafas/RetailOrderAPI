from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Client, Contact, Supplier, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # ...
    list_display = ("email", "first_name", "last_name", "user_type", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Custom Fields", {"fields": ("user_type",)}),
        # Делаем username видимым, но нередактируемым
        ("Legacy Fields", {"fields": ("username",), "classes": ("collapse",)}),
    )

    # Указываем, какие поля не должны быть редактируемыми
    readonly_fields = ("username", "last_login", "date_joined")

    add_fieldsets = UserAdmin.add_fieldsets + ((None, {"fields": ("user_type",)}),)


# ... (регистрация остальных моделей)
admin.site.register(Client)
admin.site.register(Supplier)
admin.site.register(Contact)
