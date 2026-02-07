from django.contrib import admin, messages
from django.contrib.admin import TabularInline, ModelAdmin

from store.models import *
from user.services.exceptions import InsufficientStockError
from user.services.ordering import confirm_order, adjust_product_stock
from user.services.pricing import change_product_price


class StoreAdminSite(admin.AdminSite):
    site_header = "Leather Store Admin"

class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "price")
@admin.action(description="Confirm selected order")
def confirm_orders(modeladmin, request, queryset):
    confirmed = 0
    failed = 0

    for order in queryset:
        try:
            confirm_order(order = order)
            confirmed += 1
        except InsufficientStockError:
            failed += 1

    if confirmed:
        messages.success(request, f"{confirmed}  order(s)"
                                  f" been confirmed successfully.")
    if failed:
        messages.error(request, f"{failed} order(s) been failed"
                                f"due to insufficient stock")

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ("id", "user", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__email",)
    inlines = [OrderItemInline]
    actions = [confirm_orders]

class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1

class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1

@admin.action(description="Decrease stock by 10")
def decrease_stock(modelamin, request, queryset):
    for product in queryset:
        adjust_product_stock(product=product, delta= -1)
    messages.warning(request, "Stock decreased by 1 "
                              "for the selected products.")


@admin.action(description="Increase stock by 10")
def increase_stock(modelamin, request, queryset):
    for product in queryset:
        adjust_product_stock(product=product, delta= 10)
    messages.success(request, "Stock increased by 10 "
                              "for the selected products.")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price',
                    'stock', 'low_stock', 'created_at')
    list_filter = ('category', 'created_at')
    inlines = [ProductAttributeInline, ProductImageInline]
    search_fields = ('name', 'price', 'description')
    readonly_fields = ('slug', 'created_at')
    autocomplete_fields = ('category',)
    actions = [decrease_stock, increase_stock]

    def low_stock(self, obj):
        return obj.stock < 5

    low_stock.boolean = True
    low_stock.short_description = "Low Stock!"



@admin.register(ProductPriceHistory)
class ProductPriceHistory(ModelAdmin):
    list_display = ("product", "price", "valid_from", "valid_to")
    list_filter = ("product",)
    readonly_fields = ("product", "price", "valid_from", "valid_to")


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'is_main', 'created_at')
    list_filter = ('is_main',)

@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ("id", "user")

@admin.register(CartItem)
class CartItemAdmin(ModelAdmin):
    list_display = ("cart", "product", "quantity",)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Address)
class AddressAdmin(ModelAdmin):
    list_display = ("user", "city", "state")
    search_fields = ("user__email", "city")

@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'name', 'value')

#Admin Actions region

@admin.action(description="Apply 10% discount")
def discount_10_percent(modeladmin, request, queryset):
    for product in queryset:
        new_price = product.price * 0.9
        change_product_price(product=product, new_price=new_price)

    messages.success(request, "10% discount applied.")

#endregion
