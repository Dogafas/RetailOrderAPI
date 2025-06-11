from rest_framework import serializers
from users.models import Supplier
from .models import Product, ProductInfo, ProductParameter, Parameter, Category


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
