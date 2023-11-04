from shop.models import ListModel
import logging
import json
from utils.ozon_api import OZON_API

class SELLER_API():
    def __init__(self, shop_id: str):
        self._logger = logging.getLogger(__name__)
        if shop_id is None:
            self._logger.error('shop_id is None')
            return

        shop_obj = ListModel.objects.filter(id=shop_id).first()
        if shop_obj:
            shop_data = json.loads(shop_obj.shop_data)
            if shop_data:
                self._api_data = shop_data
                if shop_obj.shop_type == 'OZON':
                    self._api = OZON_API(shop_data=shop_data)

    def getWarehouses(self) -> json:
        return self._api.getWarehouses()

    def getProducts(self, params: dict) -> json:
        return self._api.getProducts(params=params)

    def getOrders(self, params: dict) -> json:
        return self._api.getOrders(params=params)

