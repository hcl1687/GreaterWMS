from rest_framework import viewsets
from .models import ListModel
from . import serializers
from utils.page import MyPageNumberPagination
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from .filter import Filter
from rest_framework.exceptions import APIException
from .serializers import FileRenderSerializer
from rest_framework import permissions
from utils.staff import Staff
from utils.seller_api import SELLER_API
from shop.models import ListModel as ShopModel
from goods.models import ListModel as GoodsModel
from .files import FileRenderCN, FileRenderEN
from rest_framework.settings import api_settings
from django.http import StreamingHttpResponse
from shopwarehouse.models import ListModel as ShopwarehouseModal
import json
from shopsku.models import ListModel as ShopskuModel
from stock.models import StockListModel, StockBinModel
from rest_framework.request import Request as DRFRequest
from django.conf import settings
from django.http import HttpRequest
from stock.views import StockBinViewSet
from dateutil import parser

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
        if self.request.user:
            supplier_name = Staff.get_supplier_name(self.request.user)
            if supplier_name:
                if id is None:
                    return ListModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), supplier=supplier_name, is_delete=False)
                else:
                    return ListModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), supplier=supplier_name, id=id, is_delete=False)
            else:
                if id is None:
                    return ListModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), is_delete=False)
                else:
                    return ListModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), id=id, is_delete=False)
        else:
            return ListModel.objects.none()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve', 'destroy']:
            return serializers.ShoporderGetSerializer
        elif self.action in ['create']:
            return serializers.ShoporderPostSerializer
        elif self.action in ['update']:
            return serializers.ShoporderUpdateSerializer
        elif self.action in ['partial_update']:
            return serializers.ShoporderPartialUpdateSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, *args, **kwargs):
        data = self.request.data
        data['openid'] = self.request.META.get('HTTP_TOKEN')

        try:
            data['order_time'] = parser.parse(data['order_time'])
        except parser.ParserError:
            raise APIException({"detail": "order_time parse error"})

        shop_id = data.get('shop', '')
        if not shop_id:
            raise APIException({"detail": "The shop id does not exist"})
        
        shop_obj = ShopModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), id=shop_id, is_delete=False).first()
        if shop_obj is None:
            raise APIException({"detail": "The shop does not exist"})
        
        platform_warehouse_id = data.get('platform_warehouse_id', '')
        if not platform_warehouse_id:
            raise APIException({"detail": "The platform_warehouse_id does not exist"})

        platform_warehouse_obj = ShopwarehouseModal.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), shop_id=shop_id, platform_id=platform_warehouse_id, is_delete=False).first()
        if platform_warehouse_obj is None:
            raise APIException({"detail": "The platform warehouse does not exist"})

        shop_supplier = shop_obj.supplier
        supplier_name = Staff.get_supplier_name(self.request.user)
        if supplier_name and shop_supplier != supplier_name:
            raise APIException({"detail": "The shop is not belong to your supplier"})

        platform_id = data.get('platform_id', '')
        if ListModel.objects.filter(openid=data['openid'], shop_id=shop_id, platform_id=platform_id, is_delete=False).exists():
            raise APIException({"detail": "Data exists"})
        else:
            data['supplier'] = shop_supplier
            data['creater'] = self.request.user.username
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)

            # lock stock
            try:
                order_data = json.loads(data.get('order_data', ''))
            except json.JSONDecodeError:
                raise APIException({"detail": "order_data decode error"})

            # search goods_code
            # check all products have stock
            # collect available binset
            stockbin_data = []
            for item in order_data.get('products', []):
                sku = item['sku']
                shopsku_obj = ShopskuModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), shop_id=shop_id, supplier=shop_supplier, platform_sku=sku, is_delete=False).first()
                if shopsku_obj is None:
                    raise APIException({"detail": "No goods_code for {}".format(sku)})

                goods_code = shopsku_obj.goods_code
                # chedk stock
                goods_qty_change = StockListModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'),
                                                            goods_code=goods_code).first()
                if goods_qty_change is None:
                    raise APIException({"detail": "No stock for {}".format(sku)})
                if goods_qty_change.can_order_stock < int(item['quantity']):
                    raise APIException({"detail": "No enough stock for {}".format(sku)})
                
                # find available stock bin
                goods_bin_stock_list = StockBinModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'),
                                                               goods_code=goods_code,
                                                               bin_property="Normal").order_by('id')
                can_pick_qty = goods_qty_change.onhand_stock - \
                                   goods_qty_change.inspect_stock - \
                                   goods_qty_change.hold_stock - \
                                   goods_qty_change.damage_stock - \
                                   goods_qty_change.pick_stock
                if can_pick_qty > 0 and int(item['quantity']) <= can_pick_qty:
                    has_bin = False
                    for j in range(len(goods_bin_stock_list)):
                        bin_can_pick_qty = goods_bin_stock_list[j].goods_qty - \
                                                   goods_bin_stock_list[j].pick_qty
                        if bin_can_pick_qty > 0 and  int(item['quantity']) <= bin_can_pick_qty:
                            stockbin_data_item = {
                                'source_id': goods_bin_stock_list[j].id,
                                'source_bin_name': goods_bin_stock_list[j].bin_name
                            }
                            stockbin_data.append(stockbin_data_item)
                            has_bin = True
                            break
                    if not has_bin:
                        raise APIException({"detail": "No enough pick stock in a bin for {}".format(sku)})
                else:
                    raise APIException({"detail": "No enough pick stock for {}".format(sku)})

            # move to hold binset
            for i in range(len(order_data.get('products', []))):
                item = order_data.get('products', [])[i]
                stockbin_data_item = stockbin_data[i]
                request = HttpRequest()
                request.method = 'POST'
                request.path = 'stock/bin/{}/'.format(stockbin_data_item['source_id'])
                request._body = json.dumps({
                    'bin_name': stockbin_data_item['source_bin_name'],
                    'move_to_bin': 'BSH1',
                    'goods_code': goods_code,
                    'move_qty': int(item['quantity'])
                })
                request.META = {
                    'SERVER_NAME': settings.INNER_URL[0],
                    'SERVER_PORT': settings.INNER_URL[1],
                    'CONTENT_TYPE': 'application/json',
                    'HTTP_TOKEN': self.request.META.get('HTTP_TOKEN')
                }
                request.user = self.request.user

                try:
                    print('tttttt0.0')
                    view = StockBinViewSet.as_view({
                        'post': 'create'
                    })
                    pk = stockbin_data_item['source_id']
                    print('tttttt0')
                    print(request.path)
                    response = view(request, pk).render()
                    print('tttttt1')
                    print(response.content)
                    json_response = json.loads(response.content)
                    stockbin_data_item['target_id'] = json_response.stockbin_id
                    stockbin_data_item['target_bin_name'] = json_response.stockbin_bin_name
                except Exception as e:
                    print('tttttt')
                    print(e)
                    raise APIException({"detail": f'Cannot move bin from: {stockbin_data_item["source_id"]} to BSH1'})

            data['stockbin_data'] = json.dumps(stockbin_data)
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
        data = (
            FileRenderSerializer(instance).data
            for instance in self.filter_queryset(self.get_queryset())
        )
        renderer = self.get_lang(data)
        response = StreamingHttpResponse(
            renderer,
            content_type="text/csv"
        )
        response['Content-Disposition'] = "attachment; filename='shopsku_{}.csv'".format(
            str(dt.strftime('%Y%m%d%H%M%S%f')))
        return response
