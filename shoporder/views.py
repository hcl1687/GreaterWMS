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
from .files import FileRenderCN, FileRenderEN
from rest_framework.settings import api_settings
from django.http import StreamingHttpResponse
from shopwarehouse.models import ListModel as ShopwarehouseModel
import json
from shopsku.models import ListModel as ShopskuModel
from stock.models import StockListModel, StockBinModel
from django.conf import settings
import requests
import copy
from utils.seller_api import SELLER_API
from .status import Status, Handle_Status
from dn.models import DnListModel
import logging
import time

logger = logging.getLogger(__name__)

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
        for item in data['results']:
            dn_code = item['dn_code']
            if dn_code:
                dn_obj = DnListModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), dn_code=dn_code, is_delete=False).first()
                if dn_obj:
                    total_weight = dn_obj.total_weight
                    item['total_weight'] = total_weight
                    item['dn_status'] = dn_obj.dn_status

            shop_id = item['shop']['id']
            warehouse_id = item['platform_warehouse_id']
            platform_warehouse_obj = ShopwarehouseModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), shop_id=shop_id, platform_id=warehouse_id, is_delete=False).first()
            if platform_warehouse_obj:
                item['platform_warehouse_name'] = platform_warehouse_obj.platform_name

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
        
        platform_warehouse_id = data.get('platform_warehouse_id', '')
        if not platform_warehouse_id:
            raise APIException({"detail": "The platform_warehouse_id does not exist"})

        platform_warehouse_obj = ShopwarehouseModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), shop_id=shop_id, platform_id=platform_warehouse_id, is_delete=False).first()
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
            raise APIException({"detail": "Not awaiting_packaging or awaiting_deliver data"})
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

            data['status'] = Status.Awaiting_Review
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=200, headers=headers)

    def update(self, request, pk):
        qs = self.get_object()
        if qs.openid != self.request.META.get('HTTP_TOKEN'):
            raise APIException({"detail": "Cannot update data which not yours"})
        
        if qs.handle_status != Handle_Status.Normal:
            raise APIException({"detail": "This Shop order is abnormal"})

        data = self.request.data
        data['openid'] = self.request.META.get('HTTP_TOKEN')

        shop_obj = qs.shop
        shop_id = shop_obj.id
        if shop_obj is None:
            raise APIException({"detail": "The shop does not exist"})

        platform_warehouse_id = data.get('platform_warehouse_id', '')
        if not platform_warehouse_id:
            raise APIException({"detail": "The platform_warehouse_id does not exist"})

        platform_warehouse_obj = ShopwarehouseModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), shop_id=shop_id, platform_id=platform_warehouse_id, is_delete=False).first()
        if platform_warehouse_obj is None:
            raise APIException({"detail": "The platform warehouse does not exist"})

        shop_supplier = qs.supplier
        supplier_name = Staff.get_supplier_name(self.request.user)
        if supplier_name and shop_supplier != supplier_name:
            raise APIException({"detail": "The shop is not belong to your supplier"})
        
        # status: 1: awaiting_packaging; 2: awaiting_deliver; 3: delivering; 4: cancelled; 5: delivered;
        status = data.get('status', Status.Awaiting_Review)
        need_update_handle_status = False
        if status == Status.Awaiting_Deliver:
            if qs.status != Status.Awaiting_Review:
                logger.info(f'This Shop order does not in Awaiting Review Status for shop_id: {shop_id}, platform_id: {qs.platform_id}')
                return Response({"detail": "This Shop order does not in Awaiting Review Status"}, status=200)
            try:
                self.handle_awaiting_deliver(data, shop_id, shop_supplier, qs)
            except APIException as e:
                logger.error(str(e))
                need_update_handle_status = True
                data['handle_status'] = Handle_Status.Abnormal
                data['handle_message'] = e.detail['detail']
        elif status == Status.Delivering:
            try:
                self.handle_delivering(data, shop_id, shop_supplier, qs)
            except APIException as e:
                logger.error(str(e))
                need_update_handle_status = True
                data['handle_status'] = Handle_Status.Abnormal
                data['handle_message'] = e.detail['detail']
        elif status == Status.Delivered:
            try:
                self.handle_delivered(data, shop_id, shop_supplier, qs)
            except APIException as e:
                logger.error(str(e))
                need_update_handle_status = True
                data['handle_status'] = Handle_Status.Abnormal
                data['handle_message'] = e.detail['detail']
        elif status == Status.Cancelled:
            try:
                self.handle_cancelled(data, shop_id, shop_supplier, qs)
            except APIException as e:
                logger.error(str(e))
                need_update_handle_status = True
                data['handle_status'] = Handle_Status.Abnormal
                data['handle_message'] = e.detail['detail']
        else:
            return Response({"detail": "Not awaiting_deliver or delivering or cancelled data"}, status=200)

        if need_update_handle_status:
            qs.refresh_from_db()
            serializer = self.get_serializer(qs, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return Response(data, status=200)

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
            products_goods_code.append(goods_code)
            # check stock
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

            response = requests.post(url, json=req_data, headers=headers)
            str_response = response.content.decode('UTF-8')
            json_response = json.loads(str_response)
            json_response_status = json_response.get('status_code')
            if response.status_code != 200 or (json_response_status and json_response_status != 200):
                # response.content: { status_code: 5xx, detial: 'xxx' }
                logger.info(f'Cannot move bin from: {stockbin_data_item["source_id"]} to {settings.DEFAULT_HOLDING_BIN}, response: {str_response}')
                raise APIException({"detail": f'Cannot move bin from: {stockbin_data_item["source_id"]} to {settings.DEFAULT_HOLDING_BIN}'})

            stockbin_data_item['target_id'] = json_response['stockbin_id']
            stockbin_data_item['target_bin_name'] = json_response['stockbin_bin_name']

        data['stockbin_data'] = json.dumps(stockbin_data)

    def handle_awaiting_deliver(self, data, shop_id, shop_supplier, qs):
        # create DN
        try:
            order_products = json.loads(qs.order_products)
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
            'Operator': self.request.META.get('HTTP_OPERATOR')
        }

        response = requests.post(url, json=req_data, headers=headers)
        str_response = response.content.decode('UTF-8')
        json_response = json.loads(str_response)
        json_response_status = json_response.get('status_code')
        if response.status_code != 200 or (json_response_status and json_response_status != 200):
            # response.content: { status_code: 5xx, detial: 'xxx' }
            logger.info(f'Cannot create dn list, response: {str_response}')
            raise APIException({"detail": f'Cannot create dn list'})
        dn_code = json_response['dn_code']
        dn_id = json_response['id']

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
            'Operator': self.request.META.get('HTTP_OPERATOR')
        }

        response = requests.post(url, json=req_data, headers=headers)
        str_response = response.content.decode('UTF-8')
        json_response = json.loads(str_response)
        if response.status_code != 200 or (json_response_status and json_response_status != 200):
            # response.content: { status_code: 5xx, detial: 'xxx' }
            logger.info(f'Cannot create dn detail, response: {str_response}')
            raise APIException({"detail": f'Cannot create dn detail'})

        # save order first
        qs.refresh_from_db()
        qs.dn_code = dn_code
        qs.status = Status.Awaiting_Deliver
        qs.save()

        # confirm order
        url = f'{settings.INNER_URL}/dn/neworder/{dn_id}/'
        req_data = {}
        headers = {
            'Authorization': self.request.headers['Authorization'],
            'Token': self.request.META.get('HTTP_TOKEN'),
            'Operator': self.request.META.get('HTTP_OPERATOR')
        }

        response = requests.post(url, json=req_data, headers=headers)
        str_response = response.content.decode('UTF-8')
        json_response = json.loads(str_response)
        if response.status_code != 200 or (json_response_status and json_response_status != 200):
            # response.content: { status_code: 5xx, detial: 'xxx' }
            logger.info(f'Cannot confirm dn: {dn_code}, response: {str_response}')
            raise APIException({"detail": f'Cannot confirm dn: {dn_code}'})

        # generate pick order
        url = f'{settings.INNER_URL}/dn/orderrelease/{dn_id}/'
        req_data = {}
        headers = {
            'Authorization': self.request.headers['Authorization'],
            'Token': self.request.META.get('HTTP_TOKEN'),
            'Operator': self.request.META.get('HTTP_OPERATOR')
        }

        response = requests.put(url, json=req_data, headers=headers)
        str_response = response.content.decode('UTF-8')
        json_response = json.loads(str_response)
        if response.status_code != 200 or (json_response_status and json_response_status != 200):
            # response.content: { status_code: 5xx, detial: 'xxx' }
            logger.info(f'Cannot generate pick order for dn: {dn_code}, response: {str_response}')
            raise APIException({"detail": f'Cannot generate pick order for dn: {dn_code}'})

    def handle_delivering(self, data, shop_id, shop_supplier, qs):
        qs.status = Status.Delivering
        qs.save()

    def handle_delivered(self, data, shop_id, shop_supplier, qs):
        qs.status = Status.Delivered
        qs.save()

    def handle_cancelled(self, data, shop_id, shop_supplier, qs):
        if qs.status == Status.Awaiting_Review:
            # delete holding bin
            shoporder_obj = qs
            if shoporder_obj:
                try:
                    stockbin_data = json.loads(shoporder_obj.stockbin_data)
                except json.JSONDecodeError:
                    raise APIException({"detail": "stockbin_data decode error"})

            for stockbin_data_item in stockbin_data:
                # Todo: If this dn has platform order, move holding bin to normal bin
                # get hold stock bin
                hold_stockbin_obj = StockBinModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'),
                                                    id=stockbin_data_item['target_id']).first()
                # move holding stock to normal bin
                url = f'{settings.INNER_URL}/stock/bin/{stockbin_data_item["target_id"]}/'
                req_data = {
                    'bin_name': stockbin_data_item['target_bin_name'],
                    'move_to_bin': stockbin_data_item['source_bin_name'],
                    'goods_code': hold_stockbin_obj.goods_code,
                    'move_qty': hold_stockbin_obj.goods_qty
                }
                headers = {
                    'Authorization': self.request.headers['Authorization'],
                    'Token': self.request.META.get('HTTP_TOKEN'),
                }

                response = requests.post(url, json=req_data, headers=headers)
                str_response = response.content.decode('UTF-8')
                json_response = json.loads(str_response)
                json_response_status = json_response.get('status_code')
                if response.status_code != 200 or (json_response_status and json_response_status != 200):
                    # response.content: { status_code: 5xx, detial: 'xxx' }
                    logger.info(f'Cannot move bin from: {hold_stockbin_obj.id} to {stockbin_data_item["source_bin_name"]}, response: {str_response}')
                    raise APIException({"detail": f'Cannot move bin from: {hold_stockbin_obj.id} to {stockbin_data_item["source_bin_name"]}'})
                # delete hold bin
                hold_stockbin_obj.delete()

                # merge new source stock bin to origin stock bin
                new_stockbin_id = json_response["stockbin_id"]
                url = f'{settings.INNER_URL}/stock/bin/{stockbin_data_item["source_id"]}/'
                req_data = {
                    'merged_stockbin': new_stockbin_id,
                }
                headers = {
                    'Authorization': self.request.headers['Authorization'],
                    'Token': self.request.META.get('HTTP_TOKEN'),
                }

                response = requests.patch(url, json=req_data, headers=headers)
                str_response = response.content.decode('UTF-8')
                json_response = json.loads(str_response)
                json_response_status = json_response.get('status_code')
                if response.status_code != 200 or (json_response_status and json_response_status != 200):
                    # response.content: { status_code: 5xx, detial: 'xxx' }
                    logger.info(f'Cannot merge bin from: {new_stockbin_id} to {stockbin_data_item["source_id"]}, response: {str_response}')
                    raise APIException({"detail": f'Cannot merge bin from: {new_stockbin_id} to {stockbin_data_item["source_id"]}'})

                # clear target_id and target_bin_name
                stockbin_data_item['target_id'] = ''
                stockbin_data_item['target_bin_name'] = ''
                is_stockbin_data_changed = True

            # update shoporder
            if shoporder_obj and is_stockbin_data_changed:
                partial_data = {
                    'stockbin_data': json.dumps(stockbin_data)
                }
                serializer = serializers.ShoporderPartialUpdateSerializer(shoporder_obj, data=partial_data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
        else:
            # delete dn
            dn_obj = DnListModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), dn_code=qs.dn_code, is_delete=False).first()
            if dn_obj:
                url = f'{settings.INNER_URL}/dn/discard/{dn_obj.id}/'
                req_data = {}
                headers = {
                    'Authorization': self.request.headers['Authorization'],
                    'Token': self.request.META.get('HTTP_TOKEN'),
                }

                response = requests.delete(url, json=req_data, headers=headers)
                str_response = response.content.decode('UTF-8')
                json_response = json.loads(str_response)
                json_response_status = json_response.get('status_code')
                if response.status_code != 200 or (json_response_status and json_response_status != 200):
                    # response.content: { status_code: 5xx, detial: 'xxx' }
                    logger.info(f'Cannot discard dn of shop order: {qs.id}, response: {str_response}')
                    raise APIException({"detail": f'Cannot discard dn of shop order: {qs.id}'})

        qs.status = Status.Cancelled
        qs.dn_code = ''
        qs.save()

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
        start_time = time.time()
        data = self.request.data
        since = data.get('since')
        to = data.get('to')
        shop_id = data.get('shop_id')
        # mode: task or ''
        mode = data.get('mode')

        if shop_id:
            shop_list = ShopModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), id=str(shop_id), is_delete=False)
        else:
            shop_list = ShopModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), is_delete=False)

        # init Awaiting_Review order
        for shop in shop_list:
            status = Status.Awaiting_Review
            self.handle_shoporder(shop, since=since, to=to, status=status)
        # init Awaiting_Deliver order
        if mode != 'task':
            for shop in shop_list:
                status = Status.Awaiting_Deliver
                self.handle_shoporder(shop, since=since, to=to, status=status)

        processing_time = time.time() - start_time
        logger.info(f'init order for shop_id: {shop_id}, processing_time: {processing_time:.6f} seconds')

        return Response({"detail": "success"}, status=200)

    def handle_shoporder(self, shop, **args):
        shop_id = shop.id
        shopwarehouse_list = shop.shopwarehouse.filter(is_delete=False)
        warehosue_id = []
        for warehouse in shopwarehouse_list:
            warehosue_id.append(warehouse.platform_id)

        if len(warehosue_id) == 0:
            return

        seller_api = SELLER_API(shop_id)
        count = 0
        max_processing_time = 0
        offset = 0
        while True:
            params = {
                'offset': offset,
                'status':args['status'],
                'since': args['since'],
                'to': args['to'],
                'warehouse_id': warehosue_id
            }
            seller_resp = seller_api.get_orders(params)
            seller_resp_items = seller_resp.get('items', [])
            count = count + len(seller_resp_items)
            for item in seller_resp_items:
                start_time = time.time()
                item['shop'] = shop_id
                url = f'{settings.INNER_URL}/shoporder/'
                req_data = item
                headers = {
                    'Authorization': self.request.headers['Authorization'],
                    'Token': self.request.META.get('HTTP_TOKEN'),
                    'Operator': self.request.META.get('HTTP_OPERATOR')
                }

                response = requests.post(url, json=req_data, headers=headers)
                str_response = response.content.decode('UTF-8')
                json_response = json.loads(str_response)
                json_response_status = json_response.get('status_code')
                if response.status_code != 200 or (json_response_status and json_response_status != 200):
                    # response.content: { status_code: 5xx, detial: 'xxx' }
                    logger.error(f'init Awaiting_Review order failed, response: {str_response}')
                processing_time = time.time() - start_time
                if processing_time > max_processing_time:
                    max_processing_time = processing_time

            if seller_resp is None:
                break
            if not seller_resp.get('has_next', False):
                break
            offset = seller_resp['next']

        logger.info(f'handle init order for shop_id: {shop_id}, count: {count}, max_processing_time: {max_processing_time:.6f} seconds')

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
        since = data.get('since')
        to = data.get('to')

        shop_list = ShopModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), is_delete=False)

        # update Awaiting_Deliver order
        for shop in shop_list:
            status = Status.Awaiting_Deliver
            self.handle_shoporder(shop, since=since, to=to, status=status)
        # update Delivering order
        for shop in shop_list:
            status = Status.Delivering
            self.handle_shoporder(shop, since=since, to=to, status=status)
        # update Cancelled order
        for shop in shop_list:
            status = Status.Cancelled
            self.handle_shoporder(shop, since=since, to=to, status=status)

        return Response({"detail": "success"}, status=200)

    def handle_shoporder(self, shop, **args):
        shop_id = shop.id
        shopwarehouse_list = shop.shopwarehouse.filter(is_delete=False)
        warehosue_id = []
        for warehouse in shopwarehouse_list:
            warehosue_id.append(warehouse.platform_id)

        if len(warehosue_id) == 0:
            return

        seller_api = SELLER_API(shop_id)
        count = 0
        max_processing_time = 0
        offset = 0
        while True:
            params = {
                'offset': offset,
                'status':args['status'],
                'since': args['since'],
                'to': args['to'],
                'warehouse_id': warehosue_id
            }
            seller_resp = seller_api.get_orders(params)
            seller_resp_items = seller_resp.get('items', [])
            count = count + len(seller_resp_items)
            for item in seller_resp_items:
                start_time = time.time()
                item['shop'] = shop_id
                platform_id = item['platform_id']
                shop_order = ListModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), shop_id=shop_id, platform_id=platform_id, is_delete=False).first()
                if shop_order is None:
                    # logger.info(f'Can not find shop order for shop_id: {shop_id}, platform_id: {platform_id}')
                    continue
                url = f'{settings.INNER_URL}/shoporder/{shop_order.id}/'
                req_data = item
                headers = {
                    'Authorization': self.request.headers['Authorization'],
                    'Token': self.request.META.get('HTTP_TOKEN'),
                    'Operator': self.request.META.get('HTTP_OPERATOR')
                }

                response = requests.put(url, json=req_data, headers=headers)
                str_response = response.content.decode('UTF-8')
                json_response = json.loads(str_response)
                json_response_status = json_response.get('status_code')
                if response.status_code != 200 or (json_response_status and json_response_status != 200):
                    # response.content: { status_code: 5xx, detial: 'xxx' }
                    logger.info(f'update order {platform_id} to {args["status"]} failed, response: {json_response}')
                processing_time = time.time() - start_time
                if processing_time > max_processing_time:
                    max_processing_time = processing_time

            if seller_resp is None:
                break
            if not seller_resp.get('has_next', False):
                break
            offset = seller_resp['next']

        logger.info(f'update order for shop_id: {shop_id}, count: {count}, max_processing_time: {max_processing_time:.6f} seconds')

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

        # add extra info to data here
        for item in data:
            dn_code = item['dn_code']
            if dn_code:
                dn_obj = DnListModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), dn_code=dn_code, is_delete=False).first()
                if dn_obj:
                    total_weight = dn_obj.total_weight
                    item['total_weight'] = total_weight
                    item['dn_status'] = dn_obj.dn_status

            shop_id = item['shop']['id']
            warehouse_id = item['platform_warehouse_id']
            platform_warehouse_obj = ShopwarehouseModel.objects.filter(openid=self.request.META.get('HTTP_TOKEN'), shop_id=shop_id, platform_id=warehouse_id, is_delete=False).first()
            if platform_warehouse_obj:
                item['platform_warehouse_name'] = platform_warehouse_obj.platform_name

        renderer = self.get_lang(data)
        response = StreamingHttpResponse(
            renderer,
            content_type="text/csv"
        )
        response['Content-Disposition'] = "attachment; filename='shopsku_{}.csv'".format(
            str(dt.strftime('%Y%m%d%H%M%S%f')))
        return response
