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
            try:
                shop_data = json.loads(shop_obj.shop_data)
            except json.JSONDecodeError:
                print("shop_data decode error")
            if shop_data:
                self._api_data = shop_data
                if shop_obj.shop_type == 'OZON':
                    self._api = OZON_API(shop_data=shop_data)

    def get_warehouses(self) -> json:
        if self._api is None:
            return None
        return self._api.get_warehouses()

    def get_products(self, params: dict) -> json:
        if self._api is None:
            return None
        return self._api.get_products(params=params)

    def get_orders(self, params: dict) -> json:
        if self._api is None:
            return None
        return self._api.get_orders(params=params)
