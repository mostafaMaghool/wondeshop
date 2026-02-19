from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from .models import *
from store.serializers import *
from django.db.models import Max
from rest_framework.permissions import *
from rest_framework.viewsets import ModelViewSet
from rest_framework import viewsets
from user.permissions import IsSuperOrSiteAdmin, IsTicketOwnerOrAdmin
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ProductFilter
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, GenericAPIView
from contextlib import nullcontext
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from django.db import transaction
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.decorators import api_view, action

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

class OrderPaidAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk):
        try:
            with transaction.atomic():

                order = (
                    Order.objects
                    .select_for_update()
                    .get(id=pk, user=request.user)
                )

                if order.status != Order.Status.PENDING:
                    return Response(
                        {"detail": "Order already processed"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # check stock
                for item in order.items.select_related("product"):
                    product = (
                        Product.objects
                        .select_for_update()
                        .get(id=item.product.id)
                    )

                    if product.stock < item.quantity:
                        return Response(
                            {
                                "detail": f"Not enough stock for {product.name}"
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                # reduce stock
                for item in order.items.select_related("product"):
                    product = item.product
                    product.stock -= item.quantity
                    product.save()

                # mark paid
                order.status = Order.Status.PAID
                order.save()

                # lock cart
                cart = request.user.cart
                cart.is_locked = True
                cart.save()

                return Response(
                    {"detail": "Order paid successfully"},
                    status=status.HTTP_200_OK
                )

        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class TicketViewSet(ModelViewSet):

    serializer_class = TicketSerializer
    permission_classes = [IsTicketOwnerOrAdmin]

    def get_queryset(self):

        if self.request.user.is_staff:
            return Ticket.objects.all()

        return Ticket.objects.filter(user=self.request.user)

    def perform_create(self, serializer):

        # Only users (not admins) can create tickets - RULES!
        if self.request.user.is_staff:
            raise PermissionDenied("Admins cannot create tickets.")

        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):

        ticket = self.get_object()

        if not request.user.is_staff:
            raise PermissionDenied("Only admins can close tickets.")

        ticket.status = Ticket.Status.CLOSED
        ticket.save()

        return Response({"detail": "Ticket closed."})



class TicketMessageCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ticket_id):

        ticket = get_object_or_404(Ticket, id=ticket_id)

        # If closed → no replies allowed
        if ticket.status == Ticket.Status.CLOSED:
            return Response(
                {"detail": "Ticket is closed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # User rules
        if not request.user.is_staff:
            if ticket.user != request.user:
                raise PermissionDenied("You cannot reply to this ticket.")

        # Create message
        message = TicketMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=request.data.get("message"),
        )

        # Auto-update status logic
        if request.user.is_staff:
            ticket.status = Ticket.Status.ANSWERED
        else:
            ticket.status = Ticket.Status.OPEN

        ticket.save()

        serializer = TicketMessageSerializer(message)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UserPanelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDashboardSerializer(request.user)
        return Response(serializer.data)

class ProductPriceUpdateAPIView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):

        try:
            product = Product.objects.get(pk=pk)

        except Product.DoesNotExist:
            return Response({"detail": "Product not found"}, status=404)

        serializer = ProductPriceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_price = serializer.validated_data["price"]

        # ذخیره تاریخچه قیمت
        ProductPriceHistory.objects.create(
            product=product,
            price=product.price
        )

        product.price = new_price
        product.save()

        return Response({"detail": "Price updated successfully"})
    
class ProductPriceHistoryAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):

        history = ProductPriceHistory.objects.filter(product_id=pk)

        serializer = ProductPriceHistorySerializer(history, many=True)

        return Response(serializer.data)

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
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]
class AddressGenericDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    pagination_class = CustomLimitOffsetPagination()
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]


class OrdersGenericApiView(ListCreateAPIView):
    serializer_class = OrderSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Order.objects.none()
        return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrdersGenericDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

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


class ChangePasswordView(GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [AllowAny]

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
    permission_classes = [AllowAny]
class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [AllowAny]

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
    permission_classes = [AllowAny]

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