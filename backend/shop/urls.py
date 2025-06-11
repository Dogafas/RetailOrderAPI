from django.urls import path
from .views import SupplierStatusView, PriceListUploadView

app_name = 'shop'

urlpatterns = [
    # URL для управления статусом поставщика
    path('supplier/status/', SupplierStatusView.as_view(), name='supplier-status'),
    # URL для загрузки прайс-листа
    path('supplier/pricelist/', PriceListUploadView.as_view(), name='supplier-pricelist-upload'),
]
