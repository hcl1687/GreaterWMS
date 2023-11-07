from userprofile.models import Users
from staff.models import ListModel, TypeListModel
from supplier.models import ListModel as SupplierModel
import logging
import requests
import json

class OZON_API():
    def __init__(self, shop_data: dict):
        self._logger = logging.getLogger(__name__)
        self._client_id = shop_data['client_id']
        self._api_key = shop_data['api_key']
        self._api_url = shop_data['api_url']
    
    def _request(self, path: str, params: dict = {}) -> json:
        try:
            headers = {}
            headers.update({'Content-Type': 'application/json'})
            headers.update({'Accept': 'application/json'})
            headers.update({'Client-Id': self._client_id})
            headers.update({'Api-Key': self._api_key})
            param_json = json.dumps(params, sort_keys=True, separators=(',', ':'))
            url = self._api_url + '{}'.format(path)
            if self._logger:
                self._logger.debug('Request url: {}'.format(url))
                self._logger.debug('Request headers: {}'.format(headers))
                self._logger.debug('Request params: {}'.format(param_json))
            response = requests.post(url=url, data=param_json, headers=headers)
            if self._logger:
                self._logger.debug('Response status code: {}'.format(response.status_code))
                self._logger.debug('Response headers: {}'.format(response.headers))
                self._logger.debug('Response content: {}'.format(response.content.decode('UTF-8')))
            if response.status_code != 200:
                return None
            return json.loads(response.content)
        except Exception as e:
            if self._logger:
                self._logger.exception('{}'.format(e))
            return None
    def getWarehouses(self) -> json:
        return self._request(path='/v1/warehouse/list')

    def getProducts(self, params: dict) -> json:
        if not params:
            params = {
                'last_id': '',
                'limit': 30
            }
        product_resp = self._request(path='/v2/product/list', params=params)
        product_list = product_resp.get('result', {}).get('items', [])
        if len(product_list) == 0:
            return product_resp

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
                item['platform_sku'] = product_detail_dict.get('fbs_sku', '')
                item['image'] = product_detail_dict.get('primary_image', '')
                item['width'] = product_detail_dict.get('attr', {}).get('width', 0)
                item['height'] = product_detail_dict.get('attr', {}).get('height', 0)
                item['depth'] = product_detail_dict.get('attr', {}).get('depth', 0)
                item['weight'] = product_detail_dict.get('attr', {}).get('weight', 0)

        return product_resp

    def getOrders(self, params: dict) -> json:
        return self._request(path='/v3/posting/fbs/list', params=params)

