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
from shop.models import ListModel as ShopModel
from goods.models import ListModel as GoodsModel
from .files import FileRenderCN, FileRenderEN
from rest_framework.settings import api_settings
from django.http import StreamingHttpResponse
from shopwarehouse.models import ListModel as ShopwarehouseModal
import json
from shopsku.models import ListModel as ShopskuModel
from stock.models import StockListModel, StockBinModel
from django.conf import settings
from dateutil import parser
import requests
import copy
from utils.seller_api import SELLER_API
from .status import Status, Handle_Status
from datetime import datetime

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

    def list(self, request, *args, **kwargs):
        data = super().list(request=request).data
        # add extra info to data here
        return Response(data, status=200)

    def create(self, request, *args, **kwargs):
        data = self.request.data
        original_data = copy.deepcopy(data)
        data['openid'] = self.request.META.get('HTTP_TOKEN')

        # data['order_time'] is timestamp
        try:
            data['order_time'] = datetime.fromtimestamp(data['order_time'])
        except Exception:
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
        is_exists = ListModel.objects.filter(openid=data['openid'], shop_id=shop_id, platform_id=platform_id, is_delete=False).exists()
        # status: 1: awaiting_packaging; 2: awaiting_deliver; 3: delivering; 4: cancelled; 5: delivered;
        status = data.get('status')
        if is_exists:
            # raise APIException({"detail": "Data exists"})
            return Response({"detail": "Data exists"}, status=200)
        elif status != Status.Awaiting_Review and status != Status.Awaiting_Deliver:
            return Response({"detail": "Not awaiting_packaging or awaiting_deliver data"}, status=200)
        else:
            data['supplier'] = shop_supplier
            data['creater'] = self.request.user.username
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)

            try:
                self.handle_awaiting_packing(data, shop_id, shop_supplier)
            except APIException as e:
                data['handle_status'] = Handle_Status.Abnormal
                data['handle_message'] = e.detail['detail']
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            if status == 2:
                # handle awaiting_deliver data
                url = f'{settings.INNER_URL}/shoporder/{serializer.data["id"]}/'
                req_data = original_data
                headers = {
                    'Authorization': self.request.headers['Authorization'],
                    'Token': self.request.META.get('HTTP_TOKEN'),
                }

                try:
                    response = requests.put(url, json=req_data, headers=headers)
                    if response.status_code != 200:
                        # response.content: { status_code: 5xx, detial: 'xxx' }
                        json_response = json.loads(response.get('content'))
                        print(json_response.content.decode('UTF-8'))
                except Exception as e:
                    print(e)
                    raise APIException({"detail": f'Handle awaiting_deliver data failed after holding stock'})
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=200, headers=headers)

    def update(self, request, pk):
        qs = self.get_object()
        if qs.openid != self.request.META.get('HTTP_TOKEN'):
            raise APIException({"detail": "Cannot update data which not yours"})
        
        if qs.status != Status.Awaiting_Review:
            raise APIException({"detail": "This Shop order does not in Awaiting Review Status"})

        data = self.request.data
        data['openid'] = self.request.META.get('HTTP_TOKEN')

        # data['order_time'] is timestamp
        try:
            data['order_time'] = datetime.fromtimestamp(data['order_time'])
        except Exception:
            raise APIException({"detail": "order_time parse error"})

        shop_obj = qs.shop
        shop_id = shop_obj.id
        if shop_obj is None:
            raise APIException({"detail": "The shop does not exist"})
        
        platform_warehouse_id = data.get('platform_warehouse_id', '')
        if not platform_warehouse_id:
            raise APIException({"detail": "The platform_warehouse_id does not exist"})

        platform_warehouse_obj = ShopwarehouseModal.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), shop_id=shop_id, platform_id=platform_warehouse_id, is_delete=False).first()
        if platform_warehouse_obj is None:
            raise APIException({"detail": "The platform warehouse does not exist"})

        shop_supplier = qs.supplier
        supplier_name = Staff.get_supplier_name(self.request.user)
        if supplier_name and shop_supplier != supplier_name:
            raise APIException({"detail": "The shop is not belong to your supplier"})
        
        # status: 1: awaiting_packaging; 2: awaiting_deliver; 3: delivering; 4: cancelled; 5: delivered;
        status = data.get('status', Status.Awaiting_Review)
        if status == Status.Awaiting_Deliver:
            try:
                self.handle_awaiting_deliver(data, shop_id, shop_supplier)
            except APIException as e:
                print(e)
                data['handle_status'] = Handle_Status.Abnormal
                data['handle_message'] = e.detail['detail']
        elif status == Status.Delivering:
            pass
        elif status == Status.Cancelled:
            pass
        else:
            return Response({"detail": "Not awaiting_deliver or delivering or cancelled data"}, status=200)

        serializer = self.get_serializer(qs, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=200, headers=headers)

    def partial_update(self, request, pk):
        qs = self.get_object()
        if qs.openid != self.request.META.get('HTTP_TOKEN'):
            raise APIException({"detail": "Cannot partial_update data which not yours"})

        data = self.request.data
        data['openid'] = self.request.META.get('HTTP_TOKEN')

        shop_obj = qs.shop
        shop_id = shop_obj.id
        if shop_obj is None:
            raise APIException({"detail": "The shop does not exist"})

        shop_supplier = qs.supplier
        supplier_name = Staff.get_supplier_name(self.request.user)
        if supplier_name and shop_supplier != supplier_name:
            raise APIException({"detail": "The shop is not belong to your supplier"})

        # status: 1: awaiting_packaging; 2: awaiting_deliver; 3: delivering; 4: cancelled; 5: delivered;
        status = int(data.get('status', 1))
        if status == 5:
            try:
                self.handle_delivered(data, shop_id, shop_supplier)
            except APIException as e:
                data['handle_status'] = Handle_Status.Abnormal
                data['handle_message'] = e.detail['detail']
        else:
            return Response({"detail": "Not delivered data"}, status=200)

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
    
    def handle_awaiting_packing(self, data, shop_id, shop_supplier):
        # hold stock
        try:
            order_products = json.loads(data.get('order_products', ''))
        except json.JSONDecodeError:
            raise APIException({"detail": "order_products decode error"})

        # search goods_code
        # check all products have stock
        # collect available binset
        stockbin_data = []
        products_goods_code = []
        for item in order_products:
            sku = item['sku']
            shopsku_obj = ShopskuModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), shop_id=shop_id, supplier=shop_supplier, platform_sku=sku, is_delete=False).first()
            if shopsku_obj is None:
                raise APIException({"detail": "No goods_code for {}".format(sku)})

            goods_code = shopsku_obj.goods_code
            item['goods_code'] = goods_code
            products_goods_code.append(goods_code)
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
                            'sku': sku,
                            'goods_code': goods_code,
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
        for i in range(len(order_products)):
            item = order_products[i]
            stockbin_data_item = stockbin_data[i]
            product_goods_code = products_goods_code[i]
            url = f'{settings.INNER_URL}/stock/bin/{stockbin_data_item["source_id"]}/'
            req_data = {
                'bin_name': stockbin_data_item['source_bin_name'],
                'move_to_bin': settings.DEFAULT_HOLDING_BIN,
                'goods_code': product_goods_code,
                'move_qty': int(item['quantity'])
            }
            headers = {
                'Authorization': self.request.headers['Authorization'],
                'Token': self.request.META.get('HTTP_TOKEN'),
            }

            try:
                response = requests.post(url, json=req_data, headers=headers)
                json_response = json.loads(response.content)
                stockbin_data_item['target_id'] = json_response['stockbin_id']
                stockbin_data_item['target_bin_name'] = json_response['stockbin_bin_name']
            except Exception as e:
                print(e)
                raise APIException({"detail": f'Cannot move bin from: {stockbin_data_item["source_id"]} to {settings.DEFAULT_HOLDING_BIN}'})

        data['stockbin_data'] = json.dumps(stockbin_data)
        return data

    def handle_awaiting_deliver(self, data, shop_id, shop_supplier):
        # create DN
        try:
            order_products = json.loads(data.get('order_products', ''))
        except json.JSONDecodeError:
            raise APIException({"detail": "order_products decode error"})

        # collect goods_code and goods_qty
        goods_codes = []
        goods_qty = []
        for item in order_products:
            sku = item['sku']
            quantity = int(item['quantity'])
            shopsku_obj = ShopskuModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), shop_id=shop_id, supplier=shop_supplier, platform_sku=sku, is_delete=False).first()
            if shopsku_obj is None:
                raise APIException({"detail": "No goods_code for {}".format(sku)})

            goods_code = shopsku_obj.goods_code
            goods_codes.append(goods_code)
            goods_qty.append(quantity)

        # create DN
        url = f'{settings.INNER_URL}/dn/list/'
        req_data = {
            'creater': self.request.user.username,
        }
        headers = {
            'Authorization': self.request.headers['Authorization'],
            'Token': self.request.META.get('HTTP_TOKEN'),
        }
        try:
            response = requests.post(url, json=req_data, headers=headers)
            json_response = json.loads(response.content)
            dn_code = json_response['dn_code']
        except Exception as e:
            print(e)
            raise APIException({"detail": f'Cannot create dn list'})

        # create DN detail
        url = f'{settings.INNER_URL}/dn/detail/'
        req_data = {
            'creater': self.request.user.username,
            'customer': '-',
            'dn_code': dn_code,
            'goods_code': goods_codes,
            'goods_qty': goods_qty
        }
        headers = {
            'Authorization': self.request.headers['Authorization'],
            'Token': self.request.META.get('HTTP_TOKEN'),
            'Operator': str(self.request.user.id)
        }
        try:
            response = requests.post(url, json=req_data, headers=headers)
            if response.status_code != 200:
                # response.content: { status_code: 5xx, detial: 'xxx' }
                json_response = json.loads(response.get('content'))
                print(json_response.content.decode('UTF-8'))
        except Exception as e:
            print(e)
            raise APIException({"detail": f'Cannot create dn detail'})

        data['dn_code'] = dn_code
        return data

    def handle_delivering(data, shop_id, shop_supplier):
        return data

    def handle_delivered(data, shop_id, shop_supplier):
        return data

class ShoporderInitViewSet(viewsets.ModelViewSet):
    """
        retrieve:
            Response a data list（get）
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
        if self.action in ['create']:
            return serializers.ShoporderPartialUpdateSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, *args, **kwargs):
        data = self.request.data
        # timestamp
        since = data.get('since')
        # timestamp
        to = data.get('to')

        shop_list = ShopModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), is_delete=False)

        # init Awaiting_Review order
        for shop in shop_list:
            status = Status.Awaiting_Review
            shop_id = shop.id
            self.handle_shoporder(shop_id, since=since, to=to, status=status)
        # init Awaiting_Deliver order
        for shop in shop_list:
            status = Status.Awaiting_Deliver
            shop_id = shop.id
            self.handle_shoporder(shop_id, since=since, to=to, status=status)

        return Response({"detail": "success"}, status=200)

    def handle_shoporder(self, shop_id, **args):
        seller_api = SELLER_API(shop_id)
        offset = 0
        while True:
            params = {
                'offset': offset,
                'status':args['status'],
                'since': args['since'],
                'to': args['to']
            }
            seller_resp = seller_api.get_orders(params)
            for item in seller_resp.get('items', []):
                item['shop'] = shop_id
                url = f'{settings.INNER_URL}/shoporder/'
                req_data = item
                headers = {
                    'Authorization': self.request.headers['Authorization'],
                    'Token': self.request.META.get('HTTP_TOKEN'),
                }

                try:
                    response = requests.post(url, json=req_data, headers=headers)
                    if response.status_code != 200:
                        # response.content: { status_code: 5xx, detial: 'xxx' }
                        json_response = json.loads(response.get('content'))
                        print(json_response.content.decode('UTF-8'))
                except Exception as e:
                    print(e)
                    print(f'init Awaiting_Review order failed')

            if seller_resp is None:
                break
            if not seller_resp.get('has_next', False):
                break
            offset = seller_resp['next']

class ShoporderUpdateViewSet(viewsets.ModelViewSet):
    """
        retrieve:
            Response a data list（get）
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
        if self.action in ['create']:
            return serializers.ShoporderPartialUpdateSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, *args, **kwargs):
        data = self.request.data
        # timestamp
        since = data.get('since')
        # timestamp
        to = data.get('to')

        shop_list = ShopModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), is_delete=False)

        # update Awaiting_Deliver order
        for shop in shop_list:
            status = Status.Awaiting_Deliver
            shop_id = shop.id
            self.handle_shoporder(shop_id, since=since, to=to, status=status)
        # init Delivering order
        for shop in shop_list:
            status = Status.Delivering
            shop_id = shop.id
            self.handle_shoporder(shop_id, since=since, to=to, status=status)
        # init Cancelled order
        for shop in shop_list:
            status = Status.Cancelled
            shop_id = shop.id
            self.handle_shoporder(shop_id, since=since, to=to, status=status)

        return Response({"detail": "success"}, status=200)

    def handle_shoporder(self, shop_id, **args):
        seller_api = SELLER_API(shop_id)
        offset = 0
        while True:
            params = {
                'offset': offset,
                'status':args['status'],
                'since': args['since'],
                'to': args['to']
            }
            seller_resp = seller_api.get_orders(params)
            for item in seller_resp.get('items', []):
                item['shop'] = shop_id
                url = f'{settings.INNER_URL}/shoporder/'
                req_data = item
                headers = {
                    'Authorization': self.request.headers['Authorization'],
                    'Token': self.request.META.get('HTTP_TOKEN'),
                }

                try:
                    response = requests.put(url, json=req_data, headers=headers)
                    if response.status_code != 200:
                        # response.content: { status_code: 5xx, detial: 'xxx' }
                        json_response = json.loads(response.get('content'))
                        print(json_response.content.decode('UTF-8'))
                except Exception as e:
                    print(e)
                    print(f'update Awaiting_Review order failed')

            if seller_resp is None:
                break
            if not seller_resp.get('has_next', False):
                break
            offset = seller_resp['next']

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
