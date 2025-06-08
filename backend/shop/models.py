from django.db import models

from users.models import Client, Contact, Supplier


class Category(models.Model):
    """Категории товаров."""

    name = models.CharField(max_length=50, verbose_name="Название категории")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Product(models.Model):
    """Модель товара, общая для всех поставщиков."""

    name = models.CharField(max_length=100, verbose_name="Название товара")
    category = models.ForeignKey(
        Category,
        verbose_name="Категория",
        on_delete=models.SET_NULL,
        null=True,
        related_name="products",
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    """
    Информация о товаре от конкретного поставщика.
    Содержит цену, количество и уникальные параметры.
    """

    product = models.ForeignKey(
        Product,
        verbose_name="Товар",
        on_delete=models.CASCADE,
        related_name="product_infos",
    )
    supplier = models.ForeignKey(
        Supplier,
        verbose_name="Поставщик",
        on_delete=models.CASCADE,
        related_name="product_infos",
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    quantity = models.PositiveIntegerField(verbose_name="Количество")

    class Meta:
        verbose_name = "Информация о товаре от поставщика"
        verbose_name_plural = "Информация о товарах от поставщиков"
        # Гарантируем, что для одного товара у одного поставщика есть только одна запись
        unique_together = ("product", "supplier")

    def __str__(self):
        return f"{self.product.name} от {self.supplier.name}"


class Parameter(models.Model):
    """Название характеристики (например, "Цвет", "Размер")."""

    name = models.CharField(max_length=50, verbose_name="Название параметра")

    class Meta:
        verbose_name = "Параметр"
        verbose_name_plural = "Параметры"

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    """Значение характеристики для конкретного товара от поставщика."""

    product_info = models.ForeignKey(
        ProductInfo,
        verbose_name="Информация о товаре",
        on_delete=models.CASCADE,
        related_name="parameters",
    )
    parameter = models.ForeignKey(
        Parameter,
        verbose_name="Параметр",
        on_delete=models.CASCADE,
        related_name="product_parameters",
    )
    value = models.CharField(max_length=100, verbose_name="Значение")

    class Meta:
        verbose_name = "Параметр товара"
        verbose_name_plural = "Параметры товаров"
        unique_together = ("product_info", "parameter")

    def __str__(self):
        return f"{self.parameter.name}: {self.value}"


class Order(models.Model):
    """Заказ, сделанный клиентом."""

    class OrderStatus(models.TextChoices):
        NEW = "new", "Новый"
        PROCESSING = "processing", "В обработке"
        SHIPPED = "shipped", "Отправлен"
        DELIVERED = "delivered", "Доставлен"
        CANCELED = "canceled", "Отменен"

    client = models.ForeignKey(
        Client, verbose_name="Клиент", on_delete=models.CASCADE, related_name="orders"
    )
    contact = models.ForeignKey(
        Contact,
        verbose_name="Контакт для заказа",
        on_delete=models.PROTECT,  # Защищаем контакт от удаления, если есть заказы
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    status = models.CharField(
        max_length=15,
        choices=OrderStatus.choices,
        default=OrderStatus.NEW,
        verbose_name="Статус заказа",
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ("-created_at",)

    def __str__(self):
        return f'Заказ №{self.id} от {self.created_at.strftime("%Y-%m-%d")}'


class OrderItem(models.Model):
    """Позиция в заказе."""

    order = models.ForeignKey(
        Order, verbose_name="Заказ", on_delete=models.CASCADE, related_name="items"
    )
    product_info = models.ForeignKey(
        ProductInfo,
        verbose_name="Информация о товаре",
        on_delete=models.PROTECT,  # Защищаем от удаления, чтобы сохранить историю
    )
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    # Фиксируем цену на момент заказа
    price_per_item = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Цена за единицу"
    )

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказов"
        unique_together = ("order", "product_info")


class Cart(models.Model):
    """Корзина клиента."""

    client = models.OneToOneField(
        Client, verbose_name="Клиент", on_delete=models.CASCADE, related_name="cart"
    )

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        return f"Корзина клиента {self.client.user.email}"


class CartItem(models.Model):
    """Позиция в корзине."""

    cart = models.ForeignKey(
        Cart, verbose_name="Корзина", on_delete=models.CASCADE, related_name="items"
    )
    product_info = models.ForeignKey(
        ProductInfo, verbose_name="Информация о товаре", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    class Meta:
        verbose_name = "Позиция в корзине"
        verbose_name_plural = "Позиции в корзине"
        unique_together = ("cart", "product_info")
