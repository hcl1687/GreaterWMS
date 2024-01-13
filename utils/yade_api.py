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
            product_resp = self._request(path=f'/businesses/{business_id}/offer-mappings?{query}', method='GET')
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
        order_dict = {
            'has_next': False,
            'next': 0,
            'items': []
        }

        return order_dict

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

    def get_query_from_params(self, params):
        default_limit = 100
        if not params:
            return f"limit={default_limit}"

        limit = params['limit']
        if not limit:
            limit = default_limit
        res = f"limit={limit}"

        page_token = params['last_id']
        if page_token:
            res = f"{res}&page_token={page_token}"

        return res
