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
from pytz import timezone
import pytz
import math
from shopsku.status import Sync_Status

logger = logging.getLogger(__name__)
moscow = timezone('Europe/Moscow')

DEFAULT_LIMIT = 100
DEFAULT_PAGE_SIZE = 50

class YADE_API():
    def __init__(self, shop_id: str, shop_data: dict):
        self._shop_id = shop_id
        self._api_url = shop_data['api_url']
        self._token = shop_data['token']
        self._platform_shop_id = shop_data['shop_id']
        self._warehouse_id = shop_data['warehouse_id']
    
    def _request(self, path: str, method: str = 'POST', params: dict = {}) -> json:
        try:
            headers = {}
            headers.update({'Content-Type': 'application/json'})
            headers.update({'Accept': 'application/json'})
            headers.update({'Authorization': f'Bearer {self._token}'})
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
                response = requests.get(url=url, params=params, headers=headers, timeout=60)
            elif method == 'PUT':
                response = requests.put(url=url, data=param_json, headers=headers, timeout=60)
            processing_time = time.time() - start_time
            logger.info(f'Request url: [{method}]{url} took {processing_time:.6f} seconds.')

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
        # get business id by shop id
        resp = {
            'result': []
        }

        campaign_resp = self._request(path=f'/campaigns/{self._platform_shop_id}', method='GET')
        if campaign_resp is None:
            return resp

        business_id = campaign_resp.get('campaign', {}).get('business', {}).get('id', '')
        if not business_id:
            return resp

        warehouse_resp = self._request(path=f'/businesses/{business_id}/warehouses', method='GET')
        if warehouse_resp is None:
            return resp

        resp_list = resp['result']
        warehouse_list = warehouse_resp.get('result', {}).get('warehouses', [])
        for item in warehouse_list:
            resp_list.append({
                'warehouse_id': item['id'],
                'name': item['name']
            })

        return resp

    def get_products(self, params: dict) -> json:
        resp = {
            'count': 0,
            'last_id': '',
            'items': []
        }
        campaign_resp = self._request(path=f'/campaigns/{self._platform_shop_id}', method='GET')
        if campaign_resp is None:
            return resp

        business_id = campaign_resp.get('campaign', {}).get('business', {}).get('id', '')
        if not business_id:
            return resp

        query = self.get_query_from_params(params)

        shop_obj = ShopModel.objects.filter(id=self._shop_id).first()
        shopwarehouse_list = shop_obj.shopwarehouse.filter(is_delete=False)
        warehosue_ids = []
        for warehouse in shopwarehouse_list:
            warehosue_ids.append(warehouse.platform_id)

        product_resp = self._request(path=f'/businesses/{business_id}/offer-mappings?{query}')
        if product_resp is None:
            return resp

        product_list = product_resp.get('result', {}).get('offerMappings', [])
        if len(product_list) == 0:
            return {
                'count': 0,
                'last_id': '',
                'items': []
            }

        product_ids = []
        product_dict = {}
        product_items = []
        for item in product_list:
            offer = item.get('offer', {})
            offer_id = offer.get('offerId', '')
            mapping = item.get('mapping', {})
            offer['stock'] = 0
            offer['mapping'] = mapping
            if offer_id:
                product_ids.append(offer_id)
                product_dict[offer_id] = offer
                product_items.append(offer)

        # get products stock
        if len(product_ids) > 0:
            stock_params = {
                'offerIds': product_ids
            }
            query = f'limit={len(product_ids)}'
            stock_resp = self._request(path=f'/campaigns/{self._platform_shop_id}/offers/stocks?{query}', params=stock_params)
            if stock_resp:
                warehouses_list = stock_resp.get('result', {}).get('warehouses', [])
                for warehouse in warehouses_list:
                    warehouse_id = str(warehouse.get('warehouseId', ''))
                    if warehouse_id not in warehosue_ids:
                        continue
                    offers = warehouse.get('offers', [])
                    for item in offers:
                        offer_id = item.get("offerId", "")
                        if not offer_id:
                            continue
                        stocks = item.get('stocks', [])
                        available_stocks = [stock_item.get('count', 0) for stock_item in stocks if str(stock_item['type']) == 'AVAILABLE']
                        if len(available_stocks) == 0:
                            continue
                        if offer_id in product_dict:
                            product_item = product_dict[offer_id]
                            if 'stock' in product_item:
                                product_item['stock'] += available_stocks[0]
                            else:
                                product_item['stock'] = available_stocks[0]

        for product_id in product_ids:
            item = product_dict[product_id]
            item['platform_id'] = product_id
            item['platform_sku'] = product_id
            item['name'] = item['name']
            media_files = item.get('pictures', [])
            item['image'] = ''
            if len(media_files) > 0:
                item['image'] = media_files[0]
            weightDimensions = item.get('weightDimensions', {})
            item['width'] = float(weightDimensions.get('length', 0)) * 10
            item['height'] = float(weightDimensions.get('height', 0)) * 10
            item['depth'] = float(weightDimensions.get('width', 0)) * 10
            item['weight'] = float(weightDimensions.get('weight', 0)) * 1000
            platform_data = {}
            barcodes = item.get('barcodes', [])
            if len(barcodes) > 0:
                platform_data['barcode'] = barcodes[0]
            item['platform_data'] = json.dumps(platform_data)

        next_page_token = product_resp.get('result', {}).get('paging', {}).get('nextPageToken', '')
        last_id = next_page_token
        count = self.get_products_count(business_id)

        return {
            'count': count,
            'last_id': last_id,
            'items': product_items,
        }

    def get_products_count(self, business_id) -> int:
        limit = 200
        page_token = ''

        count = 0
        while True:
            query = f'page_token={page_token}&limit={limit}'
            product_resp = self._request(path=f'/businesses/{business_id}/offer-mappings?{query}')
            if product_resp is None:
                break
            next_page_token = product_resp.get('result', {}).get('paging', {}).get('nextPageToken', '')
            total = len(product_resp.get('result', {}).get('offerMappings', []))
            count += total
            if total < limit:
                break
            else:
                page_token = next_page_token

        return count

    def get_orders(self, params: dict) -> json:
        default_now = datetime.now()
        default_since = default_now + relativedelta(days=-30)
        # to moscow time
        default_now = default_now.astimezone(moscow).strftime("%d-%m-%Y")
        # to moscow time
        default_since = default_since.astimezone(moscow).strftime("%d-%m-%Y")
        if not params:
            _params = {
                'page': 1,
                'pageSize': DEFAULT_PAGE_SIZE,
                'fake': False,
                'fromDate': default_since,
                'toDate': default_now
            }
        else:
            status_obj = self.toPlatformStatus(params['status'])
            offset = params.get('offset', 0)
            page_size = params.get('limit', DEFAULT_PAGE_SIZE)
            page = int(offset / page_size) + 1
            _params = {
                'page': page,
                'pageSize': page_size,
                'fake': False,
                'fromDate': default_since,
                'toDate': default_now
            }

            # params.since params.to are timestamp
            since = params['since']
            to = params['to']
            if since:
                since = datetime.strptime(since, "%Y-%m-%dT%H:%M:%SZ")
                since = since.astimezone(moscow).strftime("%d-%m-%Y")
                _params['fromDate'] = since
            if to:
                to = datetime.strptime(to, "%Y-%m-%dT%H:%M:%SZ")
                to = to.astimezone(moscow).strftime("%d-%m-%Y")
                _params['toDate'] = to
            # filter by status
            if 'status' in status_obj:
                _params['status'] = status_obj['status']
            if 'substatus' in status_obj:
                _params['substatus'] = status_obj['substatus']

        order_resp = self._request(path=f'/campaigns/{self._platform_shop_id}/orders', method='GET', params=_params)
        if order_resp is None:
            has_next = False
            order_list = []
            next = 0
        else:
            total = order_resp.get('pager', {}).get('total', 0)
            current_page = order_resp.get('pager', {}).get('currentPage', 1)
            page_size = order_resp.get('pager', {}).get('pageSize', DEFAULT_PAGE_SIZE)
            has_next = total > (current_page * page_size)
            order_list = order_resp.get('orders', [])
            next = 0
            if has_next:
                next = current_page * page_size

        order_dict = {
            'has_next': has_next,
            'next': next,
            'items': []
        }

        for item in order_list:
            products = item.get('items', [])
            order_products = []
            for product in products:
                order_products.append({
                    'name': product.get('offerName', ''),
                    'sku': product.get('offerId', ''),
                    'quantity': product.get('count', 0)
                })

            shipments = item.get('delivery', {}).get('shipments', [])
            order_shipments = []
            for shipment in shipments:
                # shipment_date: "12-11-2023"
                shipment_date_str = shipment.get('shipmentDate', '')
                # shipment_time: "15:30"
                shipment_time_str = shipment.get('shipmentTime', '')
                if shipment_date_str and shipment_time_str:
                    shipment_datetime = f'{shipment_date_str} {shipment_time_str}:00+03:00'
                    shipment_datetime = datetime.strptime(shipment_datetime, "%d-%m-%Y %H:%M:%S%z")
                    shipment_datetime = shipment_datetime.astimezone(pytz.utc)
                    order_shipments.append(shipment_datetime)

            shipment_time = ''
            if len(order_shipments) > 0:
                # find the nearest shipment time
                order_shipments.sort()
                shipment_time = order_shipments[0].strftime("%Y-%m-%dT%H:%M:%SZ")

            order_item = {
                'platform_id': item['id'],
                'platform_warehouse_id': self._warehouse_id,
                'posting_number': item['id'],
                'order_time': '',
                'shipment_time': shipment_time,
                'status': self.toSystemStatus(item['status'], item['substatus']),
                # do not same platform order data to reduce table size.
                # 'order_data': json.dumps(item),
                'order_data': json.dumps({}),
                'order_products': json.dumps(order_products)
            }
            if item.get('creationDate', '') :
                # creationDate: DD-MM-YYYY HH:MM:SS, default Time zone - UTC+03:00 (Moscow).
                create_date = f'{item["creationDate"]}+03:00'
                create_date = datetime.strptime(create_date, "%d-%m-%Y %H:%M:%S%z")
                create_date = create_date.astimezone(pytz.utc)
                order_item['order_time'] = create_date.strftime("%Y-%m-%dT%H:%M:%SZ")

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
            skus = []

            default_now = datetime.now()
            # to moscow time
            default_now = default_now.astimezone(moscow).replace(microsecond=0).isoformat()
            for item in sub_stocks:
                skus.append({
                    'sku': item['product_id'],
                    'warehouseId': warehouse_id,
                    'items': [{
                        'count': item['stock'],
                        'type': 'FIT',
                        'updatedAt': default_now
                    }]
                })
            _params = {
                'skus': skus
            }
            stock_resp = self._request(path=f'/campaigns/{self._platform_shop_id}/offers/stocks', method='PUT', params=_params)
            if stock_resp is None:
                for item in sub_stocks:
                    res.append({
                        'product_id': item['product_id'],
                        'status': Sync_Status.Failed,
                        'message': 'api no response'
                    })
            elif stock_resp['status'] == 'ERROR':
                errors = stock_resp.get('errors', [])
                code = ''
                if len(errors) > 0:
                    code = errors[0].get('code', '')
                for item in sub_stocks:
                    res.append({
                        'product_id': item['product_id'],
                        'status': Sync_Status.Failed,
                        'message': code
                    })
            else:
                for item in sub_stocks:
                    res.append({
                        'product_id': item['product_id'],
                        'status': Sync_Status.Success,
                        'message': ''
                    })
        return res

    def toPlatformStatus(self, status):
        if status == Status.Awaiting_Review:
            return {
                'status': 'PROCESSING',
                'substatus': 'STARTED'
            }
        elif status == Status.Awaiting_Deliver:
            return {
                'status': 'PROCESSING',
                'substatus': 'READY_TO_SHIP'
            }
        elif status == Status.Delivering:
            return {
                'status': 'DELIVERY'
            }
        elif status == Status.Cancelled:
            return {
                'status': 'CANCELLED'
            }
        else:
            return {}

    def toSystemStatus(self, status, substatus):
        if status == 'PROCESSING' and substatus == 'STARTED':
            return Status.Awaiting_Review
        elif status == 'PROCESSING' and substatus == 'READY_TO_SHIP':
            return Status.Awaiting_Deliver
        elif status == 'DELIVERY':
            return Status.Delivering
        elif status == 'CANCELLED':
            return Status.Cancelled
        elif status == 'DELIVERED':
            return Status.Delivered
        else:
            return Status.Other

    def get_query_from_params(self, params):
        if not params:
            return f"limit={DEFAULT_LIMIT}"

        limit = params['limit']
        if not limit:
            limit = DEFAULT_LIMIT
        res = f"limit={limit}"

        page_token = params['last_id']
        if page_token:
            res = f"{res}&page_token={page_token}"

        return res
