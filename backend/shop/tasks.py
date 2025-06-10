import yaml
from celery import shared_task
from django.db import transaction

from users.models import User
from .models import Category, Product, ProductInfo, Parameter, ProductParameter


@shared_task
def process_pricelist_upload(data, user_id):
    """
    Асинхронная задача для обработки загруженного прайс-листа.
    
    Args:
        data (str): Содержимое YAML-файла в виде строки.
        user_id (int): ID пользователя (поставщика), загрузившего файл.
    """
    try:
        user = User.objects.get(id=user_id)
        supplier = user.supplier_profile
        
        # Загружаем данные из YAML
        content = yaml.safe_load(data)
        
        # Используем транзакцию, чтобы гарантировать целостность данных.
        # Если на любом этапе произойдет ошибка, все изменения откатятся.
        with transaction.atomic():
            # 1. Обновляем или создаем категории
            for category_data in content.get('categories', []):
                Category.objects.update_or_create(
                    id=category_data['id'],
                    defaults={'name': category_data['name']}
                )
            
            # 2. Очищаем старые товары этого поставщика
            # Это гарантирует, что товары, которых нет в новом файле, будут удалены.
            ProductInfo.objects.filter(supplier=supplier).delete()

            # 3. Обновляем или создаем товары
            for item_data in content.get('goods', []):
                # Создаем или находим категорию
                category, _ = Category.objects.get_or_create(
                    id=item_data['category']
                )

                # Создаем или находим основной товар (не привязан к поставщику)
                product, _ = Product.objects.update_or_create(
                    name=item_data['name'],
                    defaults={'category': category}
                )

                # Создаем информацию о товаре для конкретного поставщика
                product_info = ProductInfo.objects.create(
                    product=product,
                    supplier=supplier,
                    price=item_data['price'],
                    quantity=item_data['quantity']
                )

                # 4. Обновляем или создаем параметры для товара
                for param_name, param_value in item_data.get('parameters', {}).items():
                    # Создаем или находим параметр
                    parameter, _ = Parameter.objects.get_or_create(
                        name=param_name
                    )
                    
                    # Создаем значение параметра для товара
                    ProductParameter.objects.create(
                        product_info=product_info,
                        parameter=parameter,
                        value=param_value
                    )
            
            # Обновляем название магазина (поставщика)
            supplier.name = content.get('shop', supplier.name)
            supplier.save()

        return f"Прайс-лист для {supplier.name} успешно обработан."
    
    except yaml.YAMLError as e:
        # Логируем ошибку парсинга YAML
        print(f"Ошибка парсинга YAML для пользователя {user_id}: {e}")
        return f"Ошибка: неверный формат YAML файла."
    except Exception as e:
        # Логируем другие возможные ошибки
        print(f"Непредвиденная ошибка при обработке прайс-листа для {user_id}: {e}")
        return f"Ошибка: не удалось обработать файл."