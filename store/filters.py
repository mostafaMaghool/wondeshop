import django_filters
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
