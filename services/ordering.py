from django.db import transaction
from store.models import OrderItem


@transaction.atomic
def create_order_item(*, order, product, quantity):
    """
    Create an order item and snapshot product price.
    """

    return OrderItem.objects.create(
        order=order,
        product=product,
        unit_price=product.current_price,  # 🔒 The snapshot!!
        quantity=quantity,
    )