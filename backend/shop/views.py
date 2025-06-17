from celery.result import AsyncResult
from django.http import JsonResponse, HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from users.models import Supplier
from .filters import ProductFilter
from .models import Cart, CartItem, Contact, Order, Product
from .permissions import IsAdminOrSupplier, IsClient, IsSupplier
from .serializers import (
    CartItemWriteSerializer,
    CartSerializer,
    ContactSerializer,
    OrderSerializer,
    ProductSerializer,
    SupplierStatusSerializer,
)



class SupplierStatusView(RetrieveUpdateAPIView):
    """
    Получение и изменение статуса поставщика.
    
    Позволяет поставщику управлять своей готовностью принимать заказы.
    - GET: получить текущий статус.
    - PATCH/PUT: изменить статус.
    """
    serializer_class = SupplierStatusSerializer
    permission_classes = [IsSupplier]

    def get_object(self):
        """
        Возвращает профиль поставщика для текущего пользователя.
        """
        supplier, _ = Supplier.objects.get_or_create(user=self.request.user)
        return supplier


class PriceListUploadView(APIView):
    """
    Загрузка прайс-листа поставщика.
    
    Принимает POST-запрос с файлом в формате YAML.
    Ключ для файла в form-data должен быть `file`.
    """
    permission_classes = [IsSupplier]
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        from .tasks import process_pricelist_upload

        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {'error': 'Файл не был предоставлен.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = file_obj.read().decode('utf-8')

        process_pricelist_upload.delay(data, request.user.id)

        return Response(
            {'message': 'Ваш прайс-лист был принят в обработку.'},
            status=status.HTTP_202_ACCEPTED,
        )

class ProductViewSet(ReadOnlyModelViewSet):
    """
    Просмотр каталога товаров.
    
    Предоставляет доступ к списку товаров с фильтрацией и поиском.
    Доступно всем пользователям, включая неавторизованных.
    """
    queryset = Product.objects.all().prefetch_related(
        'product_infos__supplier', 'product_infos__parameters__parameter'
    )
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['name']


class CartViewSet(ModelViewSet):
    """
    Управление корзиной клиента.
    
    Позволяет добавлять, просматривать, изменять и удалять товары в корзине.
    Доступно только для аутентифицированных клиентов.
    - GET (/api/v1/cart/): просмотр корзины.
    - POST (/api/v1/cart/): добавление товара (требует product_info и quantity).
    - PATCH (/api/v1/cart/{item_id}/): изменение количества товара.
    - DELETE (/api/v1/cart/{item_id}/): удаление товара из корзины.
    """
    permission_classes = [IsAuthenticated, IsClient]

    def get_queryset(self):
        if self.action in ['list', 'retrieve', 'create']:
            return Cart.objects.filter(
                client__user=self.request.user
            ).prefetch_related('items__product_info__product')
        return CartItem.objects.filter(cart__client__user=self.request.user)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CartItemWriteSerializer
        return CartSerializer

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(
            client=self.request.user.client_profile
        )
        product_info = serializer.validated_data['product_info']
        quantity = serializer.validated_data['quantity']
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_info=product_info,
            defaults={'quantity': quantity},
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
            serializer.instance = cart_item

    def list(self, request, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(
            client=self.request.user.client_profile
        )
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    

class OrderCreateView(CreateAPIView):
    """
    Оформление заказа.
    
    Создает новый заказ на основе текущего содержимого корзины клиента.
    Требует указания ID контакта для доставки.
    После успешного создания корзина очищается.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsClient] # Только для клиентов 


class ContactViewSet(ModelViewSet):
    """
    Управление контактными данными (адресами) клиента.
    
    Позволяет клиенту создавать, просматривать, изменять и удалять свои
    контактные данные для последующего использования в заказах.
    """
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated, IsClient]

    def get_queryset(self):
        """Возвращает только контакты текущего пользователя."""
        return Contact.objects.filter(client__user=self.request.user)

    def perform_create(self, serializer):
        """Автоматически привязывает контакт к профилю клиента."""
        serializer.save(client=self.request.user.client_profile)    


class ProductExportView(APIView):
    """
    Запускает асинхронную задачу по экспорту товаров в JSON.
    """
    # Допустим, экспорт доступен только администраторам или поставщикам.

    permission_classes = [IsAdminOrSupplier] 

    def get(self, request, *args, **kwargs):
        """
        Запускает задачу и возвращает ее ID.
        """
        from .api_tasks import export_products_to_json

        task = export_products_to_json.delay()
        return Response(
            {'task_id': task.id},
            status=status.HTTP_202_ACCEPTED
        )


class TaskStatusView(APIView):
    """
    Проверяет статус асинхронной задачи и возвращает результат.
    """
    permission_classes = [IsAdminOrSupplier]

    def get(self, request, task_id, *args, **kwargs):
        """
        Возвращает статус задачи и ее результат (если готов).
        """
        # Получаем объект задачи по ее ID
        task_result = AsyncResult(task_id)
        
        response_data = {
            'task_id': task_id,
            'status': task_result.status,
            'result': None
        }

        if task_result.successful():
            # Если задача успешно выполнена, возвращаем результат как JSON-файл
            json_data = task_result.get()
            # Создаем HTTP-ответ с JSON-данными и нужными заголовками
            response = HttpResponse(
                json_data, 
                content_type='application/json; charset=utf-8'
            )
            response['Content-Disposition'] = 'attachment; filename="products.json"'
            return response
        elif task_result.failed():
            # Если задача провалилась, возвращаем информацию об ошибке
            response_data['result'] = str(task_result.info) # .info содержит traceback
            return JsonResponse(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Если задача еще выполняется, просто возвращаем ее статус
            return JsonResponse(response_data, status=status.HTTP_200_OK)
        

class OrderViewSet(ReadOnlyModelViewSet):
    """
    ViewSet для просмотра заказов клиента.
    
    Позволяет клиенту просматривать список своих заказов и детали
    каждого конкретного заказа.
    - GET /api/v1/orders/ - список заказов.
    - GET /api/v1/orders/{id}/ - детали заказа.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsClient] # Только для клиентов

    def get_queryset(self):
        """
        Возвращает только заказы текущего пользователя.
        Используем prefetch_related для оптимизации запросов к позициям заказа.
        """
        return Order.objects.filter(
            client__user=self.request.user
        ).prefetch_related(
            'items',
            'items__product_info__product'
        )
