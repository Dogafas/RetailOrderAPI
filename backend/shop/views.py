from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.parsers import MultiPartParser

from .serializers import SupplierStatusSerializer
from .tasks import process_pricelist_upload
from users.models import Supplier


class SupplierStatusView(RetrieveUpdateAPIView):
    """
    View для управления статусом поставщика (принимает ли он заказы).
    Доступно только для аутентифицированных поставщиков.
    """
    serializer_class = SupplierStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Возвращает профиль поставщика для текущего аутентифицированного пользователя.
        """
        # Проверяем, является ли пользователь поставщиком
        if self.request.user.user_type != 'supplier':
            return None
        
        # Получаем или создаем профиль поставщика
        supplier, _ = Supplier.objects.get_or_create(user=self.request.user)
        return supplier


class PriceListUploadView(APIView):
    """
    View для загрузки прайс-листа поставщиком.
    Принимает POST-запрос с файлом.
    """
    permission_classes = [IsAuthenticated]
    # Указываем, что будем работать с файлами
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        """
        Обрабатывает загрузку файла и запускает асинхронную задачу.
        """
        # Проверяем, является ли пользователь поставщиком
        if request.user.user_type != 'supplier':
            return Response(
                {'error': 'Только поставщики могут загружать прайс-листы.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Проверяем, был ли файл отправлен
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {'error': 'Файл не был предоставлен.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Читаем содержимое файла
        data = file_obj.read().decode('utf-8')
        
        # Запускаем асинхронную задачу Celery
        process_pricelist_upload.delay(data, request.user.id)
        
        # Возвращаем ответ, что задача принята в обработку
        return Response(
            {'message': 'Ваш прайс-лист был принят в обработку.'},
            status=status.HTTP_202_ACCEPTED
        )