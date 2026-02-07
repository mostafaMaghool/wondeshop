from django.db import transaction
from django.utils import timezone
from store.models import ProductPriceHistory
from user.services.audit import log_action


@transaction.atomic
def change_product_price(*, product, new_price, user = None):
    """
    This is the ONLY place allowed to
    change prices and record history.
    """

    # No-operation guard
    if product.price == new_price:
        return product

    now = timezone.now()
    old_price = product.price

    # Close previous active price
    ProductPriceHistory.objects.filter(
        product=product,
        valid_to__isnull=True
    ).update(valid_to=now)

    # Create new price record
    ProductPriceHistory.objects.create(
        product=product,
        price=new_price,
        valid_from=now
    )

    # Update cached current price
    product.price = new_price
    product.save(update_fields=["current_price"])

    log_action(
        user=user,
        action="price_changed",
        obj=product,
        metadata={
            "old_price": old_price,
            "new_price": new_price,
        },
    )

    return product

