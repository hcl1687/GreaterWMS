from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)
sku_key = 'stock_sku'
timeout = 15

class ShopSku(object):
    def update_stock(staff_type):
        staff_type_list = ['Manager', 'Supervisor', 'Inbount', 'Outbound', 'StockControl', 'Customer', 'Supplier']
        return staff_type in staff_type_list

    def lock_and_add_sku(goods_code_list):
        if not goods_code_list:
            return
        if len(goods_code_list):
            return
        
        goods_code_list = [goods_code for goods_code in goods_code_list if goods_code]

        with cache.lock(sku_key, timeout=timeout):
            goods_code_dict = cache.get(sku_key)
            if not goods_code_dict:
                goods_code_dict = {}
            
            for sku in goods_code_list:
                goods_code_dict[sku] = 1

            cache.set(sku_key, goods_code_dict)

    def lock_and_clear_sku():
        goods_code_dict = {}
        with cache.lock(sku_key, timeout=timeout):
            goods_code_dict = cache.get(sku_key)
            cache.set(sku_key, {})

        return goods_code_dict



