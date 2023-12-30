import requests
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from shoporder.status import Status
import logging
import time
from urllib.parse import parse_qs, quote, unquote
from shop.models import ListModel as ShopModel

logger = logging.getLogger(__name__)
PACK_WEIGHT_KEY = 'Вес товара с упаковкой (г)'
PACK_WIDTH_KEY = 'Длина упаковки'
PACK_HEIGHT_KEY = 'Высота упаковки'
PACK_DEPTH_KEY = 'Ширина упаковки'

class WIBE_API():
    def __init__(self, shop_id: str, shop_data: dict):
        self._shop_id = shop_id
        self._api_key = shop_data['api_key']
        self._api_url = shop_data['api_url']
    
    def _request(self, path: str, method: str = 'POST', params: dict = {}) -> json:
        try:
            headers = {}
            headers.update({'Content-Type': 'application/json'})
            headers.update({'Accept': 'application/json'})
            headers.update({'Authorization': self._api_key})
            param_json = json.dumps(params, sort_keys=True, separators=(',', ':'))
            url = self._api_url + '{}'.format(path)
            logger.info(f'Request url: [{method}]{url} with params: {param_json}')

            start_time = time.time()
            if method == 'POST':
                response = requests.post(url=url, data=param_json, headers=headers)
            elif method == 'GET':
                response = requests.get(url=url, params=param_json, headers=headers)
            processing_time = time.time() - start_time
            logger.info(f'Request url: [{method}]{url} took {processing_time:.6f} seconds.')

            if response.status_code != 200:
                logger.error(f'Request url: [{method}]{url} with response status code: {response.status_code}')
                return None
            return json.loads(response.content)
        except Exception as e:
            logger.exception('{}'.format(e))
            return None

    def get_warehouses(self) -> json:
        warehouse_resp = self._request(path='/api/v3/warehouses', method='GET')
        resp = {
            'result': []
        }
        resp_list = resp['result']
        for item in warehouse_resp:
            resp_list.append({
                'warehouse_id': item['id'],
                'name': item['name']
            })

        return resp

    def get_products(self, params: dict) -> json:
        sort = self.get_sort_from_params(params)
        _params = {
            'sort': sort
        }

        shop_obj = ShopModel.objects.filter(id=self._shop_id).first()
        shopwarehouse_list = shop_obj.shopwarehouse.filter(is_delete=False)
        warehosue_ids = []
        for warehouse in shopwarehouse_list:
            warehosue_ids.append(warehouse.platform_id)

        product_resp = self._request(path='/content/v1/cards/cursor/list', params=_params)
        product_list = product_resp.get('data', {}).get('cards', [])
        if len(product_list) == 0:
            return {
                'count': 0,
                'last_id': '',
                'items': []
            }

        vendor_code_list = []
        sku_list = []
        sku_nmid_map = {}
        for item in product_list:
            nmid = item.get('nmID', '')
            vendor_code = item.get('vendorCode', '')
            if vendor_code:
                vendor_code_list.append(vendor_code)
            sizes = item.get('sizes', [])
            if len(sizes) > 0:
                size = sizes[0]
                skus = size.get('skus', [])
                if len(skus) > 0:
                    sku_list.append(skus[0])
                    sku_nmid_map[skus[0]] = nmid

        product_dict = {}
        if len(vendor_code_list) > 0:
            # get product detail info
            detail_params = {
                'vendorCodes': vendor_code_list,
                'allowedCategoriesOnly': True
            }
            product_detail_resp = self._request(path='/content/v1/cards/filter', params=detail_params)
            product_detail_list = product_detail_resp.get('data', [])
            for item in product_detail_list:
                id = item.get('nmID', '')
                if id:
                    product_dict[id] = item

            # get product total stock
            sku_stock_map = {}
            stock_params = {
                'skus': sku_list
            }
            for warehosue_id in warehosue_ids:
                product_stock_resp = self._request(path=f'/api/v3/stocks/{warehosue_id}', params=stock_params)
                product_stock_list = product_stock_resp.get('stocks', [])
                for item in product_stock_list:
                    sku = item.get('sku', '')
                    stock = item.get('amount', 0)
                    if sku in sku_stock_map:
                        sku_stock_map[sku] += stock
                    else:
                        sku_stock_map[sku] = stock

                    nmid = sku_nmid_map[sku]
                    product_item = product_dict[nmid]
                    if product_item:
                        product_item['stock'] = sku_stock_map[sku]

        for item in product_list:
            nmid = item.get('nmID', '')
            if nmid and product_dict.get(nmid):
                product_detail_dict = product_dict.get(nmid)
                item['platform_id'] = nmid
                item['platform_sku'] = nmid
                item['name'] = item['title']
                media_files = item.get('mediaFiles', [])
                if len(media_files) > 0:
                    item['image'] = media_files[0]
                characteristics = product_detail_dict.get('characteristics', [])
                item['width'] = 0
                item['height'] = 0
                item['depth'] = 0
                item['weight'] = 0
                for character in characteristics:
                    if PACK_WIDTH_KEY in character:
                        item['width'] = int(character[PACK_WIDTH_KEY]) * 10
                    elif PACK_HEIGHT_KEY in character:
                        item['height'] = int(character[PACK_HEIGHT_KEY]) * 10
                    elif PACK_DEPTH_KEY in character:
                        item['depth'] = int(character[PACK_DEPTH_KEY]) * 10
                    elif PACK_WEIGHT_KEY in character:
                        item['weight'] = int(character[PACK_WEIGHT_KEY])
                item['stock'] = product_detail_dict.get('stock', 0)
                item['platform_data'] = json.dumps({
                    'vendorCode': item['vendorCode']
                })

        cursor = product_resp.get('data', {}).get('cursor', {})
        limit = sort['cursor']['limit']
        last_id = self.get_last_id_from_cursor(cursor, limit)
        count = self.get_products_count()

        return {
            'count': count,
            'last_id': last_id,
            'items': product_resp.get('data', {}).get('cards', []),
        }

    def get_products_count(self) -> int:
        limit = 1000
        _params = {
            'sort': {
                'cursor': {
                    'limit': limit
                },
                'filter': {
                    'withPhoto': -1
                }
            }
        }

        count = 0
        while True:
            product_resp = self._request(path='/content/v1/cards/cursor/list', params=_params)
            cursor = product_resp.get('data', {}).get('cursor', {})
            total = cursor.get('total', 0)
            count += total
            nm_id = cursor.get('nmID', 0)
            update_at = cursor.get('updatedAt', '')
            if total < limit:
                break
            else:
                _params['sort']['cursor']['nmID'] = nm_id
                _params['sort']['cursor']['updatedAt'] = update_at

        return count

    def get_orders(self, params: dict) -> json:
        default_now = datetime.now()
        default_since = default_now + relativedelta(days=-300)
        default_now = default_now.strftime("%Y-%m-%dT%H:%M:%SZ")
        default_since = default_since.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not params:
            _params = {
                'offset': 0,
                'limit': 50,
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
                'limit': params.get('limit', 50),
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
        order_list = order_resp.get('result', {}).get('postings', [])

        order_dict = {
            'has_next': order_resp.get('result', {}).get('has_next', False),
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
                'order_data': json.dumps(item),
                'order_products': json.dumps(order_products)
            }
            order_dict['items'].append(order_item)

        return order_dict
    
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
        else:
            return Status.Other

    def get_sort_from_params(self, params):
        sort = {
            'cursor': {
                'limit': 30
            },
            'filter': {
                'withPhoto': -1
            }
        }

        if not params:
            return sort

        last_id = params['last_id']
        if last_id:
            # last_id = 'updatedAt=2022-08-10T10:16:52Z&nmID=66964167'
            last_obj = parse_qs(unquote(last_id))
            if last_obj:
                updated_at = last_obj.get('updatedAt')
                nm_id = last_obj.get('nmID')
                if updated_at:
                    sort['cursor']['updatedAt'] = updated_at[0]
                if nm_id:
                    try:
                        nm_id_value = int(nm_id[0])
                        sort['cursor']['nmID'] = nm_id_value
                    except ValueError:
                        logger.error(f'parse nmId {nm_id} to int failed')

        limit = params['limit']
        if limit:
            sort['cursor']['limit'] = int(limit)

        return sort

    def get_last_id_from_cursor(self, cursor, limit):
        if cursor['total'] < limit:
            return ''

        return quote(f"updatedAt={cursor['updatedAt']}&nmID={cursor['nmID']}")

