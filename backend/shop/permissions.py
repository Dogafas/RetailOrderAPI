from rest_framework.permissions import BasePermission

class IsClient(BasePermission):
    """
    Права доступа, которые разрешают доступ только пользователям
    с типом 'client'.
    """
    message = 'Только клиенты могут выполнять это действие.'

    def has_permission(self, request, view):
        # Проверяем, что пользователь аутентифицирован
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Проверяем, что тип пользователя - 'client'
        return request.user.user_type == 'client'