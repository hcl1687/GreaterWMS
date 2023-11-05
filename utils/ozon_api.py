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
                'limit': 1000
            }
        return self._request(path='/v2/product/list', params=params)

    def getOrders(self, params: dict) -> json:
        return self._request(path='/v3/posting/fbs/list', params=params)

