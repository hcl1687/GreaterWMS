from django.db import models

class ListModel(models.Model):
    shop_name = models.CharField(max_length=255, verbose_name="Shop Name")
    shop_type = models.CharField(max_length=255, verbose_name="Shop Type")
    shop_data = models.CharField(max_length=1024, verbose_name="Shop Data")
    sync = models.BooleanField(default=False, verbose_name='Sync Store')
    supplier = models.CharField(max_length=255, verbose_name="Supplier")
    openid = models.CharField(max_length=255, verbose_name="Openid")
    creater = models.CharField(max_length=255, verbose_name="Who Created")
    is_delete = models.BooleanField(default=False, verbose_name='Delete Label')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="Create Time")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="Update Time")
    class Meta:
        db_table = 'shop'
        verbose_name = 'Shop'
        verbose_name_plural = "Shop"
        ordering = ['shop_name']
