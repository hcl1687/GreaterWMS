from rest_framework import serializers
from .models import ListModel
from utils import datasolve
from shop.serializers import ShopGetSerializer
from stock.serializers import StockBinGetSerializer

class ShoporderGetSerializer(serializers.ModelSerializer):
    platform_id = serializers.CharField(read_only=True, required=False)
    platform_warehouse_id = serializers.CharField(read_only=True, required=False)
    dn_code = serializers.CharField(read_only=True, required=False)
    order_data = serializers.CharField(read_only=True, required=False)
    status = serializers.IntegerField(read_only=True, required=False)
    supplier = serializers.CharField(read_only=True, required=False)
    creater = serializers.CharField(read_only=True, required=False)
    create_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    update_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', ]

    def to_representation(self, instance):
        self.fields['shop'] =  ShopGetSerializer(read_only=True)
        self.fields['stockbin'] =  StockBinGetSerializer(read_only=True)
        return super(ShoporderGetSerializer, self).to_representation(instance)

class ShoporderPostSerializer(serializers.ModelSerializer):
    platform_id = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    platform_warehouse_id = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    dn_code = serializers.CharField(read_only=False, required=False, validators=[datasolve.data_validate])
    order_data = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    openid = serializers.CharField(read_only=False, required=False, validators=[datasolve.openid_validate])
    supplier = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]

class ShoporderUpdateSerializer(serializers.ModelSerializer):
    platform_id = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    platform_warehouse_id = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    dn_code = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    order_data = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=True, required=False, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', 'supplier' ]

class ShoporderPartialUpdateSerializer(serializers.ModelSerializer):
    platform_id = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    platform_warehouse_id = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    dn_code = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    order_data = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=True, required=False, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', 'supplier' ]

class FileRenderSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.shop_name', read_only=False, required=True, validators=[datasolve.data_validate])
    shop_type = serializers.CharField(source='shop.shop_type', read_only=False, required=True, validators=[datasolve.data_validate])
    platform_id = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    platform_warehouse_id = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    dn_code = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    order_data = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    dn_status = serializers.IntegerField(read_only=False, required=False)
    supplier = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    create_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    update_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = ListModel
        ref_name = 'ShoporderFileRenderSerializer'
        exclude = ['openid', 'is_delete', ]
