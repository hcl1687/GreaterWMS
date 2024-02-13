from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)
sku_key = 'stock_sku'
timeout = 15

class CacheTool(object):
    def lock_and_add_sku(goods_code_list):
        if not goods_code_list:
            return
        if len(goods_code_list) == 0:
            return
        
        goods_code_list = [goods_code for goods_code in goods_code_list if goods_code]

        with cache.lock(f'{sku_key}_lock', timeout=timeout):
            goods_code_dict = cache.get(sku_key)
            if not goods_code_dict:
                goods_code_dict = {}
            for sku in goods_code_list:
                goods_code_dict[sku] = 1

            cache.set(sku_key, goods_code_dict)

    def lock_and_clear_sku():
        goods_code_dict = {}
        with cache.lock(f'{sku_key}_lock', timeout=timeout):
            goods_code_dict = cache.get(sku_key)
            if not goods_code_dict:
                goods_code_dict = {}
            cache.set(sku_key, {})

        return goods_code_dict



