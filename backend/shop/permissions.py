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

class IsSupplier(BasePermission):
    """
    Разрешает доступ только пользователям с типом 'supplier'.
    """
    def has_permission(self, request, view):
        # Проверяем, что пользователь аутентифицирован и является поставщиком
        return request.user.is_authenticated and request.user.user_type == 'supplier'    
    
class IsAdminOrSupplier(BasePermission):
    """
    Разрешает доступ администраторам ИЛИ поставщикам.
    """
    def has_permission(self, request, view):
        # Проверяем, что пользователь аутентифицирован
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Разрешаем доступ, если пользователь - суперпользователь (админ)
        # ИЛИ если тип пользователя - поставщик.
        return request.user.is_superuser or request.user.user_type == 'supplier'    