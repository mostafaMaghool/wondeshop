from django.db import transaction
from django.db.models import F

from store.models import Product, OrderItem
from store.services.exceptions import InsufficientStockError


@transaction.atomic
def deduct_stock(product_id: int, quantity: int):
    """
    Atomically deduct stock from a product.

    exception:
        InsufficientStockError
    """

    product = (
        Product.objects
        .select_for_update()  # 🔒 row-level lock, most important line
        .get(id=product_id)
    )

    if product.stock < quantity:
        raise InsufficientStockError(
            product_id=product.id,
            requested=quantity,
            available=product.stock
        )

    product.stock = F("stock") - quantity
    product.save(update_fields=["stock"])

@transaction.atomic
def deduct_stock_for_order(order):
    """
    Deduct stock for all items in an order.
    """

    items = (
        OrderItem.objects
        .select_related("product")
        .filter(order=order)
    )

    for item in items:
        deduct_stock(
            product_id=item.product_id,
            quantity=item.quantity
        )
