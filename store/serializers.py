from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from rest_framework.fields import SerializerMethodField, DecimalField, DateTimeField, CharField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from user.serializers import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.relations import PrimaryKeyRelatedField
from store.models import *

# ======================================================
# region Sara (Products / Categories / Payments)
# ======================================================
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_main']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id','name', 'description', 'price', 'image_url', 'stock', 'category','is_active')
        read_only_fields = ['id']
        def validate_price(self, value):
            if value <= 0:
                raise serializers.ValidationError(
                    "price must be graeter than 0"
                )
            return value

class ProductInfoSerializer(serializers.Serializer):
    products = ProductSerializer(many=True)
    count = serializers.IntegerField()
    max_price =  serializers.FloatField()

class PaymentSerializer(ModelSerializer):
    class Meta:
            model = Payment
            fields = "__all__"
            read_only_fields = ('payment_date', 'payment_id','status')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class TicketMessageSerializer(serializers.ModelSerializer):

    sender = serializers.StringRelatedField(read_only=True)

    class Meta:
            model = TicketMessage
            fields = [
                "id",
                "ticket",
                "sender",
                "message",
                "created_at",
            ]
            read_only_fields = ["id", "sender", "created_at"]


class TicketSerializer(serializers.ModelSerializer):

    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "subject",
            "status",
            "created_at",
            "updated_at",
            "messages",
        ]
        read_only_fields = [
            "status",
            "created_at",
            "updated_at",
        ]


class UserDashboardSerializer(serializers.Serializer):

    user = serializers.SerializerMethodField()
    orders = serializers.SerializerMethodField()
    addresses = serializers.SerializerMethodField()
    cart = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()

    def get_user(self, obj):
        user = obj
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }

    def get_orders(self, obj):
        orders = Order.objects.filter(user=obj)
        return OrderSerializer(orders, many=True).data

    def get_addresses(self, obj):
        addresses = Address.objects.filter(user=obj)
        return AddressSerializer(addresses, many=True).data

    def get_cart(self, obj):
        try:
            cart = Cart.objects.get(user=obj)
            return CartSerializer(cart).data
        except Cart.DoesNotExist:
            return None

    def get_payments(self, obj):
        payments = Payment.objects.filter(user=obj)
        return PaymentSerializer(payments, many=True).data

#endregion
        
# ======================================================
# region Kooshan (Orders / Addresses / Auth)
# ======================================================
class AddressSerializer(ModelSerializer):
    user = PrimaryKeyRelatedField(queryset=User.objects.all(),
                                  help_text="username that address belongs to")
    postal_code = CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{5,10}$', 'wrong postal code..!')]
    )

    class Meta:
        model = Address
        fields = [
            "user",  # FK → User,
            "title",
            "city",
            "state",
            "postal_code",
            "country",
            "is_default"
        ]
        read_only_fields = ["address_id", "created_at", "updated_at"]


class OrderItemSerializer(ModelSerializer):
    item_subtotal = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "order",
            "product",
            "quantity",
            "price",
            "item_subtotal",
        ]
        read_only_fields = ["price", "item_subtotal"]

    def get_item_subtotal(self, obj):
        return obj.item_subtotal

    def validate(self, attrs):
        order = self.instance.order if self.instance else attrs.get("order")
        if order and order.status != Order.Status.PENDING:
            raise serializers.ValidationError(
                "Order items cannot be modified after payment."
            )
        return attrs
import random

class OrderSerializer(serializers.ModelSerializer):

    def generate_follow_up_code(self):
        while True:
            code = random.randint(1000000000, 9999999999)
            if not Order.objects.filter(follow_up_code=code).exists():
                return code

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        user = self.context["request"].user

        order = Order.objects.create(
            user=user,
            follow_up_code=self.generate_follow_up_code(),
            **validated_data
        )

        total = 0

        for item_data in items_data:
            product = item_data["product"]
            quantity = item_data["quantity"]

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )

            total += product.price * quantity

        order.total_amount = total
        order.save()

        return order
    items = OrderItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    # created_at = serializers.DateTimeField(read_only=True)
    # updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Order
        fields = [
            # "user",
            "id",
            "follow_up_code",
            "user",
            "status",
            "total_amount",
            "created_at",
            "updated_at",
            "shipment_time",
            "full_name",
            "phone",
            "address_postal_code",
            "items",
        ]
        read_only_fields = ["id", "status","total_amount"]

    def get_items(self, obj):
        # از related_name مدل OrderItem استفاده می‌کنیم
        # فرض کنیم در مدل OrderItem:
        # order = models.ForeignKey(Order, related_name="items", ...)
        order_items = obj.items.all()
        return OrderItemSerializer(order_items, many=True).data

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, input_old_password):
        user = self.context["request"].user
        if not user.check_password(input_old_password):
            raise ValidationError("Old password is incorrect!")
        return input_old_password

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


    def save(self):
        user = User.objects.filter(
        email=self.validated_data["email"]
        ).first()

        if user:
            token = PasswordResetTokenGenerator().make_token(user)
        # TODO send token via email or whatever later....
        #     self.context["send_reset"](user, token)

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.IntegerField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)


    def validate(self, attrs):
        user = User.objects.filter(pk=attrs["uid"]).first()
        if not user:
            raise serializers.ValidationError("Invalid input, Try anpther time!")


        if not PasswordResetTokenGenerator().check_token(user, attrs["token"]):
            raise serializers.ValidationError("Invalid or expired token")


        self.user = user
        return attrs


    def save(self):
        self.user.set_password(self.validated_data["new_password"])
        self.user.save()

class ProductPriceUpdateSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price can not be negative number..!")
        return value

class ProductPriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPriceHistory
        fields = ["price", "valid_from", "valid_to"]

#endregion
        
# ======================================================
# region Mostafa (Cart)
# ======================================================

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True)

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'product_id', 'quantity')
        extra_kwargs = {'quantity': {'min_value': 1}}

    def validate(self, attrs):
        product = attrs['product']
        if product.stock < attrs['quantity']:
            raise serializers.ValidationError('موجودی کافی نیست')
        return attrs


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('id', 'user', 'items','total_price')
        read_only_fields = ('user',)
    def get_total_price(self, obj):
        return obj.total_price()

#endregion
        
