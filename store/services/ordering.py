from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import PermissionDenied

from store.models import OrderItem, Order, Product
from store.services.inventory import deduct_stock_for_order


@transaction.atomic
def create_order_item(*, order, product, quantity):
    """
    Create an order item and snapshot product price.
    """
    if order.status != "draft":
        raise ValueError("Cannot modify confirmed order!")
    return OrderItem.objects.create(
        order=order,
        product=product,
        unit_price=product.price,  # 🔒 The snapshot!!
        quantity=quantity,
    )


@transaction.atomic
def confirm_order(order: Order):
    """
    Confirm an order and deduct inventory.
    So that the products stock does not conflict!
    """

    if order.status != "draft":
        raise ValueError("Only draft orders can be confirmed")

    deduct_stock_for_order(order)

    order.status = "confirmed"
    order.save(update_fields=["status"])


def adjust_product_stock(*, product, delta: int, reason: str = ""):
    """
    Adjust the stuck by delta (positive for increase,
                                and negative for decrease)
    :param product:
    :param delta:
    :param reason:
    :return:
    """
    with transaction.atomic():
        product = (Product.objects.select_for_update().get(pk=product.pk))
        product.stock = F("stock") + delta
        product.save(update_fields=["stock"])

def change_order_status(*, order, new_status, user):
    if not user.has_perm("store.confirm_order"):
        raise PermissionDenied()

    order.status = new_status
    order.save(update_fields=["status"])

    # TODO: Add after implementation of AuditLog
    # log_action(
    #     user=user,
    #     action="order_status_changed",
    #     obj=order,
    #     metadata={"new_status": new_status},
    # )
