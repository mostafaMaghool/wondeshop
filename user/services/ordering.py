from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import PermissionDenied

from store.models import OrderItem, Order, Product
from user.api.admin_models import AuditLog
from user.services.audit import log_snapshot_change
from user.services.inventory import deduct_stock_for_order


@transaction.atomic
def create_order_item(*, order: Order, product, quantity):
    """
    Create an order item and snapshot product price.
    """
    if order.status != "draft":
        raise ValueError("Cannot modify confirmed order!")

    order_item = OrderItem.objects.create(
        order=order,
        product=product,
        quantity=quantity,
        price=product.price,
    )

    log_snapshot_change(
        user=Order.user,
        obj=order_item,
        before=None,
        after={
            "product_id": product.id,
            "quantity": quantity,
            "price": product.price,
        },
        action=AuditLog.ACTION_CHOICES.SNAPSHOT,
    )
    return order_item

def snapshot_address(order, address, user):
    before = {
        "shipping_full_name": order.shipping_full_name,
        "shipping_phone": order.shipping_phone,
        "shipping_address": order.shipping_address,
        "shipping_city": order.shipping_city,
        "shipping_postal_code": order.shipping_postal_code,
    }

    order.shipping_full_name = address.full_name
    order.shipping_phone = address.phone
    order.shipping_address = address.address
    order.shipping_city = address.city
    order.shipping_postal_code = address.postal_code
    order.save()

    after = {
        "shipping_full_name": order.shipping_full_name,
        "shipping_phone": order.shipping_phone,
        "shipping_address": order.shipping_address,
        "shipping_city": order.shipping_city,
        "shipping_postal_code": order.shipping_postal_code,
    }

    log_snapshot_change(
        user=user,
        obj=order,
        before=before,
        after=after,
        action=AuditLog.ACTION_CHOICES.SNAPSHOT,
    )


@transaction.atomic
def confirm_order(*, order: Order, user = None):
    """
    Confirm an order and deduct inventory.
    So that the products stock does not conflict!
    """

    if order.status != "draft":
        raise ValueError("Only draft orders can be confirmed")

    deduct_stock_for_order(order)

    order.status = "confirmed"
    order.save(update_fields=["status"])

    log_snapshot_change(
        user=user,
        action="order_confirmed",
        obj=order,
        metadata={"status": "paid"},
    )


def adjust_product_stock(*, product, delta: int, reason: str = "", user = None):
    """
    Adjust the stuck by delta (positive for increase,
                                and negative for decrease)
    :param user:
    :param product:
    :param delta:
    :param reason:
    :return:
    """
    with transaction.atomic():
        product = (Product.objects.select_for_update().get(pk=product.pk))
        product.stock = F("stock") + delta
        product.save(update_fields=["stock"])

        log_snapshot_change(
            user=user,
            action="stock_adjusted",
            obj=product,
            metadata={"delta": delta},
        )

def change_order_status(*, order, new_status, user):
    if user.admin_role != (user.AdminRole.SUPER_ADMIN | user.AdminRole.SITE_ADMIN):
        raise PermissionDenied("Only super admins can change roles")

    order.status = new_status
    order.save(update_fields=["status"])

    log_snapshot_change(
        user=user,
        action="order_status_changed",
        obj=order,
        metadata={"new_status": new_status},
    )
