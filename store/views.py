from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    GenericAPIView,
    ListAPIView
)

from user.api.admin_models import AuditLog
from user.services.audit import log_snapshot_change
from user.services.exceptions import InsufficientStockError
from user.services.fake_gateway import FakePaymentGateway
from user.services.ordering import confirm_order, snapshot_address
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Max
from django_filters.rest_framework import DjangoFilterBackend


from store.serializers import *
from store.filters import ProductFilter
from user.services.searching import search_products


# ===================== PRODUCTS =====================

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter

    def get_permissions(self):
        if self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return [IsAdminUser()]
        return [AllowAny()]


@api_view(["GET"])
def product_info(request):
    products = Product.objects.all()
    serializer = ProductInfoSerializer({
        "products": products,
        "count": products.count(),
        "max_price": products.aggregate(max_price=Max("price"))["max_price"]
    })
    return Response(serializer.data)


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer

    def perform_create(self, serializer):
        product = serializer.validated_data["product"]
        is_main = serializer.validated_data.get("is_main", False)

        if is_main:
            ProductImage.objects.filter(product=product, is_main=True).update(is_main=False)

        serializer.save()


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# ===================== PAGINATION =====================

class CustomLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 120
    limit_query_param = "size"
    offset_query_param = "page"


# ===================== ADDRESS =====================

class AddressGenericApiView(ListCreateAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    pagination_class = CustomLimitOffsetPagination
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class AddressGenericDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


# ===================== ORDERS =====================

class OrdersGenericApiView(GenericAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = self.get_queryset()
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        items_data = request.data.pop("items", [])
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request, "items_data": items_data}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrdersGenericDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status != Order.Status.PENDING:
            return Response({"detail": "Only pending orders can be deleted"}, status=400)
        return super().delete(request, *args, **kwargs)


class OrderItemsGenericApiView(ListCreateAPIView):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class OrderItemsGenericDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = OrderItemSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OrderItem.objects.filter(order__user=self.request.user)

    def perform_update(self, serializer):
        order_item = self.get_object()
        if order_item.order.status == Order.Status.PAID:
            raise PermissionDenied("Order is locked after payment,"
                                   " and cannot be updated..!")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.order.status == Order.Status.PAID:
            raise PermissionDenied("Order is locked after payment, "
                                   "and cannot be deleted..!")
        instance.delete()

# ===================== AUTH =====================

class LogoutView(GenericAPIView):
    serializer_class = LogoutSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "User logged out"})


class ChangePasswordView(GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password changed"})


# ===================== SEARCH =====================

class ProductSearchAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response([])
        products = search_products(query)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


# ===================== PRICE HISTORY =====================

class ProductPriceHistoryView(ListAPIView):
    serializer_class = ProductPriceHistorySerializer

    def get_queryset(self):
        product_id = self.kwargs["pk"]
        qs = ProductPriceHistory.objects.filter(product_id=product_id)

        start = self.request.query_params.get("from")
        end = self.request.query_params.get("to")

        if start and end:
            qs = qs.filter(valid_from__lte=end, valid_to__gte=start)

        return qs.order_by("-valid_from")


class OrderConfirmAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            order = Order.objects.get(
                id=pk,
                user=request.user,
                status="draft"
            )

            confirm_order(order = order, user = request.user )

            return Response(
                {"detail": "Order confirmed successfully"},
                status=status.HTTP_200_OK
            )

        except Order.DoesNotExist:
            return Response(
                {"detail": "Draft order not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        except InsufficientStockError as e:
            return Response(
                {
                    "detail": "Insufficient stock..!",
                    "product_id": e.product_id,
                    "requested": e.requested,
                    "available": e.available,
                },
                status=status.HTTP_409_CONFLICT
            )

class InitiatePaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        address_id = request.data.get("address_id")
        order = Order.objects.get(id=order_id, user=request.user)

        address = Address.objects.get(
            id=address_id,
            user=request.user
        )

        snapshot_address(order, address, user=request.user)

        if order.is_paid:
            return Response({"detail": "Order already paid"}, status=400)

        gateway_data = FakePaymentGateway.initiate(order.total_amount)

        payment = Payment.objects.create(
            order=order,
            amount=order.total_amount,
            transaction_id=gateway_data["transaction_id"],
        )

        return Response({
            "payment_url": gateway_data["payment_url"],
            "transaction_id": payment.transaction_id,
        })


class VerifyPaymentAPIView(APIView):
    def post(self, request):
        transaction_id = request.data.get("transaction_id")

        payment = Payment.objects.get(transaction_id=transaction_id)

        if payment.status != Payment.Status.PENDING:
            return Response(
                {"detail": "Payment already processed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = FakePaymentGateway.verify(transaction_id)

        if result["success"]:
            before_status = payment.order.status

            payment.status = Payment.Status.PAID
            payment.save()

            payment.order.status = "paid"
            payment.order.is_paid = True
            payment.order.save()

            log_snapshot_change(
                user=request.user,
                obj=payment.order,
                before={"status": before_status},
                after={"status": payment.order.status},
                action=AuditLog.ACTION_CHOICES.STATUS_CHANGE,
            )

            return Response({"detail": "Payment successful"})
        else:
            before_status = payment.order.status

            payment.status = Payment.Status.FAILED
            payment.save()

            payment.order.status = "payment_failed"
            payment.order.save()

            log_snapshot_change(
                user=request.user,
                obj=payment.order,
                before={"status": before_status},
                after={"status": payment.order.status},
                action=AuditLog.ACTION_CHOICES.STATUS_CHANGE,
            )

            return Response({"detail": "Payment failed"})

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
        cart, _ = Cart.objects.get_or_create(user=self.request.user)

        if cart.is_locked():
            raise PermissionDenied("Cart is locked after payment,"
                                   " cannot add any item")

        serializer.save(cart=cart)

    def perform_update(self, serializer):
        cart = Cart.objects.get(user=self.request.user)

        if cart.is_locked():
            raise PermissionDenied("Cart is locked after payment,"
                                   " cannot update any item")

        serializer.save(cart=cart)

    def perform_destroy(self, instance):
        cart = Cart.objects.get(user=self.request.user)

        if cart.is_locked():
            raise PermissionDenied("Cart is locked after payment,"
                                   " cannot remove any item")

        instance.delete()

