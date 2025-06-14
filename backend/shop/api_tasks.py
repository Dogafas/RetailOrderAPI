import json
from celery import shared_task
from .models import Product
from .serializers import ProductSerializer

@shared_task
def export_products_to_json():
    """
    Асинхронная задача для экспорта всех товаров в JSON.
    """
    try:
        products = Product.objects.all().prefetch_related(
            'product_infos__supplier', 
            'product_infos__parameters__parameter'
        )
        serializer = ProductSerializer(products, many=True)
        json_data = json.dumps(serializer.data, indent=4, ensure_ascii=False)
        return json_data
    except Exception as e:
        print(f"Ошибка при экспорте товаров в JSON: {e}")
        return json.dumps(
            {'error': 'Не удалось выполнить экспорт товаров.', 'details': str(e)}
        )