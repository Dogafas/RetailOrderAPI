from django_filters import rest_framework as filters
from .models import Product

class ProductFilter(filters.FilterSet):
    """
    Фильтр для модели Product.
    Позволяет фильтровать товары по категории.
    """
    # Используем 'category__id' для фильтрации по ID категории
    category = filters.NumberFilter(field_name='category__id')

    class Meta:
        model = Product
        # Указываем поля, по которым можно будет фильтровать
        fields = ['category']