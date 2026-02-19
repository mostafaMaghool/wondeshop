from django.conf import settings
from django.db import models
from user.models import User
from django.core.validators import MinLengthValidator
from django.db.models import Q
#region Sara
from django.utils.text import slugify
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(validators=[MinLengthValidator(10)])
    price = models.PositiveIntegerField(default=0)
    image_url = models.ImageField(upload_to='product_img/',default='product_img/Asset_64x.png',null=True,blank=True)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )
    is_active = models.BooleanField(default=True)


    class Meta:
        verbose_name = 'product'
        verbose_name_plural = 'products'
        
    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='product_images/')
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'product image'
        verbose_name_plural = 'product images'

    def __str__(self):
        return f"{self.product.name} image"
   
class ProductAttribute(models.Model):
    ATTRIBUTE_CHOICES = [
        ('weight', 'Weight'),
        ('size', 'Size'),
        ('color', 'Color'),
        ('type', 'Type'),
        ('country', 'Country'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='attributes'
    )
    name = models.CharField(
        max_length=50,
        choices=ATTRIBUTE_CHOICES
    )
    value = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'product attribute'
        verbose_name_plural = 'product attributes'

    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"

class Ticket(models.Model):

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ANSWERED = "answered", "Answered"
        CLOSED = "closed", "Closed"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject} - {self.status}"

#endregion
    
# region Kooshan
    
class TicketMessage(models.Model):

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ticket_messages",
    )

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    follow_up_code = models.BigIntegerField(editable=False)

    user = models.ForeignKey(to=settings.AUTH_USER_MODEL,
                      on_delete=models.CASCADE,
                      related_name='order',
                      verbose_name='user')

    status = models.CharField(max_length=20,
                       choices=Status.choices,
                       default=Status.PENDING,
                       verbose_name='order state')

    total_amount =  models.DecimalField(max_digits=12,
                                decimal_places=2,
                                default=0.00,
                                verbose_name='the total order items amount')

    created_at = models.DateTimeField(auto_now_add=True,
                               verbose_name="the time of order creation")
    updated_at = models.DateTimeField(auto_now=True,
                               verbose_name="the time of order being edited")
    shipment_time = models.DateTimeField(null=True, blank=True,verbose_name="the set time ,so that the order be shipped")
    address_title = models.CharField(max_length=20)

    address_state = models.CharField(max_length=45)
    address_postal_code = models.CharField(max_length=16)
    address_country = models.CharField(max_length=45)

    full_name = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=100)

    class Meta:
        ordering = ['-created_at']
        verbose_name='order'
    def __str__(self):
            return f"سفارش #{self.id} - {self.user}"

    def __str__(self):
        return f"سفارش #{self.follow_up_code} - {self.user.username if self.user else 'بدون کاربر'}"

    def __str__(self):
        return f"سفارش {self.follow_up_code} – کاربر: {self.user.get_full_name() or self.user.username}" 

class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'

    user = models.ForeignKey(
            settings.AUTH_USER_MODEL,          # ← این مهمه!
            on_delete=models.CASCADE,          # یا SET_NULL / PROTECT بسته به نیازت
            related_name='payments',           # اختیاری ولی خیلی خوبه
            null=True,                         # اگر بعضی پرداخت‌ها بدون کاربر مجازن
            blank=True,
        )

    payment_date = models.DateTimeField(auto_now_add=True)

    amount = models.DecimalField(max_digits=15, decimal_places=2)

    class Method(models.TextChoices):
        TRANSFER = 'transfer', 'کارت بانکی'

    method = models.CharField(
        max_length=15,
        choices=Method.choices,
        default=Method.TRANSFER,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    def __str__(self):
        return f"Payment for Order #{self.order.id}"


class ProductPriceHistory(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="price_history",
        on_delete=models.CASCADE
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)

    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["product", "valid_from"]),
            models.Index(fields=["product", "valid_to"]),
        ]
#endregion
    
# region Mostafa
from decimal import Decimal

class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True,          # موقتاً اجازه بده null باشه
        blank=True
    )

    def save(self, *args, **kwargs):
        if self.price is None and self.product is not None:
            self.price = self.product.price  # قیمت محصول رو در لحظه ذخیره کن
        super().save(*args, **kwargs)

    @property
    def item_subtotal(self):
        qty = self.quantity or 0
        price = self.price or Decimal('0.00')
        return qty * price

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'محصول حذف‌شده'} (Order #{self.order.id})"

class Address(models.Model):

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='addresses',
        db_index=True,
        verbose_name='user'
    )
    title = models.CharField(max_length=20, verbose_name='the address title (like «home»)')
    city = models.CharField(max_length=40, verbose_name='city/town')
    state = models.CharField(max_length=45, verbose_name='state/province')
    postal_code = models.CharField(max_length=16, verbose_name='zip code/postal code')
    country = models.CharField(max_length=45, verbose_name='country')
    is_default = models.BooleanField(default=False, verbose_name='default address')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='creation time')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='update time')

    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name = 'address'
        unique_together = (('user', 'is_default'),)  # only one default for every user

    def __str__(self):
        return f'{self.title} - {self.city}, {self.country}'
    
class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    is_locked = models.BooleanField(default=False)
    def total_price(self):
        return sum(
            item.quantity * item.product.price
            for item in self.items.all()
        )
    def __str__(self):
        return f'Cart({self.user.username})'
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE,
                             related_name='items')
    product = models.ForeignKey('Product', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'
#endregion