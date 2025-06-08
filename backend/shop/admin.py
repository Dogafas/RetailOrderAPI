from django.contrib import admin

from .models import (
    Cart,
    CartItem,
    Category,
    Order,
    OrderItem,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
    )
    search_fields = ("name",)


class ProductParameterInline(admin.TabularInline):
    """Инлайн для параметров товара на странице ProductInfo."""

    model = ProductParameter
    extra = 1  # Количество пустых форм для добавления


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "supplier",
        "price",
        "quantity",
    )
    list_filter = ("supplier",)
    search_fields = ("product__name",)
    inlines = (ProductParameterInline,)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "category",
    )
    list_filter = ("category",)
    search_fields = ("name",)


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
    )
    search_fields = ("name",)


class OrderItemInline(admin.TabularInline):
    """Инлайн для позиций заказа на странице Order."""

    model = OrderItem
    raw_id_fields = ("product_info",)  # Виджет для выбора ForeignKey
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "client",
        "contact",
        "status",
        "created_at",
    )
    list_filter = (
        "status",
        "created_at",
    )
    search_fields = ("client__user__email", "contact__last_name", "id")
    inlines = (OrderItemInline,)


class CartItemInline(admin.TabularInline):
    """Инлайн для позиций корзины на странице Cart."""

    model = CartItem
    raw_id_fields = ("product_info",)
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "client",
    )
    inlines = (CartItemInline,)
