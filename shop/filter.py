from django_filters import FilterSet
from .models import ListModel, TypeListModel

class Filter(FilterSet):
    class Meta:
        model = ListModel
        fields = {
            "id": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "shop_name": ['exact', 'iexact', 'contains', 'icontains'],
            "shop_type": ['exact', 'iexact', 'contains', 'icontains'],
            "shop_data": ['exact', 'iexact', 'contains', 'icontains'],
            "sync": ['exact', 'iexact'],
            "supplier": ['exact', 'iexact', 'contains', 'icontains'],
            "creater": ['exact', 'iexact', 'contains', 'icontains'],
            "is_delete": ['exact', 'iexact'],
            "create_time": ['year', 'month', 'day', 'week_day', 'gt', 'gte', 'lt', 'lte', 'range'],
            "update_time": ['year', 'month', 'day', 'week_day', 'gt', 'gte', 'lt', 'lte', 'range']
        }
