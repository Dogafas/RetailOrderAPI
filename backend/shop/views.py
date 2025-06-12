from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import RetrieveUpdateAPIView, CreateAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from users.models import Supplier
from .filters import ProductFilter
from .models import Cart, CartItem, Product, Contact
from .permissions import IsClient
from .serializers import (
    SupplierStatusSerializer,
    ProductSerializer,
    CartSerializer,
    CartItemWriteSerializer,
    OrderSerializer, 
    ContactSerializer
)
from .tasks import process_pricelist_upload



class SupplierStatusView(RetrieveUpdateAPIView):
    """
    View для управления статусом поставщика (принимает ли он заказы).
    """
    serializer_class = SupplierStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        if self.request.user.user_type != 'supplier':
            return None
        supplier, _ = Supplier.objects.get_or_create(user=self.request.user)
        return supplier


class PriceListUploadView(APIView):
    """
    View для загрузки прайс-листа поставщиком.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        if request.user.user_type != 'supplier':
            return Response(
                {'error': 'Только поставщики могут загружать прайс-листы.'},
                status=status.HTTP_403_FORBIDDEN,
            )
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
    ViewSet для просмотра каталога товаров.
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
    ViewSet для управления корзиной пользователя.
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
    View для создания заказа.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsClient] # Только для клиентов 


class ContactViewSet(ModelViewSet):
    """
    ViewSet для управления контактами (адресами) клиента.
    """
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated, IsClient]

    def get_queryset(self):
        """Возвращает только контакты текущего пользователя."""
        return Contact.objects.filter(client__user=self.request.user)

    def perform_create(self, serializer):
        """Автоматически привязывает контакт к профилю клиента."""
        serializer.save(client=self.request.user.client_profile)    