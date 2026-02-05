from django.contrib import admin
from .models import *


class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'stock')
    inlines = [ProductAttributeInline]
    search_fields = ('name', 'price', 'stock')

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'is_main', 'created_at')
    list_filter = ('is_main',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'name', 'value')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at', 'follow_up_code')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'follow_up_code')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'quantity', 'item_subtotal')
    readonly_fields = ('item_subtotal',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'item_subtotal')
    list_filter = ('order__status',)
    search_fields = ('product__name', 'order__follow_up_code')
    readonly_fields = ('item_subtotal',)


# اگر می‌خوای داخل صفحه Order بتونی آیتم‌هاش رو مستقیم ویرایش کنی:
OrderAdmin.inlines = [OrderItemInline]
