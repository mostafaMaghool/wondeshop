from django.db import transaction

from user.api.admin_models import AuditLog
from user.services.audit import log_snapshot_change
from user.services.inventory import deduct_stock_for_order


def finalize_payment(*, payment, verified_status, user=None):
    """
    Central place to handle payment state transition.
    """

    if payment.status != payment.Status.PENDING:
        return payment  # idempotent behavior

    with transaction.atomic():

        before_status = payment.order.status

        if verified_status == "success":
            payment.status = payment.Status.PAID
            payment.save()

            payment.order.status = payment.order.Status.PAID
            payment.order.is_paid = True
            payment.order.save()

            deduct_stock_for_order(order= payment.order)

            log_snapshot_change(
                user=user,
                obj=payment.order,
                before={"status": before_status},
                after={"status": payment.order.status},
                action=AuditLog.ACTION_CHOICES.STATUS_CHANGE,
            )

        else:
            payment.status = payment.Status.FAILED
            payment.save()

            payment.order.status = payment.order.Status.PAYMENT_FAILED
            payment.order.save()

            log_snapshot_change(
                user=user,
                obj=payment.order,
                before={"status": before_status},
                after={"status": payment.order.status},
                action=AuditLog.ACTION_CHOICES.STATUS_CHANGE,
            )

    return payment
