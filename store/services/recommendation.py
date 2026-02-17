from django.db.models import (
    Count,
    Sum,
    Case,
    When,
    IntegerField,
    Value,
    Q, F,
)
from django.db.models.functions import Coalesce

from store.models import Product, OrderItem, Order

def get_hybrid_recommendations(product, limit=8):
    """
    Hybrid recommendation system:
    - Same category boost
    - Popularity (total sold)
    - Collaborative filtering (co-purchased products)
    """

    # -------------------------------------
    # Step 1 — Users who bought this product
    # -------------------------------------
    users_who_bought = OrderItem.objects.filter(
        product=product,
        order__status=Order.Status.PAID,
    ).values_list("order__user", flat=True)

    # -------------------------------------
    # Step 2 — Co-purchased products
    # -------------------------------------
    co_purchase_queryset = OrderItem.objects.filter(
        order__user__in=users_who_bought,
        order__status=Order.Status.PAID,
    ).exclude(product=product)

    # -------------------------------------
    # Step 3 — Base Product Query
    # -------------------------------------
    queryset = (
        Product.objects
        .exclude(id=product.id)
        .annotate(

            # Popularity score
            total_sold=Sum(
                "orderitem__quantity",
                filter=Q(orderitem__order__status=Order.Status.PAID),
            ),

            # Collaborative score
            co_purchase_count=Count(
                "orderitem",
                filter=Q(
                    orderitem__in=co_purchase_queryset
                ),
            ),

            # Category match boost
            category_match=Case(
                When(category=product.category, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
        )
        .annotate(
            # Weighted final score
            score=(
                (5 * F("category_match")) +
                (3 * F("co_purchase_count")) +
                (1 * Coalesce(F("total_sold"), 0))
            )
        )
        .order_by("-score")
    )

    return queryset[:limit]