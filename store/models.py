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

class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    total_stock = models.PositiveIntegerField()
    reserved_stock = models.PositiveIntegerField(default=0)

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

    def calculate_total(self):
        total = sum(item.item_subtotal for item in self.items.all())
        self.total_amount = total
        self.save()

    class Meta:
        ordering = ['-created_at']
        verbose_name='order'

    def __str__(self):
        return f"سفارش {self.follow_up_code} – کاربر: {self.user.get_full_name() or self.user.username}" 

class Payment(models.Model):

    class Status(models.TextChoices):
        WAITING = "waiting", "Waiting"
        CONFIRMING = "confirming", "Confirming"
        FINISHED = "finished", "Finished"
        FAILED = "failed", "Failed"
        EXPIRED = "expired", "Expired"

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="payment"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    payment_id = models.CharField(max_length=255, blank=True)
    pay_address = models.CharField(max_length=255, blank=True)
    pay_currency = models.CharField(max_length=20, blank=True)

    price_amount = models.DecimalField(max_digits=12, decimal_places=2)
    pay_amount = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        null=True,
        blank=True
    )

    tx_hash = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def mark_success(self):
        self.status = self.Status.FINISHED
        self.save(update_fields=["status"])
        self.order.status = Order.Status.PAID
        self.order.save(update_fields=["status"])

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

from django.db import models
from django.conf import settings
from django.db.models import Q

class Address(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='addresses',
        db_index=True
    )

    title = models.CharField(max_length=50)
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)

    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=Q(is_default=True),
                name='unique_default_address_per_user'
            )
        ]

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(
                user=self.user,
                is_default=True
            ).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.city}"


class Cart(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )

    is_locked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total_price(self):
        return sum(
            item.quantity * item.price
            for item in self.items.all()
        ) or Decimal('0.00')

    def __str__(self):
        return f"Cart({self.user.username})"    

class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )

    quantity = models.PositiveIntegerField(default=1)

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    class Meta:
        unique_together = ('cart', 'product')

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.product.price
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

#endregion