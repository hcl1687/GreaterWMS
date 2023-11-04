from rest_framework import serializers
from .models import ListModel
from utils import datasolve
from warehouse.serializers import WarehouseGetSerializer
from shop.serializers import ShopGetSerializer

class ShopwarehouseGetSerializer(serializers.ModelSerializer):
    shopwarehouse_code = serializers.CharField(read_only=True, required=False)
    shopwarehouse_name = serializers.CharField(read_only=True, required=False)
    supplier = serializers.CharField(read_only=True, required=False)
    creater = serializers.CharField(read_only=True, required=False)
    create_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    update_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', ]

    def to_representation(self, instance):
        self.fields['warehouse'] =  WarehouseGetSerializer(read_only=True)
        self.fields['shop'] =  ShopGetSerializer(read_only=True)
        return super(ShopwarehouseGetSerializer, self).to_representation(instance)

class ShopwarehousePostSerializer(serializers.ModelSerializer):
    openid = serializers.CharField(read_only=False, required=False, validators=[datasolve.openid_validate])
    shopwarehouse_code = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    shopwarehouse_name = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    supplier = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]

class ShopwarehouseUpdateSerializer(serializers.ModelSerializer):
    shopwarehouse_code = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    shopwarehouse_name = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=True, required=False, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', 'supplier' ]

class ShopwarehousePartialUpdateSerializer(serializers.ModelSerializer):
    shopwarehouse_code = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    shopwarehouse_name = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=True, required=False, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', 'supplier' ]
