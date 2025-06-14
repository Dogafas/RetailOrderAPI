from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Order
from .tasks import send_status_change_email


@receiver(pre_save, sender=Order)
def cache_old_order_status(sender, instance, **kwargs):
    """
    Перед сохранением запоминаем старый статус заказа, если он уже существует.
    """
    if instance.pk:
        try:
            # Сохраняем старый статус в атрибуте объекта, который не хранится в БД
            instance._old_status = Order.objects.get(pk=instance.pk).status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Order)
def order_status_changed(sender, instance, created, **kwargs):
    """
    После сохранения проверяем, изменился ли статус, и отправляем уведомление.
    """
    # Не отправляем письмо при создании заказа
    if not created and hasattr(instance, '_old_status') and instance._old_status is not None:
        # Сравниваем старый статус (из кэша) с новым
        if instance._old_status != instance.status:
            # Если статус изменился, запускаем асинхронную задачу
            send_status_change_email.delay(
                instance.id,
                instance.client.user.email,
                instance.status
            )