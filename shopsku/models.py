from django.db import models
from shop.models import ListModel as ShopModel

class ListModel(models.Model):
    platform_id = models.CharField(max_length=255, verbose_name="Platform ID")
    platform_sku = models.CharField(max_length=255, verbose_name="Platform SKU")
    goods_code = models.CharField(max_length=255, verbose_name="Goods code")
    shop = models.ForeignKey(ShopModel, on_delete=models.CASCADE, related_name='shopsku')
    supplier = models.CharField(max_length=255, verbose_name="Supplier")
    openid = models.CharField(max_length=255, verbose_name="Openid")
    creater = models.CharField(max_length=255, verbose_name="Who Created")
    is_delete = models.BooleanField(default=False, verbose_name='Delete Label')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="Create Time")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="Update Time")

    class Meta:
        db_table = 'shopsku'
        verbose_name = 'Shop Sku'
        verbose_name_plural = "Shop Sku"
        ordering = ['platform_sku']
