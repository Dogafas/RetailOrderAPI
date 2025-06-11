from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupplierStatusView, PriceListUploadView, ProductViewSet

app_name = 'shop'

# Создаем роутер
router = DefaultRouter()

router.register(r'products', ProductViewSet, basename='products')

urlpatterns = [
    # URL для управления статусом поставщика
    path('supplier/status/', SupplierStatusView.as_view(), name='supplier-status'),
    # URL для загрузки прайс-листа
    path('supplier/pricelist/', PriceListUploadView.as_view(), name='supplier-pricelist-upload'),

    # Подключаем URL, сгенерированные роутером
    path('', include(router.urls)),
]
