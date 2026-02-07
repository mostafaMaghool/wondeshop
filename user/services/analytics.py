from django.db.models import Sum
from django.utils.timezone import now

from store.models import Product, Order


def get_admin_kpis():
    today = now().date()

    return {
        "total_products": Product.objects.count(),
        "low_stock_products": Product.objects.filter(stock__lt=5).count(),
        "draft_orders": Order.objects.filter(status="draft").count(),
        "paid_orders_today": Order.objects.filter(
            status="paid",
            created_at__date=today
        ).count(),
        "revenue_today": (
            Order.objects
            .filter(status="paid", created_at__date=today)
            .aggregate(total=Sum("total_price"))["total"]
            or 0
        ),
    }
