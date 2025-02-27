from rest_framework import serializers
from .models import ListModel
from utils import datasolve

class CompanyGetSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(read_only=True, required=False)
    company_city = serializers.CharField(read_only=True, required=False)
    company_address = serializers.CharField(read_only=True, required=False)
    company_contact = serializers.CharField(read_only=True, required=False)
    company_manager = serializers.CharField(read_only=True, required=False)
    creater = serializers.CharField(read_only=True, required=False)
    create_time = serializers.DateTimeField(read_only=True)
    update_time = serializers.DateTimeField(read_only=True)
    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id']

class CompanyPostSerializer(serializers.ModelSerializer):
    openid = serializers.CharField(read_only=False, required=False, validators=[datasolve.openid_validate])
    company_name = serializers.CharField(read_only=False,  required=True, validators=[datasolve.data_validate])
    company_city = serializers.CharField(read_only=False,  required=True, validators=[datasolve.data_validate])
    company_address = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    company_contact = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    company_manager = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]

class CompanyUpdateSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    company_city = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    company_address = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    company_contact = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    company_manager = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]

class CompanyPartialUpdateSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(read_only=False, required=False, validators=[datasolve.data_validate])
    company_city = serializers.CharField(read_only=False, required=False, validators=[datasolve.data_validate])
    company_address = serializers.CharField(read_only=False, required=False, validators=[datasolve.data_validate])
    company_contact = serializers.CharField(read_only=False, required=False, validators=[datasolve.data_validate])
    company_manager = serializers.CharField(read_only=False, required=False, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=False, required=False, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]
