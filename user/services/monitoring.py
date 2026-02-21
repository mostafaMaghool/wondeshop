from datetime import timedelta, datetime

from django.db.models import Sum, Avg, Count
from django.db.models.functions import TruncDay
from django.utils import timezone

from store.models import Order


def get_admin_dashboard_metrics(range_type=None, start=None, end=None):

    start_date, end_date = resolve_time_range(range_type, start, end)

    orders_qs = Order.objects.all()

    if start_date and end_date:
        orders_qs = orders_qs.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )

    total_orders = orders_qs.count()
    paid_orders = orders_qs.filter(status=Order.Status.PAID).count()

    total_revenue = (
        orders_qs.filter(status=Order.Status.PAID)
        .aggregate(total=Sum("total_price"))["total"] or 0
    )

    average_order_value = (
        orders_qs.filter(status=Order.Status.PAID)
        .aggregate(avg=Avg("total_price"))["avg"] or 0
    )

    return {
        "orders": {
            "total": total_orders,
            "paid": paid_orders,
        },
        "revenue": {
            "total": total_revenue,
            "average_order_value": average_order_value,
        },
    }


def get_revenue_trend(range_type="week"):

    start_date, end_date = resolve_time_range(range_type)

    qs = Order.objects.filter(status=Order.Status.PAID)

    if start_date and end_date:
        qs = qs.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )

    if range_type == "month":
        trunc = TruncDay("created_at")
    elif range_type == "week":
        trunc = TruncDay("created_at")
    else:
        trunc = TruncDay("created_at")

    trend = (
        qs.annotate(period=trunc)
        .values("period")
        .annotate(total=Sum("total_price"))
        .order_by("period")
    )

    return trend


def get_orders_trend(range_type="week"):

    start_date, end_date = resolve_time_range(range_type)

    qs = Order.objects.all()

    if start_date and end_date:
        qs = qs.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )

    trend = (
        qs.annotate(period=TruncDay("created_at"))
        .values("period")
        .annotate(total=Count("id"))
        .order_by("period")
    )

    return trend


def resolve_time_range(range_type, start=None, end=None):
    now = timezone.now()

    if range_type == "today":
        start_date = now.date()
        end_date = now.date()

    elif range_type == "week":
        start_date = (now - timedelta(days=7)).date()
        end_date = now.date()

    elif range_type == "month":
        start_date = (now - timedelta(days=30)).date()
        end_date = now.date()

    elif range_type == "custom" and start and end:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()

    else:
        start_date = None
        end_date = None

    return start_date, end_date