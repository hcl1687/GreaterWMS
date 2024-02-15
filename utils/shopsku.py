from shopsku.models import ListModel as ShopskuModel
from stock.models import StockListModel
from utils.seller_api import SELLER_API
import logging
from datetime import datetime
from shop.models import ListModel as ShopModel

logger = logging.getLogger(__name__)

class Shopsku(object):
    def update_stock(shop_id, goods_code_list, celeryuser, **args):
        shop = ShopModel.objects.filter(openid=celeryuser['openid'], id=str(shop_id), is_delete=False, sync=True).first()
        stock_threshold = shop.stock_threshold
        shopwarehouse_list = shop.shopwarehouse.filter(is_delete=False)
        warehosue_id_list = []
        for warehouse in shopwarehouse_list:
            warehosue_id_list.append(warehouse.platform_id)

        if len(warehosue_id_list) == 0:
            return
        
        warehosue_id = warehosue_id_list[0]

        # get product id
        product_id_dict = {}
        shopsku_list = ShopskuModel.objects.filter(openid=celeryuser['openid'], shop_id=shop_id, is_delete=False,
                                                goods_code__in=goods_code_list)
        for shopsku_item in shopsku_list:
            product_id_dict[shopsku_item.goods_code] = shopsku_item.platform_id

        # get latest stock
        stocks_dict = {}
        goods_qty_change_list = StockListModel.objects.filter(openid=celeryuser['openid'],
                                                            goods_code__in=goods_code_list)
        for goods_qty_change in goods_qty_change_list:
            goods_code = goods_qty_change.goods_code
            if goods_code in product_id_dict:
                product_id = product_id_dict[goods_code]
                can_order_stock = goods_qty_change.can_order_stock
                stocks_dict[product_id] = can_order_stock

        stocks = []
        for product_id in list(product_id_dict.values()):
            stock = 0
            if product_id in stocks_dict:
                stock = stocks_dict[product_id]

            # handle stock threshold
            if stock <= stock_threshold:
                stock = 0

            stocks.append({
                'product_id': product_id,
                'stock': stock
            })

        seller_api = SELLER_API(shop_id)
        params = {
            'stocks': stocks,
            'warehouse_id': warehosue_id
        }
        seller_resp = seller_api.update_stock(params)
        if seller_resp is None:
            return

        res_dict = {}
        for stock_item in seller_resp:
            res_dict[stock_item['product_id']] = stock_item
        
        product_id_list = list(res_dict.keys())
        shopsku_obj_list = ShopskuModel.objects.filter(openid=celeryuser['openid'], shop_id=shop_id, is_delete=False,
                                                            platform_id__in=product_id_list)
        for shopsku_obj in shopsku_obj_list:
            product_id = shopsku_obj.platform_id
            stock_item = res_dict[product_id]
            shopsku_obj.sync_status = stock_item['status']
            shopsku_obj.sync_message = stock_item['message']
            shopsku_obj.sync_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        ShopskuModel.objects.bulk_update(shopsku_obj_list, ['sync_status', 'sync_message', 'sync_time'])
