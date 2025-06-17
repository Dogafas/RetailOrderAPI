from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SupplierStatusView,
    PriceListUploadView,
    ProductViewSet,
    CartViewSet,
    ContactViewSet, 
    OrderCreateView,
    ProductExportView,
    TaskStatusView,
    OrderViewSet
    )

app_name = 'shop'

# Создаем роутер
router = DefaultRouter()

router.register(r'products', ProductViewSet, basename='products')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'contacts', ContactViewSet, basename='contacts') 
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    # URL для управления статусом поставщика
    path('supplier/status/', SupplierStatusView.as_view(), name='supplier-status'),
    # URL для загрузки прайс-листа
    path('supplier/pricelist/', PriceListUploadView.as_view(), name='supplier-pricelist-upload'),
    # URL для создания заказа
    path('order/', OrderCreateView.as_view(), name='order-create'),
    # URL для запуска экспорта
    path('products/export/', ProductExportView.as_view(), name='product-export'),
    # URL для проверки статуса и получения результата задачи
    path('tasks/<str:task_id>/', TaskStatusView.as_view(), name='task-status'),

    # Подключаем URL, сгенерированные роутером
    path('', include(router.urls)),
]


