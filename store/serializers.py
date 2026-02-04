from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from rest_framework.fields import SerializerMethodField, DecimalField, DateTimeField, CharField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from user.serializers import User
from rest_framework_simplejwt.tokens import RefreshToken
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
        fields = ('name', 'description', 'price', 'image_url', 'stock', 'category','is_active')
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
        fields = ('amount', 'method')
        read_only_fields = ('payment_date', 'payment_id')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

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
    order = PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        write_only=True,
        help_text="related order identifier"
    )

    product = PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        help_text="product identifier"
    )

    item_subtotal = SerializerMethodField(read_only=True)

    def get_item_subtotal(self, obj):
        return str(obj.item_subtotal)

    # جزئیات سفارش به صورت خواندنی (اختیاری)
    # order_detail = SerializerMethodField(read_only=True)
    #
    # def get_order_detail(self, obj):
    #     """نمایش مختصر سفارش؛ می‌توانید فیلدهای دلخواه اضافه کنید."""
    #     return {
    #         "id": obj.order.id,
    #         "status": obj.order.status,
    #         "created_at": obj.order.created_at,
    #     }
    #
    # line_total = DecimalField(
    #     max_digits=12, decimal_places=2, read_only=True
    # )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "order",
            # "order_detail",
            "quantity",
            "item_subtotal"
            # "price",
        ]
        read_only_fields = ["id", "item_subtotal"]

    def validate_quantity(self, value):
        if value <= 0:
            raise ValidationError("Quantity insufficient [must be greater than zero].")
        return value

    # def validate_unit_price(self, value):
    #     if value <= 0:
    #         raise ValidationError("Unit price must be positive.")
    #     return value
import random

class OrderSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        # 🔥 تولید کد پیگیری امن
        validated_data["follow_up_code"] = random.randint(1000000000, 9999999999)

        items_data = self.context.get("items_data", [])
        order = Order.objects.create(**validated_data)

        total = 0
        for item_dict in items_data:
            product_id = item_dict["product"]

            product = Product.objects.get(id=product_id)

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_dict["quantity"]
            )

            total += product.price * item_dict["quantity"]


        order.total_amount = total
        order.save()
        return order
    items = OrderItemSerializer(source="orderitem_set", many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "user",
            "created_at",
            "updated_at",
            "status",
            "total_amount",
            "shipment_time",
            "items",
        ]
        read_only_fields = [
            "id", "created_at", "updated_at",
            "total_amount", "items", "follow_up_code"
        ]

    def get_items(self, obj):
        # از related_name مدل OrderItem استفاده می‌کنیم
        # فرض کنیم در مدل OrderItem:
        # order = models.ForeignKey(Order, related_name="items", ...)
        order_items = obj.items.all()
        return OrderItemSerializer(order_items, many=True).data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def save(self, **kwargs):
        token = RefreshToken(self.validated_data["refresh"])
        token.blacklist()


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
        
