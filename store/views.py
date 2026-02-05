from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from .models import *
from store.serializers import *
from rest_framework.decorators import api_view
from django.db.models import Max
from rest_framework.permissions import *
from rest_framework.viewsets import ModelViewSet
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ProductFilter
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, GenericAPIView
from contextlib import nullcontext
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView

# region Sara
class ProductView(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter

    def get_permissions(self):
        self.permission_classes = [AllowAny]

        if self.request.method in ['POST', 'DELETE', 'PUT', 'PATCH']:
            self.permission_classes = [IsAdminUser]

        return super().get_permissions()

    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter

@api_view(['GET'])
def product_info(request):
    products = Product.objects.all()
    serializer = ProductInfoSerializer({
        'products':products,
        'count':len(products),
        'max_price' :products.aggregate(max_price=Max('price'))['max_price']
    })
    return Response(serializer.data)

class ProductImageViewSet(ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer

    def perform_create(self, serializer):
        """
        اگر عکسی main شد،
        بقیه عکس‌های main همون محصول false بشن
        """
        product = serializer.validated_data['product']
        is_main = serializer.validated_data.get('is_main', False)

        if is_main:
            ProductImage.objects.filter(
                product=product,
                is_main=True
            ).update(is_main=False)

        serializer.save()

class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

#endregion

# region Kooshan
class CustomLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 120
    limit_query_param = 'size'
    offset_query_param = 'page'
    default_offset = 0


class AddressGenericApiView(ListCreateAPIView):
    queryset =  Address.objects.all()
    serializer_class = AddressSerializer
    pagination_class = CustomLimitOffsetPagination
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
class AddressGenericDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    pagination_class = CustomLimitOffsetPagination()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class OrdersGenericApiView(GenericAPIView):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        orders = self.get_queryset()
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        items_data = request.data.pop("items", [])
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request, "items_data": items_data}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)



from rest_framework import status

class OrdersGenericDetailView(GenericAPIView):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        orders = self.get_queryset()
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        items_data = request.data.get("items", [])
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request, "items_data": items_data}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)




class OrderItemsGenericApiView(ListCreateAPIView):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    pagination_class = CustomLimitOffsetPagination
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

class OrderItemsGenericDetailView(RetrieveUpdateDestroyAPIView):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    pagination_class = CustomLimitOffsetPagination
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class LogoutView(GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"detail": "User logged out"})
    

class ChangePasswordView(GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raiseExceptions=True)
        serializer.save()
        return Response({"detail": "Password changed successfully!"})


class PasswordResetRequestView(GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data,
            context={
                "send_reset": nullcontext  # serializers send email TODO
            }
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Check your email, recovery email has been sent"})

class PasswordResetConfirmView(GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer


    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password reset successful"})

#endregion
    
# region Mostafa

class IsOwnerMixin:
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        try:
            cart = Cart.objects.get(user=user)
            return cart.items.all()
        except Cart.DoesNotExist:
            return CartItem.objects.none()

    def perform_create(self, serializer):
        cart = Cart.objects.get_or_create(user=self.request.user)[0]
        if cart.is_locked:
            raise serializers.ValidationError("The cart is locked and cannot be modified.")
        serializer.save(cart=cart)

    def perform_update(self, serializer):
        if serializer.instance.cart.is_locked:
            raise serializers.ValidationError("The cart is locked and cannot be modified.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.cart.is_locked:
            raise serializers.ValidationError("The cart is locked and cannot be modified.")
        instance.delete()

class LockCartForPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart = request.user.cart

        if cart.is_locked:
            return Response(
                {"detail": "The cart is locked and cannot be modified."},
                status=400
              )

        cart.is_locked = True
        cart.save()

        return Response({"detail": "Cart locked for payment."})
#endregion    