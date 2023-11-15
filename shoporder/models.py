from django.db import models
from shop.models import ListModel as ShopModel
from stock.models import StockBinModel

class ListModel(models.Model):
    platform_id = models.CharField(max_length=255, verbose_name="Platform Order ID")
    platform_warehouse_id = models.CharField(max_length=255, verbose_name="Platform Warehouse ID")
    dn_code = models.CharField(max_length=255, verbose_name="DN Code")
    order_data = models.CharField(max_length=8192, verbose_name="Order Data")
    status = models.BigIntegerField(default=1, verbose_name="Status")
    shop = models.ForeignKey(ShopModel, on_delete=models.CASCADE, related_name='shopsku')
    stockbin = models.ForeignKey(StockBinModel, on_delete=models.CASCADE, related_name='stockbin')
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
        ordering = ['platform_id']
