from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    GenericAPIView,
    ListAPIView
)
from user.services.exceptions import InsufficientStockError
from user.services.ordering import confirm_order
from user.services.searching import search_products
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Max
from django_filters.rest_framework import DjangoFilterBackend

from .models import *
from .serializers import *
from .filters import ProductFilter
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
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


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

