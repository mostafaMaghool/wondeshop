from django.conf import settings
from django.db import models
from django.core.validators import MinLengthValidator
from django.utils import timezone
# region Kooshan
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
    image_url = models.ImageField(upload_to='product_img/',default='product_img/default.jpg',null=True,blank=True)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )
    is_active = models.BooleanField(default=True)    
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)
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

    
class Payment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
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

#endregion
    
# region Kooshan
class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    follow_up_code = models.BigIntegerField(unique=True, editable=False)

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

    follow_up_code = models.BigIntegerField()

    class Meta:
        ordering = ['-created_at']
        verbose_name='order'

    def __str__(self):
        return f'Order #{self.pk} - {self.user}'
    
class ProductPriceHistory(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="price_history",
        on_delete=models.CASCADE
    )
    price = models.DecimalField(max_digits=10, decimal_places=2,default=0)

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
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2) 

    @property
    def item_subtotal(self):
        return self.quantity * self.product.price
    def __str__(self):
        return f"{self.quantity} x {self.product.name} in order {self.order.order_id}"

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