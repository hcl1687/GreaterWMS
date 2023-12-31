import requests
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from shoporder.status import Status
import logging
import time
from urllib.parse import parse_qs, quote, unquote
from shop.models import ListModel as ShopModel
from shopsku.models import ListModel as ShopskuModel

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
                response = requests.get(url=url, params=params, headers=headers)
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
        if warehouse_resp is None:
            return resp

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
        if product_resp is None:
            return {
                'count': 0,
                'last_id': '',
                'items': []
            }

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
                for sku in skus:
                    sku_list.append(sku)
                    sku_nmid_map[sku] = nmid

        product_dict = {}
        if len(vendor_code_list) > 0:
            # get product detail info
            detail_params = {
                'vendorCodes': vendor_code_list,
                'allowedCategoriesOnly': True
            }
            product_detail_resp = self._request(path='/content/v1/cards/filter', params=detail_params)
            if product_detail_resp is None:
                product_detail_list = []
            else:
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
                if product_stock_resp is None:
                    product_stock_list = []
                else:
                    product_stock_list = product_stock_resp.get('stocks', [])

                for item in product_stock_list:
                    sku = item.get('sku', '')
                    stock = item.get('amount', 0)
                    if sku in sku_stock_map:
                        sku_stock_map[sku] += stock
                    else:
                        sku_stock_map[sku] = stock

            # update product item's stock
            for sku in list(sku_stock_map.keys()):
                nmid = sku_nmid_map[sku]
                if nmid in product_dict:
                    product_item = product_dict[nmid]
                    if 'stock' in product_item:
                        product_item['stock'] += sku_stock_map[sku]
                    else:
                        product_item['stock'] = sku_stock_map[sku]

        for item in product_list:
            nmid = item.get('nmID', '')
            if nmid and product_dict.get(nmid):
                product_detail_dict = product_dict.get(nmid, {})
                item['platform_id'] = nmid
                item['platform_sku'] = nmid
                item['name'] = item['title']
                media_files = item.get('mediaFiles', [])
                item['image'] = ''
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
            if product_resp is None:
                break
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
        if params['status'] == Status.Awaiting_Review:
            order_resp = self.get_new_orders(params)
        else:
            order_resp = self.get_orders_by_filter(params)

        nm_ids = [item.get('nmId', 0) for item in order_resp['items']]
        # remove duplicate elements
        nm_ids = list(set(nm_ids))
        shopsku_list = ShopskuModel.objects.filter(platform_id__in=nm_ids)
        shopsku_dict = {}
        for item in shopsku_list:
            shopsku_dict[item.platform_id] = item

        order_dict = {
            'has_next': order_resp.get('has_next', False),
            'next': order_resp.get('next', 0),
            'items': []
        }
        for item in order_resp['items']:
            nm_id = item.get('nmId', 0)
            name = ''
            if nm_id in shopsku_dict:
                name = shopsku_dict[nm_id].name
            order_products = [{
                'name': name,
                'sku': nm_id,
                'quantity': 1
            }]

            create_time = item['createdAt']
            shipment_time = datetime.strptime(create_time, "%Y-%m-%dT%H:%M:%SZ") + relativedelta(days=3)
            shipment_time = shipment_time.strftime("%Y-%m-%dT%H:%M:%SZ")

            order_item = {
                'platform_id': item['id'],
                'platform_warehouse_id': item.get('warehouseId'),
                'posting_number': item['id'],
                'order_time': create_time,
                'shipment_time': shipment_time,
                'status': self.toSystemStatus(item['status']),
                'order_data': json.dumps(item),
                'order_products': json.dumps(order_products)
            }
            order_dict['items'].append(order_item)

        return order_dict

    def get_new_orders(self, params: dict):
        default_now = datetime.now()
        default_since = default_now + relativedelta(days=-300)
        default_now = int(default_now.timestamp())
        default_since = int(default_since.timestamp())
        if not params:
            warehouse_id = []
            _params = {
                'next': 0,
                'limit': 1000,
                'dateFrom': default_since,
                'dateTo': default_now
            }
        else:
            warehouse_id = params.get('warehouse_id', [])
            _params = {
                'next': params.get('offset', 0),
                'limit': params.get('limit', 1000),
                'dateFrom': default_since,
                'dateTo': default_now,
            }

            # params.since params.to are timestamp
            since = params['since']
            to = params['to']
            if since:
                since = int(datetime.strptime(since, "%Y-%m-%dT%H:%M:%SZ").timestamp())
                _params['dateFrom'] = since
            if to:
                to = int(datetime.strptime(to, "%Y-%m-%dT%H:%M:%SZ").timestamp())
                _params['dateTo'] = to

        order_resp = self._request(path='/api/v3/orders/new', method='GET')
        if order_resp is None:
            order_list = []
        else:
            order_list = order_resp.get('orders', [])

        # filter by warehouse_id
        if len(warehouse_id) > 0:
            order_list = [item for item in order_list if str(item['warehouseId']) in warehouse_id]

        # filter by date
        items = []
        for order in order_list:
            created_at = int(datetime.strptime(order['createdAt'], "%Y-%m-%dT%H:%M:%SZ").timestamp())
            if created_at >= _params['dateFrom'] and created_at <= _params['dateTo']:
                order['status'] = 'new'
                items.append(order)

        logger.info(f'WIBE get_new_orders with {json.dumps(params)}, items length: {len(items)}')

        return {
            'has_next': False,
            'next': 0,
            'items': items
        }
    
    def get_orders_by_filter(self, params: dict):
        default_now = datetime.now()
        default_since = default_now + relativedelta(days=-300)
        default_now = int(default_now.timestamp())
        default_since = int(default_since.timestamp())
        if not params:
            status = ''
            warehouse_id = []
            _params = {
                'next': 0,
                'limit': 1000,
                'dateFrom': default_since,
                'dateTo': default_now
            }
        else:
            status = self.toPlatformStatus(params['status'])
            warehouse_id = params.get('warehouse_id', [])
            _params = {
                'next': params.get('offset', 0),
                'limit': params.get('limit', 1000),
                'dateFrom': default_since,
                'dateTo': default_now,
            }

            # params.since params.to are timestamp
            since = params['since']
            to = params['to']
            if since:
                since = int(datetime.strptime(since, "%Y-%m-%dT%H:%M:%SZ").timestamp())
                _params['dateFrom'] = since
            if to:
                to = int(datetime.strptime(to, "%Y-%m-%dT%H:%M:%SZ").timestamp())
                _params['dateTo'] = to

        order_resp = self._request(path='/api/v3/orders', method='GET', params=_params)
        if order_resp is None:
            order_resp_next = 0
            order_list = []
        else:
            order_resp_next = order_resp.get('next', 0)
            order_list = order_resp.get('orders', [])
        # filter by warehouse_id
        if len(warehouse_id) > 0:
            order_list = [item for item in order_list if str(item['warehouseId']) in warehouse_id]
        order_dict = {}
        for item in order_list:
            order_dict[item['id']] = item

        # get orders' latest status
        if len(order_list) > 0:
            order_ids = [item['id'] for item in order_list]
            status_params = {
                'orders': order_ids
            }
            order_status_resp = self._request(path='/api/v3/orders/status', params=status_params)
            if order_status_resp is None:
                order_status_list = []
            else:
                order_status_list = order_status_resp.get('orders', [])
            for item in order_status_list:
                order_item = order_dict[item['id']]
                order_item['status'] = item['supplierStatus']

        # filter by status
        if status:
            order_list = [item for item in order_list if item['status'] == status]

        logger.info(f'WIBE get_orders_by_filter with {json.dumps(params)}, items length: {len(order_list)}')

        return {
            'has_next': order_resp_next != 0,
            'next': order_resp_next,
            'items': order_list
        }

    def toPlatformStatus(self, status):
        if status == Status.Awaiting_Review:
            return 'new'
        elif status == Status.Awaiting_Deliver:
            return 'confirm'
        elif status == Status.Delivering:
            return 'complete'
        elif status == Status.Cancelled:
            return 'cancel'
        else:
            return ''

    def toSystemStatus(self, status):
        if status == 'new':
            return Status.Awaiting_Review
        elif status == 'confirm':
            return Status.Awaiting_Deliver
        elif status == 'complete':
            return Status.Delivering
        elif status == 'cancel':
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

