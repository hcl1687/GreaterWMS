from django.db import models
from warehouse.models import ListModel as WarehosueModel
from shop.models import ListModel as ShopModel

class ListModel(models.Model):
    platform_id = models.CharField(max_length=255, verbose_name="Shop Warehouse id")
    platform_name = models.CharField(max_length=255, verbose_name="Shop Warehouse Name")
    warehouse = models.ForeignKey(WarehosueModel, blank=True, null=True, on_delete=models.SET_NULL, related_name='shopwarehouse')
    shop = models.ForeignKey(ShopModel, on_delete=models.CASCADE, related_name='shopwarehouse')
    supplier = models.CharField(max_length=255, verbose_name="Supplier")
    openid = models.CharField(max_length=255, verbose_name="Openid")
    creater = models.CharField(max_length=255, verbose_name="Who Created")
    is_delete = models.BooleanField(default=False, verbose_name='Delete Label')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="Create Time")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="Update Time")

    class Meta:
        db_table = 'shopwarehouse'
        verbose_name = 'Shop Warehouse'
        verbose_name_plural = "Shop Warehouse"
        ordering = ['platform_name']
