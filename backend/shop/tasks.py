import yaml
from celery import shared_task
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from users.models import User
from .models import Category, Product, ProductInfo, Parameter, ProductParameter, Order
from django.core.mail import send_mail
from django.conf import settings





@shared_task(name="shop.tasks.process_pricelist_upload")
def process_pricelist_upload(data, user_id):
    """
    Асинхронная задача для обработки загруженного прайс-листа в формате YAML.

    Args:
        data (str): Содержимое YAML-файла в виде строки.
        user_id (int): ID пользователя (поставщика), загрузившего файл.
    """
    try:
        # Получаем пользователя и его профиль поставщика
        user = User.objects.get(id=user_id)
        supplier = user.supplier_profile

        # Загружаем данные из YAML. Используем safe_load для безопасности.
        content = yaml.safe_load(data)
        
        # Используем одну большую транзакцию. Если что-то пойдет не так,
        # все изменения в базе данных будут отменены.
        with transaction.atomic():
            
            # 1. Обновляем или создаем категории из файла
            for category_data in content.get('categories', []):
                Category.objects.update_or_create(
                    id=category_data['id'],
                    defaults={'name': category_data['name']}
                )
            
            # 2. Удаляем товары, которых нет в новом прайс-листе
            new_external_ids = {item['id'] for item in content.get('goods', [])}

            # Находим и удаляем те ProductInfo этого поставщика, 
            # чьи external_id отсутствуют в новом файле.
            ProductInfo.objects.filter(
                supplier=supplier
            ).exclude(
                external_id__in=new_external_ids
            ).delete()

            # 3. Обновляем или создаем товары и их параметры
            for item_data in content.get('goods', []):
                # Находим или создаем категорию для товара
                category, _ = Category.objects.get_or_create(
                    id=item_data['category']
                )

                # Находим или создаем основной (абстрактный) товар
                product, _ = Product.objects.update_or_create(
                    name=item_data['name'],
                    defaults={'category': category}
                )

                # Находим или создаем конкретное предложение от поставщика.
                product_info_obj, _ = ProductInfo.objects.update_or_create(
                    supplier=supplier,
                    external_id=item_data['id'],
                    defaults={
                        'product': product,
                        'price': item_data['price'],
                        'quantity': item_data['quantity'],                                             
                        'external_id': item_data['id']
                    }
                )

                # 4. Обновляем параметры товара
                # Сначала удаляем все старые параметры для данного товара
                product_info_obj.parameters.all().delete()
                # Затем создаем новые параметры из файла
                for param_name, param_value in item_data.get('parameters', {}).items():
                    parameter, _ = Parameter.objects.get_or_create(
                        name=param_name
                    )
                    
                    ProductParameter.objects.create(
                        product_info=product_info_obj,
                        parameter=parameter,
                        value=param_value
                    )
            
            # 5. Обновляем название магазина (поставщика) из файла
            supplier_name = content.get('shop')
            if supplier_name:
                supplier.name = supplier_name
                supplier.save()

        # Возвращаем успешный результат
        return f"Прайс-лист для '{supplier.name}' успешно обработан."
    
    except ObjectDoesNotExist:
        # Эта ошибка может возникнуть, если user_id некорректен
        print(f"Ошибка: пользователь с ID {user_id} не найден.")
        return f"Ошибка: не удалось найти пользователя."
    
    except yaml.YAMLError as e:
        # Ошибка при парсинге YAML
        print(f"Ошибка парсинга YAML для пользователя {user_id}: {e}")
        return f"Ошибка: неверный формат YAML файла."
    
    except Exception as e:
        # Ловим все остальные ошибки (например, ошибки базы данных)
        # и возвращаем общее сообщение. Детали пишем в лог.
        print(f"Непредвиденная ошибка при обработке прайс-листа для {user_id}: {e}")
        return f"Ошибка: не удалось обработать файл."
    




@shared_task
def send_order_confirmation_email(order_id, user_email):
    """
    Асинхронная задача для отправки email-подтверждения заказа клиенту.
    """
    try:
        order = Order.objects.get(id=order_id)
        subject = f'Подтверждение заказа №{order.id}'
        message = (
            f'Уважаемый клиент,\n\n'
            f'Ваш заказ №{order.id} от {order.created_at.strftime("%d.%m.%Y %H:%M")} успешно принят в обработку.\n'
            f'Вы можете отслеживать его статус в личном кабинете.'
        )
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,  # От кого
            [user_email],             # Кому
            fail_silently=False,
        )
        return f"Письмо о заказе №{order_id} успешно отправлено клиенту {user_email}."
    except Order.DoesNotExist:
        return f"Ошибка: Заказ №{order_id} не найден."
    except Exception as e:
        return f"Ошибка при отправке письма для заказа №{order_id}: {e}"


@shared_task
def send_new_order_notification_to_admin(order_id):
    """
    Асинхронная задача для отправки уведомления о новом заказе администратору.
    """
    try:
        order = Order.objects.get(id=order_id)
        subject = f'Новый заказ №{order.id}'
        
        # Собираем информацию о заказе для письма
        items_details = "\n".join(
            [f'- {item.product_info.product.name}: {item.quantity} шт. по {item.price_per_item} руб.' 
             for item in order.items.all()]
        )
        
        message = (
            f'Поступил новый заказ №{order.id}.\n\n'
            f'Клиент: {order.client.user.first_name} {order.client.user.last_name} ({order.client.user.email})\n'
            f'Контакт для доставки: {order.contact}\n\n'
            f'Состав заказа:\n{items_details}\n'
        )
        
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,       # От кого
            [settings.ADMIN_EMAIL],         # Кому (берем из настроек)
            fail_silently=False,
        )
        return f"Уведомление о заказе №{order_id} успешно отправлено администратору."
    except Order.DoesNotExist:
        return f"Ошибка: Заказ №{order_id} для уведомления не найден."
    except Exception as e:
        return f"Ошибка при отправке уведомления администратору для заказа №{order_id}: {e}"    