from django_filters import FilterSet
from .models import ListModel

class Filter(FilterSet):
    class Meta:
        model = ListModel
        fields = {
            "id": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "platform_id": ['exact', 'iexact', 'contains', 'icontains'],
            "platform_warehouse_id": ['exact', 'iexact', 'contains', 'icontains'],
            "dn_code": ['exact', 'iexact', 'contains', 'icontains'],
            "status": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "order_time": ['year', 'month', 'day', 'week_day', 'gt', 'gte', 'lt', 'lte', 'range'],
            "openid": ['exact', 'iexact', 'contains', 'icontains'],
            "supplier": ['exact', 'iexact', 'contains', 'icontains'],
            "creater": ['exact', 'iexact', 'contains', 'icontains'],
            "is_delete": ['exact', 'iexact'],
            "create_time": ['year', 'month', 'day', 'week_day', 'gt', 'gte', 'lt', 'lte', 'range'],
            "update_time": ['year', 'month', 'day', 'week_day', 'gt', 'gte', 'lt', 'lte', 'range']
        }
