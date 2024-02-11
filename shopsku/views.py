from rest_framework import viewsets
from .models import ListModel
from . import serializers
from utils.page import MyPageNumberPagination
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from .filter import Filter
from rest_framework.exceptions import APIException
from .serializers import ShopskuGetSerializer
from rest_framework import permissions
from utils.staff import Staff
from utils.seller_api import SELLER_API
from shop.models import ListModel as ShopModel
from goods.models import ListModel as GoodsModel
from .files import FileRenderCN, FileRenderEN
from rest_framework.settings import api_settings
from django.http import StreamingHttpResponse
from stock.models import StockListModel
from .tasks import stock_manual_update
from celery.result import AsyncResult
from greaterwms.celery import app

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

        partial_update:Partial_update a data（patch：partial_update）

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
            return serializers.ShopskuGetSerializer
        elif self.action in ['create']:
            return serializers.ShopskuPostSerializer
        elif self.action in ['update']:
            return serializers.ShopskuUpdateSerializer
        elif self.action in ['partial_update']:
            return serializers.ShopskuPartialUpdateSerializer
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
        seller_sku_resp = seller_api.get_products({
            'last_id': request.GET.get('last_id', ''),
            'limit': 100
        })
        shopsku_data = [
            ShopskuGetSerializer(instance).data
            for instance in self.get_queryset()
        ]

        new_dict = {}
        for item in shopsku_data:
            id = item['platform_id']
            new_dict[id] = item

        resp_data = {}
        resp_data['previous'] = None
        resp_data['next'] = None
        resp_data['count'] = seller_sku_resp.get('count', 0)
        resp_data['last_id'] = seller_sku_resp.get('last_id', '')
        resp_data['results'] = []
        resp_items = resp_data['results']
        for seller_item in seller_sku_resp.get('items', []):
            item = {}
            seller_product_id = str(seller_item['platform_id'])
            seller_platform_sku = str(seller_item['platform_sku'])
            item['shop_type'] = shop_obj.shop_type
            item['shop_name'] = shop_obj.shop_name
            item['id'] = seller_product_id
            item['platform_id'] = seller_product_id
            item['platform_sku'] = seller_platform_sku
            item['name'] = seller_item['name']
            item['image'] = seller_item['image']
            item['width'] = seller_item['width']
            item['height'] = seller_item['height']
            item['depth'] = seller_item['depth']
            item['weight'] = seller_item['weight']
            item['platform_stock'] = seller_item['stock']
            item['platform_data'] = seller_item['platform_data']
            if seller_product_id in new_dict:
                sys_item = new_dict[seller_product_id]
                item['sys_id'] = sys_item['id']
                item['goods_code'] = sys_item['goods_code']
                item['supplier'] = sys_item['supplier']
                item['creater'] = sys_item['creater']
                item['create_time'] = sys_item['create_time']
                item['update_time'] = sys_item['update_time']
                # get system stock
                sku_stock = StockListModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), goods_code=sys_item['goods_code']).first()
                if sku_stock:
                    item['sys_stock'] = sku_stock.can_order_stock
                else:
                    item['sys_stock'] = 0
            resp_items.append(item)

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
        
        platform_id = data.get('platform_id', '')
        if not platform_id:
            raise APIException({"detail": "The platform id does not exist"})

        goods_code = data.get('goods_code', '')
        if not goods_code:
            raise APIException({"detail": "The goods code does not exist"})

        goods_obj = GoodsModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), goods_supplier=shop_supplier, goods_code=goods_code, is_delete=False).first()
        if goods_obj is None:
            raise APIException({"detail": "The goods does not exist"})

        if ListModel.objects.filter(openid=data['openid'], shop=shop_id, platform_id=platform_id, is_delete=False).exists():
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

        platform_id = data.get('platform_id', '')
        if not platform_id:
            raise APIException({"detail": "The platform id does not exist"})

        goods_code = data.get('goods_code', '')
        if not goods_code:
            raise APIException({"detail": "The goods code does not exist"})

        goods_obj = GoodsModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), goods_supplier=shop_supplier, goods_code=goods_code, is_delete=False).first()
        if goods_obj is None:
            raise APIException({"detail": "The goods does not exist"})

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

        goods_code = data.get('goods_code', '')
        if not goods_code:
            raise APIException({"detail": "The goods code does not exist"})

        goods_obj = GoodsModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), goods_supplier=shop_supplier, goods_code=goods_code, is_delete=False).first()
        if goods_obj is None:
            raise APIException({"detail": "The goods does not exist"})

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

class FileDownloadView(viewsets.ModelViewSet):
    renderer_classes = (FileRenderCN,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ["create_time", "update_time", ]
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
        if self.action in ['list']:
            return serializers.FileRenderSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def get_lang(self, data):
        lang = self.request.META.get('HTTP_LANGUAGE')
        if lang:
            if lang == 'zh-hans':
                return FileRenderCN().render(data)
            else:
                return FileRenderEN().render(data)
        else:
            return FileRenderEN().render(data)

    def list(self, request, *args, **kwargs):
        from datetime import datetime
        dt = datetime.now()
        data = self.get_list(request)
        renderer = self.get_lang(data)
        response = StreamingHttpResponse(
            renderer,
            content_type="text/csv"
        )
        response['Content-Disposition'] = "attachment; filename='shopsku_{}.csv'".format(
            str(dt.strftime('%Y%m%d%H%M%S%f')))
        return response

    def get_list(self, request, *args, **kwargs):
        shop_id = str(request.GET.get('shop_id'))
        if not shop_id:
            raise APIException({"detail": "The shop id does not exist"})
        
        shop_obj = ShopModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), id=shop_id).first()
        if shop_obj is None:
            raise APIException({"detail": "The shop does not exist"})

        seller_api = SELLER_API(shop_id)

        last_id = request.GET.get('last_id', '')
        res = []
        while True:
            seller_sku_resp = seller_api.get_products({
                'last_id': last_id,
                'limit': 100
            })
            shopsku_data = [
                ShopskuGetSerializer(instance).data
                for instance in self.get_queryset()
            ]

            new_dict = {}
            for item in shopsku_data:
                id = item['platform_id']
                new_dict[id] = item

            resp_data = {}
            resp_data['previous'] = None
            resp_data['next'] = None
            resp_data['count'] = seller_sku_resp.get('count', 0)
            resp_data['last_id'] = seller_sku_resp.get('last_id', '')
            resp_data['results'] = []
            resp_items = resp_data['results']
            for seller_item in seller_sku_resp.get('items', []):
                item = {}
                seller_product_id = str(seller_item['platform_id'])
                seller_platform_sku = str(seller_item['platform_sku'])
                item['shop_type'] = shop_obj.shop_type
                item['shop_name'] = shop_obj.shop_name
                item['id'] = seller_product_id
                item['platform_id'] = seller_product_id
                item['platform_sku'] = seller_platform_sku
                item['name'] = seller_item['name']
                item['image'] = seller_item['image']
                item['width'] = seller_item['width']
                item['height'] = seller_item['height']
                item['depth'] = seller_item['depth']
                item['weight'] = seller_item['weight']
                item['platform_stock'] = seller_item['stock']
                if seller_product_id in new_dict:
                    sys_item = new_dict[seller_product_id]
                    item['sys_id'] = sys_item['id']
                    item['goods_code'] = sys_item['goods_code']
                    item['supplier'] = sys_item['supplier']
                    item['creater'] = sys_item['creater']
                    item['create_time'] = sys_item['create_time']
                    item['update_time'] = sys_item['update_time']
                    # get system stock
                    sku_stock = StockListModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), goods_code=sys_item['goods_code']).first()
                    if sku_stock:
                        item['sys_stock'] = sku_stock.can_order_stock
                    else:
                        item['sys_stock'] = 0
                resp_items.append(item)
                res.append(item)
            
            last_id = resp_data['last_id']
            if last_id == '':
                break

        return res

class StockSyncViewSet(viewsets.ModelViewSet):
    """
        retrieve:
            Response a data list（get）

        list:
            Response a data list（all）

        create:
            Create a data line（post）

        delete:
            Delete a data line（delete)

        partial_update:Partial_update a data（patch：partial_update）

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
        if self.action in ['list']:
            return serializers.StockSyncGetSerializer
        elif self.action in ['create']:
            return serializers.StockSyncPostSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def list(self, request, *args, **kwargs):
        shop_id = str(request.GET.get('shop_id'))
        if not shop_id:
            raise APIException({"detail": "The shop id does not exist"})
        
        shop_obj = ShopModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), id=shop_id).first()
        if shop_obj is None:
            raise APIException({"detail": "The shop does not exist"})

        data = super().list(request=request).data
        # add extra info to data here

        return Response(data, status=200)

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

        goods_code = data.get('goods_code', '')
        if not goods_code:
            raise APIException({"detail": "The goods code does not exist"})
        
        if len(goods_code) == 0:
            raise APIException({"detail": "The goods code is empty"})

        # remove duplicate
        goods_code_list = list(set(goods_code))
        goods_obj_list = GoodsModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), goods_supplier=shop_supplier, goods_code__in=goods_code_list, is_delete=False)
        if len(goods_obj_list) == 0:
            raise APIException({"detail": "The goods does not exist"})

        goods_code_list = [item.goods_code for item in goods_obj_list]
        celeryuser = self.request.user
        task_id = stock_manual_update(goods_code_list, celeryuser)

        return Response(task_id, status=200)

    def retrieve(self, request, pk):
        res = AsyncResult(pk, app=app)
        return Response(res.state, status=200)
