from djoser.email import ActivationEmail, PasswordResetEmail
from .tasks import send_djoser_email 


class CustomActivationEmail(ActivationEmail):
    """
    Класс для формирования письма активации.
    """
    def send(self, to, *args, **kwargs):
        # Получаем полный контекст от Djoser
        context = self.get_context_data()      

        user = context.get("user")
        user_id = user.pk
        domain = context.get("domain")
        site_name = context.get("site_name")
        uid = context.get("uid")
        token = context.get("token")
        
        # Передаем в задачу только ID пользователя и другие строки
        send_djoser_email.delay(
            template_name=self.template_name,
            user_id=user_id,
            domain=domain,
            site_name=site_name,
            uid=uid,
            token=token,
            to_email=to,
            subject='Активация аккаунта'
        )


class CustomPasswordResetEmail(PasswordResetEmail):
    """
    Класс для сброса пароля
    """
    def send(self, to, *args, **kwargs):
        context = self.get_context_data()
        
        user = context.get("user")
        user_id = user.pk
        domain = context.get("domain")
        site_name = context.get("site_name")
        uid = context.get("uid")
        token = context.get("token")
        
        send_djoser_email.delay(
            template_name=self.template_name,
            user_id=user_id,
            domain=domain,
            site_name=site_name,
            uid=uid,
            token=token,
            to_email=to,
            subject='Сброс пароля'
        )