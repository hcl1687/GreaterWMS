from django.db import models
from shop.models import ListModel as ShopModel
from stock.models import StockBinModel

class ListModel(models.Model):
    platform_id = models.CharField(max_length=255, verbose_name="Platform Order ID")
    platform_warehouse_id = models.CharField(max_length=255, verbose_name="Platform Warehouse ID")
    posting_number = models.CharField(max_length=255, verbose_name="Posting Number")
    dn_code = models.CharField(max_length=255, verbose_name="DN Code")
    order_data = models.TextField(verbose_name="Order Data")
    stockbin_data = models.CharField(max_length=255, verbose_name="Stockbin Data")
    order_time = models.DateTimeField(auto_now=False, blank=False, null=False, verbose_name="Order Time")
    status = models.BigIntegerField(default=1, verbose_name="Status")
    handle_status = models.BigIntegerField(default=1, verbose_name="Handle Status")
    handle_message = models.CharField(max_length=255, verbose_name="Handle Message")
    shop = models.ForeignKey(ShopModel, on_delete=models.CASCADE, related_name='shoporder')
    supplier = models.CharField(max_length=255, verbose_name="Supplier")
    openid = models.CharField(max_length=255, verbose_name="Openid")
    creater = models.CharField(max_length=255, verbose_name="Who Created")
    is_delete = models.BooleanField(default=False, verbose_name='Delete Label')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="Create Time")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="Update Time")

    class Meta:
        db_table = 'shoporder'
        verbose_name = 'Shop Order'
        verbose_name_plural = "Shop Order"
        ordering = ['id']
