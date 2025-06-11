from rest_framework import serializers
from users.models import Supplier
from .models import Product, ProductInfo, ProductParameter, Parameter, Category
from .models import Cart, CartItem, ProductInfo


class SupplierStatusSerializer(serializers.ModelSerializer):
    """
    Сериализатор для просмотра и обновления статуса поставщика.
    """
    class Meta:
        model = Supplier
        # Показываем только название и статус
        fields = ('name', 'is_active')
        # Разрешаем изменять только поле is_active
        read_only_fields = ('name',)


class ParameterSerializer(serializers.ModelSerializer):
    """Сериализатор для названий характеристик."""
    class Meta:
        model = Parameter
        fields = ('name',)


class ProductParameterSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода характеристик товара."""
    parameter = ParameterSerializer() # Вложенный сериализатор

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value')


class ProductInfoSerializer(serializers.ModelSerializer):
    """Сериализатор для информации о товаре от поставщика."""
    # Используем `source` для получения имени поставщика
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    parameters = ProductParameterSerializer(many=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'supplier_name', 'price', 'quantity', 'parameters')


class ProductSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения полного списка товаров.
    """
    # `product_infos` - это related_name из модели ProductInfo
    product_infos = ProductInfoSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'product_infos')


# CART SERIALIZERS

class CartItemWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для добавления/изменения товаров в корзине (для записи).
    """
    # product_info указывается только по ID.
    product_info = serializers.PrimaryKeyRelatedField(
        queryset=ProductInfo.objects.all()
    )

    class Meta:
        model = CartItem
        fields = ('product_info', 'quantity')


class CartItemSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения позиций в корзине (для чтения).
    """
    # Предоставляем более подробную информацию о товаре.
    # Используем `source` для получения полей из связанной модели Product.
    name = serializers.CharField(source='product_info.product.name', read_only=True)
    price = serializers.DecimalField(
        source='product_info.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    # Вычисляемое поле для общей суммы по позиции.
    total_sum = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ('id', 'name', 'price', 'quantity', 'total_sum')

    def get_total_sum(self, obj):
        """Вычисляет сумму (цена * количество)."""
        return obj.product_info.price * obj.quantity


class CartSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения корзины.
    """
    # Вкладываем сериализатор позиций, чтобы видеть их в ответе.
    items = CartItemSerializer(many=True, read_only=True)
    # Вычисляемое поле для итоговой суммы всей корзины.
    total_sum = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('id', 'items', 'total_sum')

    def get_total_sum(self, obj):
        """Вычисляет общую сумму всех позиций в корзине."""
        return sum(item.product_info.price * item.quantity for item in obj.items.all())