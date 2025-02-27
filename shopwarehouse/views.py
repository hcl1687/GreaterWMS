from rest_framework import viewsets
from .models import ListModel
from . import serializers
from utils.page import MyPageNumberPagination
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from .filter import Filter
from rest_framework.exceptions import APIException
from .serializers import ShopwarehouseGetSerializer
from rest_framework import permissions
from utils.staff import Staff
from utils.seller_api import SELLER_API
from shop.models import ListModel as ShopModel
from warehouse.models import ListModel as WarehouseModel

class APIViewSet(viewsets.ModelViewSet):
    """
        retrieve:
            Response a data list（get）

        list:
            Response a data list（all）

        create:
            Create a data line（post）

        delete:
            Delete a data line（delete)

        partial_update:
            Partial_update a data（patch：partial_update）

        update:
            Update a data（put：update）
    """
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = Filter
    permission_classes = (permissions.DjangoModelPermissions,)

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        shop_id = str(self.request.GET.get('shop_id') or self.request.data.get('shop'))
        if self.request.user:
            supplier_name = Staff.get_supplier_name(self.request.user)
            if supplier_name:
                if id is None:
                    return ListModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), supplier=supplier_name, shop_id=shop_id, is_delete=False)
                else:
                    return ListModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), supplier=supplier_name, id=id, is_delete=False)
            else:
                if id is None:
                    return ListModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), shop_id=shop_id, is_delete=False)
                else:
                    return ListModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), id=id, is_delete=False)
        else:
            return ListModel.objects.none()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve', 'destroy']:
            return serializers.ShopwarehouseGetSerializer
        elif self.action in ['create']:
            return serializers.ShopwarehousePostSerializer
        elif self.action in ['update']:
            return serializers.ShopwarehouseUpdateSerializer
        elif self.action in ['partial_update']:
            return serializers.ShopwarehousePartialUpdateSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def list(self, request, *args, **kwargs):
        shop_id = str(request.GET.get('shop_id'))
        if not shop_id:
            raise APIException({"detail": "The shop id does not exist"})
        
        shop_obj = ShopModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), id=shop_id).first()
        if shop_obj is None:
            raise APIException({"detail": "The shop does not exist"})

        seller_api = SELLER_API(shop_id)
        seller_warehouse_list = seller_api.get_warehouses()
        shopwarehouse_data = [
            ShopwarehouseGetSerializer(instance).data
            for instance in self.get_queryset()
        ]

        new_dict = {}
        for item in shopwarehouse_data:
            id = item['platform_id']
            new_dict[id] = item

        resp_data = []
        for seller_item in seller_warehouse_list.get('result', []):
            seller_warehouse_id = str(seller_item['warehouse_id'])
            resp_item = {}
            resp_item['id'] = seller_warehouse_id
            resp_item['name'] = seller_item['name']
            if seller_warehouse_id in new_dict:
                sys_item = new_dict[seller_warehouse_id]
                resp_item['sys_id'] = sys_item['id']
                resp_item['sys_warehouse_id'] = sys_item['warehouse']['id']
                resp_item['sys_name'] = sys_item['warehouse']['warehouse_name']
            resp_data.append(resp_item)

        return Response(resp_data, status=200)

    def create(self, request, *args, **kwargs):
        data = self.request.data
        data['openid'] = self.request.META.get('HTTP_TOKEN')

        shop_id = data.get('shop', '')
        if not shop_id:
            raise APIException({"detail": "The shop id does not exist"})
        
        shop_obj = ShopModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), id=shop_id, is_delete=False).first()
        if shop_obj is None:
            raise APIException({"detail": "The shop does not exist"})

        shop_supplier = shop_obj.supplier
        supplier_name = Staff.get_supplier_name(self.request.user)
        if supplier_name and shop_supplier != supplier_name:
            raise APIException({"detail": "The shop is not belong to your supplier"})

        warehouse_id = data.get('warehouse', '')
        if not warehouse_id:
            raise APIException({"detail": "The warehouse id does not exist"})

        warehouse_obj = WarehouseModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), id=warehouse_id, is_delete=False).first()
        if warehouse_obj is None:
            raise APIException({"detail": "The warehouse does not exist"})

        if ListModel.objects.filter(openid=data['openid'], shop=shop_id, platform_id=data['platform_id'], is_delete=False).exists():
            raise APIException({"detail": "Data exists"})
        else:
            data['supplier'] = shop_supplier
            data['creater'] = self.request.user.username
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=200, headers=headers)

    def update(self, request, pk):
        qs = self.get_object()
        data = self.request.data

        shop_id = data.get('shop', '')
        if not shop_id:
            raise APIException({"detail": "The shop id does not exist"})
        
        shop_obj = ShopModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), id=shop_id, is_delete=False).first()
        if shop_obj is None:
            raise APIException({"detail": "The shop does not exist"})

        shop_supplier = shop_obj.supplier
        supplier_name = Staff.get_supplier_name(self.request.user)
        if supplier_name and shop_supplier != supplier_name:
            raise APIException({"detail": "The shop is not belong to your supplier"})

        warehouse_id = data.get('warehouse', '')
        if not warehouse_id:
            raise APIException({"detail": "The warehouse id does not exist"})

        warehouse_obj = WarehouseModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), id=warehouse_id, is_delete=False).first()
        if warehouse_obj is None:
            raise APIException({"detail": "The warehouse does not exist"})

        serializer = self.get_serializer(qs, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=200, headers=headers)

    def partial_update(self, request, pk):
        qs = self.get_object()
        data = self.request.data

        shop_id = data.get('shop', '')
        if shop_id:
            shop_obj = ShopModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), id=shop_id, is_delete=False).first()
            if shop_obj is None:
                raise APIException({"detail": "The shop does not exist"})
            shop_supplier = shop_obj.supplier
            supplier_name = Staff.get_supplier_name(self.request.user)
            if supplier_name and shop_supplier != supplier_name:
                raise APIException({"detail": "The shop is not belong to your supplier"})

        warehouse_id = data.get('warehouse', '')
        if warehouse_id:
            warehouse_obj = WarehouseModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), id=warehouse_id, is_delete=False).first()
            if warehouse_obj is None:
                raise APIException({"detail": "The warehouse does not exist"})

        data = self.request.data
        serializer = self.get_serializer(qs, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=200, headers=headers)

    def destroy(self, request, pk):
        qs = self.get_object()
        supplier_name = Staff.get_supplier_name(self.request.user)
        if qs.openid != self.request.META.get('HTTP_TOKEN'):
            raise APIException({"detail": "Cannot Delete Data Which Not Yours"})
        elif supplier_name and supplier_name != qs.supplier:
            raise APIException({"detail": "Cannot Delete Data Which Not Yours"})
        else:
            qs.is_delete = True
            qs.save()
            serializer = self.get_serializer(qs, many=False)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=200, headers=headers)
