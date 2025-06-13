from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db import transaction
from users.models import Supplier
from .models import Product, ProductInfo, ProductParameter, Parameter, Category
from .models import Cart, CartItem, ProductInfo

from users.models import Contact
from .models import Order, OrderItem
from .tasks import send_order_confirmation_email, send_new_order_notification_to_admin

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


class OrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор для оформления и отображения заказа.
    """
    
    # Принимает ID контакта при создании заказа. Не отображается в ответе.
    contact_id = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.none(),
        write_only=True,
        source='contact'  # Указываем, что это поле работает с модельным полем 'contact'
    )
    
    
    # Отображает ID контакта в ответе. Не используется для записи.
    contact = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'contact', 'contact_id', 'created_at', 'status')
        read_only_fields = ('id', 'created_at', 'status')

    def __init__(self, *args, **kwargs):
        """
        Динамически задаем queryset для поля ЗАПИСИ.
        """
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            self.fields['contact_id'].queryset = Contact.objects.filter(
                client__user=request.user
            )

    
    def validate(self, data):
        """
        Проверяем, что корзина не пуста.
        """
        cart = self.context['request'].user.client_profile.cart
        if not cart.items.exists():
            raise serializers.ValidationError("Нельзя оформить заказ с пустой корзиной.")
        return data

    
    def create(self, validated_data):
        """
        Создаем заказ, переносим товары из корзины и запускаем задачи.
        """
        request = self.context['request']
        user = request.user
        cart = user.client_profile.cart

        with transaction.atomic():
            # Извлекаем контакт из проверенных данных
            contact = validated_data['contact']
            
            # Создаем объект Order вручную
            order = Order.objects.create(
                client=user.client_profile,
                contact=contact
            )

            # Переносим товары
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product_info=item.product_info,
                    quantity=item.quantity,
                    price_per_item=item.product_info.price
                )
            
            # Очищаем корзину
            cart.items.all().delete()

            # Запускаем асинхронные задачи
            send_order_confirmation_email.delay(order.id, user.email)
            send_new_order_notification_to_admin.delay(order.id)
            
            return order


class ContactSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Contact.
    """
    class Meta:
        model = Contact
        exclude = ('client',)
        
    
    def validate(self, data):
        """
        Проверяем на существование дубликата контакта для текущего пользователя.
        """
        # Получаем текущего пользователя из контекста
        current_user = self.context['request'].user
        
        # Собираем данные для проверки уникальности.
        # Мы будем считать контакт уникальным по совокупности всех его полей.
        # Вы можете выбрать только ключевые поля, если это требуется по бизнес-логике.
        unique_fields = {
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'patronymic': data.get('patronymic'),
            'email': data.get('email'),
            'phone_number': data.get('phone_number'),
            'address': data.get('address'),
            'city': data.get('city'),
            'street': data.get('street'),
            'house': data.get('house'),
            'building': data.get('building'),
            'structure': data.get('structure'),
            'apartment': data.get('apartment'),
        }

        # Ищем контакт с такими же полями у текущего клиента
        if Contact.objects.filter(
            client__user=current_user, **unique_fields
        ).exists():
            # Если найден - вызываем ошибку валидации
            raise serializers.ValidationError(
                "Контакт с такими данными уже существует."
            )
            
        return data


class CartItemWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для добавления/изменения товаров в корзине (для записи).
    """
    product_info = serializers.IntegerField(write_only=True, source='product_info_id')

    class Meta:
        model = CartItem
        fields = ('product_info', 'quantity')

    def validate(self, data):
        """
        Общая валидация данных.
        """
        product_info_id = data.get('product_info_id')
        
        try:
            # Пытаемся найти объект ProductInfo по ID
            product_info = ProductInfo.objects.get(id=product_info_id)
        except ProductInfo.DoesNotExist:
            # Если не найден, генерируем кастомную ошибку
            raise ValidationError({'product_info': ['Товар с указанным ID не найден.']})
        
        # Проверяем, что поставщик активен
        if not product_info.supplier.is_active:
            raise ValidationError(
                {'product_info': ['Товары от данного поставщика временно недоступны для заказа.']}
            )
                
        # Метод `create` ожидает ключ 'product_info'.
        data['product_info'] = product_info
        
        return data

