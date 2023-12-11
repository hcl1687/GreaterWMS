from rest_framework import serializers
from .models import ListModel

class BinpropertyGetSerializer(serializers.ModelSerializer):
    bin_property = serializers.CharField(read_only=True, required=False)
    creater = serializers.CharField(read_only=True, required=False)
    create_time = serializers.DateTimeField(read_only=True)
    update_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ListModel
        ref_name = 'BinpropertyGetSerializer'
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', ]
