import django_filters
from django.db.models import Q

from .models import Product

class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        label='حداقل قیمت'
    )
    max_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        label='حداکثر قیمت'
    )

    available = django_filters.BooleanFilter(
        method='filter_available',
        label='فقط محصولات موجود'
    )

    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        label='جستجو'
    )

    class Meta:
        model = Product
        fields = ['name', 'min_price', 'max_price', 'available']

    def filter_available(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset


class AdminProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(method="filter_name")
    category = django_filters.CharFilter(
        field_name="category__name",
        lookup_expr="icontains",
    )
    available = django_filters.BooleanFilter(method="filter_available")

    class Meta:
        model = Product
        fields = []

    def filter_name(self, queryset, name, value):
        """
        Handles:
        - Exact name
        - Partial phrase
        - Multiple words (split search)
        """
        words = value.split()

        query = Q()
        for word in words:
            query |= Q(name__icontains=word)

        return queryset.filter(query)

    def filter_available(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset
