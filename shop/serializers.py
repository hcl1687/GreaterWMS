from rest_framework import serializers
from .models import ListModel
from utils import datasolve

class ShopGetSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(read_only=True, required=False)
    shop_type = serializers.CharField(read_only=True, required=False)
    shop_data = serializers.CharField(read_only=True, required=False)
    supplier = serializers.CharField(read_only=True, required=False)
    creater = serializers.CharField(read_only=True, required=False)
    sync = serializers.BooleanField(read_only=True, required=False)
    create_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    update_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', ]

class ShopPostSerializer(serializers.ModelSerializer):
    openid = serializers.CharField(read_only=False, required=False, validators=[datasolve.openid_validate])
    shop_name = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    shop_type = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    shop_data = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    supplier = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]

class ShopUpdateSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    shop_type = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    shop_data = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]

class ShopPartialUpdateSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    shop_type = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    shop_data = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]

class FileRenderSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    shop_type = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    shop_data = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    supplier = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    create_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    update_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = ListModel
        ref_name = 'ShopFileRenderSerializer'
        exclude = ['openid', 'is_delete', ]