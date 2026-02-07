from django.db.models import Q
from store.models import Product


def search_products(query: str):
    """
    [free-text] search service for products.
    Scope:
    - name
    - description
    - category name
    """

    if not query:
        return Product.objects.none()

    return (
        Product.objects
        .select_related("category")
        .filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
        .distinct()
    )
