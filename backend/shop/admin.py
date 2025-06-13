from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Order, OrderItem


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    Админка для позиций в заказе.
    Обычно не используется напрямую, а как часть OrderAdmin.
    """
    list_display = ('order', 'product_info', 'quantity')


class OrderItemInline(admin.TabularInline):
    """
    Встраиваемая модель для отображения позиций заказа
    на странице самого заказа.
    """
    model = OrderItem
    # `raw_id_fields` удобен для полей ForeignKey с большим количеством вариантов
    raw_id_fields = ['product_info']
    # `extra = 0` убирает пустые слоты для добавления новых позиций
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Админка для заказов.
    """
    # Поля, которые будут отображаться в списке заказов
    list_display = (
        'id', 'client_link', 'contact', 'created_at', 'status'
    )
    # Поля, по которым можно будет кликнуть для перехода к редактированию
    list_display_links = ('id',)
    
    # Фильтрация по статусу и дате создания
    list_filter = ('status', 'created_at')
    
    # Поиск по имени клиента и email
    search_fields = ('client__user__first_name', 'client__user__last_name', 'client__user__email')
    
    # Включаем inline-модель с позициями заказа
    inlines = [OrderItemInline]

    # Добавляем кастомное действие для смены статуса
    actions = ['set_status_processing', 'set_status_shipped', 'set_status_delivered']

    def client_link(self, obj):
        """
        Создает кликабельную ссылку на профиль клиента в админке.
        """
        # Получаем URL для страницы редактирования пользователя
        url = reverse("admin:users_user_change", args=[obj.client.user.id])
        # Формируем HTML-ссылку
        return format_html('<a href="{}">{}</a>', url, obj.client.user.get_full_name())
    
    # Задаем короткое описание для нашего кастомного поля
    client_link.short_description = 'Клиент'

    @admin.action(description='Изменить статус на "В обработке"')
    def set_status_processing(self, request, queryset):
        queryset.update(status='processing')

    @admin.action(description='Изменить статус на "Отправлен"')
    def set_status_shipped(self, request, queryset):
        queryset.update(status='shipped')

    @admin.action(description='Изменить статус на "Доставлен"')
    def set_status_delivered(self, request, queryset):
        queryset.update(status='delivered')