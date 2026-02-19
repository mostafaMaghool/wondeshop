from django.db import transaction
from django.utils import timezone
from store.models import ProductPriceHistory


@transaction.atomic
def change_product_price(*, product, new_price):
    """
    This is the ONLY place allowed to
    change prices and record history.
    """

    # 1️⃣ No-op guard (very important)
    if product.price == new_price:
        return product

    now = timezone.now()

    # 2️⃣ Close previous active price
    ProductPriceHistory.objects.filter(
        product=product,
        valid_to__isnull=True
    ).update(valid_to=now)

    # 3️⃣ Create new price record
    ProductPriceHistory.objects.create(
        product=product,
        price=new_price,
        valid_from=now
    )

    # 4️⃣ Update cached current price
    product.price = new_price
    product.save(update_fields=["current_price"])

    return product