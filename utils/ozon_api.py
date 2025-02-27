import requests
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from shoporder.status import Status
import logging
import time
import math
from shopsku.status import Sync_Status
from django.core.files.storage import default_storage
import io
from shoporder.models import ListModel

logger = logging.getLogger(__name__)
DEFAULT_LIMIT = 100

class OZON_API():
    def __init__(self, shop_id: str, shop_data: dict):
        self._shop_id = shop_id
        self._client_id = shop_data['client_id']
        self._api_key = shop_data['api_key']
        self._api_url = shop_data['api_url']
    
    def _request(self, path: str, method: str = 'POST', params: dict = {}, raw: bool = False) -> json:
        try:
            headers = {}
            headers.update({'Content-Type': 'application/json'})
            headers.update({'Accept': 'application/json'})
            headers.update({'Client-Id': self._client_id})
            headers.update({'Api-Key': self._api_key})
            param_json = json.dumps(params, sort_keys=True, separators=(',', ':'))
            url = self._api_url + '{}'.format(path)

            shot_param_str = param_json
            if len(param_json) > 1000:
                shot_param_str = param_json[0:1000] + "..."
            logger.info(f'Request url: [{method}]{url} with params: {shot_param_str}')

            start_time = time.time()
            if method == 'POST':
                response = requests.post(url=url, data=param_json, headers=headers, timeout=60)
            elif method == 'GET':
                response = requests.get(url=url, params=param_json, headers=headers, timeout=60)
            elif method == 'PUT':
                response = requests.put(url=url, data=param_json, headers=headers, timeout=60)
            processing_time = time.time() - start_time
            logger.info(f'Request url: [{method}]{url} took {processing_time:.6f} seconds.')

            if raw:
                return response

            if response.status_code != 200:
                logger.error(f'Request url: [{method}]{url} with response status code: {response.status_code}')
                return None
            return json.loads(response.content)
        except requests.exceptions.Timeout:
            logger.error(f'Request url: [{method}]{url} timeout')
            return None
        except Exception as e:
            logger.exception('{}'.format(e))
            return None

    def get_warehouses(self) -> json:
        resp = self._request(path='/v1/warehouse/list')
        if resp is None:
            resp = {
                'result': []
            }

        return resp

    def get_products(self, params: dict) -> json:
        if not params:
            params = {
                'last_id': '',
                'limit': DEFAULT_LIMIT
            }
        product_resp = self._request(path='/v2/product/list', params=params)
        if product_resp is None:
            product_list = []
        else:
            product_list = product_resp.get('result', {}).get('items', [])
        if len(product_list) == 0:
            return {
                'count': 0,
                'last_id': '',
                'items': []
            }

        product_id_list = []
        for item in product_list:
            product_id = item.get('product_id', '')
            if product_id:
                product_id_list.append(product_id)

        product_dict = {}
        if len(product_id_list) > 0:
            detail_params = {
                'product_id': product_id_list,
            }
            product_detail_resp = self._request(path='/v2/product/info/list', params=detail_params)
            if product_detail_resp is None:
                product_detail_list = []
            else:
                product_detail_list = product_detail_resp.get('result', {}).get('items', [])
            for item in product_detail_list:
                id = item.get('id', '')
                if id:
                    product_dict[id] = item

            attr_params = {
                'filter': {
                    'product_id': product_id_list,
                },
                'limit': params.get('limit')
            }
            product_attr_resp = self._request(path='/v3/products/info/attributes', params=attr_params)
            if product_attr_resp is None:
                product_attr_list = []
            else:
                product_attr_list = product_attr_resp.get('result', [])
            for item in product_attr_list:
                id = item.get('id', '')
                if id and product_dict.get(id):
                    product_dict[id]['attr'] = item

        for item in product_list:
            product_id = item.get('product_id', '')
            if product_id and product_dict.get(product_id):
                product_detail_dict = product_dict.get(product_id)
                item['platform_id'] = product_id
                # Todo: need to consider how to support fbo
                platform_sku = product_detail_dict.get('fbs_sku', 0)
                if platform_sku == 0:
                    platform_sku = product_detail_dict.get('sku', 0)
                item['platform_sku'] = platform_sku
                item['name'] = product_detail_dict.get('name', '')
                item['image'] = product_detail_dict.get('primary_image', '')
                item['width'] = product_detail_dict.get('attr', {}).get('width', 0)
                item['height'] = product_detail_dict.get('attr', {}).get('height', 0)
                item['depth'] = product_detail_dict.get('attr', {}).get('depth', 0)
                item['weight'] = product_detail_dict.get('attr', {}).get('weight', 0)
                item['stock'] = product_detail_dict.get('stocks', {}).get('present', 0)
                item['platform_data'] = json.dumps({})

        return {
            'count': product_resp.get('result', {}).get('total', 0),
            'last_id': product_resp.get('result', {}).get('last_id', ''),
            'items': product_resp.get('result', {}).get('items', []),
        }

    def get_orders(self, params: dict) -> json:
        default_now = datetime.now()
        default_since = default_now + relativedelta(days=-300)
        default_now = default_now.strftime("%Y-%m-%dT%H:%M:%SZ")
        default_since = default_since.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not params:
            _params = {
                'offset': 0,
                'limit': DEFAULT_LIMIT,
                'filter': {
                    'since': default_since,
                    'to': default_now,
                    'status': ''
                }
            }
        else:
            status = self.toPlatformStatus(params['status'])
            _params = {
                'offset': params.get('offset', 0),
                'limit': params.get('limit', DEFAULT_LIMIT),
                'filter': {
                    'since': default_since,
                    'to': default_now,
                    'status': status
                }
            }

            # params.since params.to are timestamp
            since = params['since']
            to = params['to']
            if since:
                _params['filter']['since'] = since
            if to:
                _params['filter']['to'] = to
            # filter by warehouse id
            if params['warehouse_id']:
                _params['filter']['warehouse_id'] = params['warehouse_id']

        order_resp = self._request(path='/v3/posting/fbs/list', params=_params)
        if order_resp is None:
            has_next = False
            order_list = []
        else:
            has_next = order_resp.get('result', {}).get('has_next', False)
            order_list = order_resp.get('result', {}).get('postings', [])

        order_dict = {
            'has_next': has_next,
            'next': _params['offset'] + _params['limit'],
            'items': []
        }

        for item in order_list:
            products = item.get('products', [])
            order_products = []
            for product in products:
                order_products.append({
                    'name': product.get('name', ''),
                    'sku': product.get('sku', 0),
                    'quantity': product.get('quantity', 0)
                })

            order_item = {
                'platform_id': item['order_id'],
                'platform_warehouse_id': item.get('delivery_method', {}).get('warehouse_id'),
                'posting_number': item['posting_number'],
                'order_time': item['in_process_at'],
                'shipment_time': item['shipment_date'],
                'status': self.toSystemStatus(item['status']),
                # do not same platform order data to reduce table size.
                # 'order_data': json.dumps(item),
                'order_data': json.dumps({}),
                'order_products': json.dumps(order_products)
            }
            order_dict['items'].append(order_item)

        return order_dict

    def update_stock(self, params: dict) -> json:
        if not params:
            return None

        # params: {'warehouse_id': 123, stocks: [{'product_id': 456, 'stock': 100}]}
        stocks = params.get('stocks', [])
        if len(stocks) == 0:
            return None

        res = []
        warehouse_id = params.get('warehouse_id', '')
        if not warehouse_id:
            for item in stocks:
                res.append({
                    'product_id': item['product_id'],
                    'status': Sync_Status.Failed,
                    'message': 'no warehouse_id'
                })
            return res

        # only 100 products in one request at most.
        size = 100
        times = math.ceil(len(stocks) / size)
        for i in range(times):
            sub_stocks = stocks[i * size : (i + 1) * size]
            for item in sub_stocks:
                item['warehouse_id'] = warehouse_id
            _params = {
                'stocks': sub_stocks
            }
            stock_resp = self._request(path='/v2/products/stocks', params=_params)
            if stock_resp is None:
                for item in sub_stocks:
                    res.append({
                        'product_id': item['product_id'],
                        'status': Sync_Status.Failed,
                        'message': 'api no response'
                    })
            else:
                stock_result = stock_resp.get('result', [])
                stock_result_dict = {}
                for item in stock_result:
                    updated = item.get('updated', True)
                    message = ''
                    if not updated:
                        errors = item.get('errors', [])
                        if len(errors) > 0:
                            message = errors[0].get('code', '')
                    status = Sync_Status.Success
                    if not updated:
                        status = Sync_Status.Failed
                    stock_result_dict[str(item['product_id'])] = {
                        'product_id': str(item['product_id']),
                        'status': status,
                        'message': message
                    }

                for item in sub_stocks:
                    stock_result_item = stock_result_dict.get(str(item['product_id']))
                    if not stock_result_item:
                        stock_result_item = {
                            'product_id': item['product_id'],
                            'status': Sync_Status.Failed,
                            'message': 'no result'
                        }
                    res.append(stock_result_item)

        return res

    def get_label(self, params: dict) -> json:
        if not params:
            return None

        # params: {'order_id': '123'}
        order_id = params.get('order_id', '')
        if not order_id:
            return None
        
        shoporder_obj = ListModel.objects.filter(shop_id=self._shop_id, is_delete=False, id=order_id).first()
        if shoporder_obj is None:
            return None

        shop_type = shoporder_obj.shop.shop_type
        if not shop_type:
            return None
        
        posting_number = shoporder_obj.posting_number
        if not posting_number:
            return None
        
        _params = {
            'posting_number': [posting_number]
        }
        label_resp = self._request(path='/v2/posting/fbs/package-label', params=_params, raw=True)
        if label_resp.status_code != 200:
            logger.error(f'Request url: [POST]/v2/posting/fbs/package-label with response status code: {label_resp.status_code}')
            return None

        if label_resp is None:
            return None

        bytes_io = io.BytesIO(label_resp.content)
        file_name = default_storage.save(f'labels/{shop_type}_{posting_number}.pdf', bytes_io)
        return file_name

    def toPlatformStatus(self, status):
        if status == Status.Awaiting_Review:
            return 'awaiting_packaging'
        elif status == Status.Awaiting_Deliver:
            return 'awaiting_deliver'
        elif status == Status.Delivering:
            return 'delivering'
        elif status == Status.Cancelled:
            return 'cancelled'
        else:
            return ''

    def toSystemStatus(self, status):
        if status == 'awaiting_packaging':
            return Status.Awaiting_Review
        elif status == 'awaiting_deliver':
            return Status.Awaiting_Deliver
        elif status == 'delivering':
            return Status.Delivering
        elif status == 'cancelled':
            return Status.Cancelled
        elif status == 'delivered':
            return Status.Delivered
        else:
            return Status.Other

