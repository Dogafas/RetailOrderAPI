from celery import shared_task
from templated_mail.mail import BaseEmailMessage
from django.contrib.auth import get_user_model
from django.conf import settings

# Получаем модель User
User = get_user_model()

@shared_task
def send_djoser_email(template_name, user_id, domain, site_name, uid, token, to_email, subject):
    """
    Асинхронная задача для отправки email от Djoser.
    """
    try:
        # Находим пользователя по ID
        user = User.objects.get(pk=user_id)
        
        # Воссоздаем контекст для шаблона письма
        context = {
            "user": user,
            "domain": domain,
            "site_name": site_name,
            "uid": uid,
            "token": token,
            "protocol": "https" if "https" in domain else "http"
        }
        
        context["url"] = settings.DJOSER['ACTIVATION_URL'].format(**context)
        
        # Отправляем письмо
        email = BaseEmailMessage(template_name=template_name, context=context)
        email.send(to=to_email)
        
        return f"Письмо '{subject}' успешно отправлено на {to_email[0]}."
    except User.DoesNotExist:
        return f"Ошибка: пользователь с ID {user_id} не найден."
    except Exception as e:
        return f"Ошибка при отправке письма '{subject}' на {to_email[0]}: {e}"