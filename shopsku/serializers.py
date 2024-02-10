from rest_framework import serializers
from .models import ListModel
from utils import datasolve
from shop.serializers import ShopGetSerializer

class ShopskuGetSerializer(serializers.ModelSerializer):
    platform_id = serializers.CharField(read_only=True, required=False)
    platform_sku = serializers.CharField(read_only=True, required=False)
    platform_data = serializers.CharField(read_only=True, required=False)
    goods_code = serializers.CharField(read_only=True, required=False)
    sync_status = serializers.IntegerField(read_only=True, required=False)
    sync_message = serializers.CharField(read_only=True, required=False)
    sync_time = serializers.DateTimeField(read_only=True)
    supplier = serializers.CharField(read_only=True, required=False)
    creater = serializers.CharField(read_only=True, required=False)
    create_time = serializers.DateTimeField(read_only=True)
    update_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', ]

    def to_representation(self, instance):
        self.fields['shop'] =  ShopGetSerializer(read_only=True)
        return super(ShopskuGetSerializer, self).to_representation(instance)

class ShopskuPostSerializer(serializers.ModelSerializer):
    openid = serializers.CharField(read_only=False, required=False, validators=[datasolve.openid_validate])
    platform_id = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    platform_sku = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    goods_code = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    sync_message = serializers.CharField(read_only=False, required=False, validators=[datasolve.data_validate])
    supplier = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]

class ShopskuUpdateSerializer(serializers.ModelSerializer):
    platform_id = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    platform_sku = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    goods_code = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    sync_message = serializers.CharField(read_only=False, required=False, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=True, required=False, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', 'supplier' ]

class ShopskuPartialUpdateSerializer(serializers.ModelSerializer):
    platform_id = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    platform_sku = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    goods_code = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    sync_message = serializers.CharField(read_only=False, required=False, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=True, required=False, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', 'supplier' ]

class FileRenderSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.shop_name', read_only=False, required=True, validators=[datasolve.data_validate])
    shop_type = serializers.CharField(source='shop.shop_type', read_only=False, required=True, validators=[datasolve.data_validate])
    platform_id = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    platform_sku = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    platform_data = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    goods_code = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    platform_stock = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    sys_stock = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    sync_status = serializers.IntegerField(read_only=False, required=False)
    sync_message = serializers.CharField(read_only=False, required=False, validators=[datasolve.data_validate])
    sync_time = serializers.DateTimeField(read_only=True)
    supplier = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    create_time = serializers.DateTimeField(read_only=True)
    update_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ListModel
        ref_name = 'ShopskuFileRenderSerializer'
        exclude = ['openid', 'is_delete', ]

class StockSyncGetSerializer(serializers.ModelSerializer):
    platform_id = serializers.CharField(read_only=True, required=False)
    platform_sku = serializers.CharField(read_only=True, required=False)
    goods_code = serializers.CharField(read_only=True, required=False)
    sync_status = serializers.IntegerField(read_only=True, required=False)
    sync_message = serializers.CharField(read_only=True, required=False)
    sync_time = serializers.DateTimeField(read_only=True)
    supplier = serializers.CharField(read_only=True, required=False)
    creater = serializers.CharField(read_only=True, required=False)
    create_time = serializers.DateTimeField(read_only=True)
    update_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', ]

    def to_representation(self, instance):
        self.fields['shop'] =  ShopGetSerializer(read_only=True)
        return super(ShopskuGetSerializer, self).to_representation(instance)

class StockSyncPostSerializer(serializers.ModelSerializer):
    goods_code = serializers.ListField(child=serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate]))

    class Meta:
        model = ListModel
        exclude = ['is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]
