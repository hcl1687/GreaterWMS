from django.core.cache import cache
from shopsku.models import ListModel as ShopskuModel
from stock.models import StockListModel
from utils.seller_api import SELLER_API
import logging
from datetime import datetime
from shop.models import ListModel as ShopModel


logger = logging.getLogger(__name__)
sku_key = 'stock_sku'
timeout = 15

class Shopsku(object):
    def update_stock(shop_id, goods_code_list, celeryuser, **args):
        shop = ShopModel.objects.filter(openid=celeryuser['openid'], id=str(shop_id), is_delete=False, sync=True).first()
        shopwarehouse_list = shop.shopwarehouse.filter(is_delete=False)
        warehosue_id_list = []
        for warehouse in shopwarehouse_list:
            warehosue_id_list.append(warehouse.platform_id)

        if len(warehosue_id_list) == 0:
            return
        
        warehosue_id = warehosue_id_list[0]

        # get product id
        product_id_dict = {}
        shopsku_list = ShopskuModel.objects.filter(openid=celeryuser['openid'], is_delete=False,
                                                goods_code__in=goods_code_list)
        for shopsku_item in shopsku_list:
            product_id_dict[shopsku_item.goods_code] = shopsku_item.platform_id

        # get latest stock
        stocks = []
        goods_qty_change_list = StockListModel.objects.filter(openid=celeryuser['openid'], is_delete=False,
                                                            goods_code__in=goods_code_list)
        for goods_qty_change in goods_qty_change_list:
            goods_code = goods_qty_change.goods_code
            if goods_code in product_id_dict:
                product_id = product_id_dict[goods_code]
                can_order_stock = goods_qty_change.can_order_stock
                stocks.push({
                    'product_id': product_id,
                    'stock': can_order_stock
                })

        seller_api = SELLER_API(shop_id)
        params = {
            'stocks': stocks,
            'warehosue_id': warehosue_id
        }
        seller_resp = seller_api.update_stock(params)

        if seller_resp:
            for stock_item in seller_resp:
                shopsku_obj = ShopskuModel.objects.filter(openid=celeryuser['openid'], is_delete=False, shop_id=shop_id,
                                                            platform_id=stock_item['product_id']).first()
                if shopsku_obj:
                    shopsku_obj.sync_status = stock_item['status']
                    shopsku_obj.sync_message = stock_item['message']
                    shopsku_obj.sync_time = datetime.now()
                    shopsku_obj.save()


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



