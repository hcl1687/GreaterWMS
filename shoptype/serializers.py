from rest_framework import serializers
from .models import ListModel

class ShoptypeGetSerializer(serializers.ModelSerializer):
    shop_type = serializers.CharField(read_only=True, required=False)
    shop_schema = serializers.CharField(read_only=True, required=False)
    creater = serializers.CharField(read_only=True, required=False)
    create_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    update_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = ListModel
        ref_name = 'ShoptypeGetSerializer'
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', ]
