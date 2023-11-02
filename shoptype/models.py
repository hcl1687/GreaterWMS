from django.db import models

class ListModel(models.Model):
    shop_type = models.CharField(max_length=32, verbose_name="Shop type")
    shop_schema = models.CharField(max_length=1024, verbose_name="Shop schema")
    creater = models.CharField(max_length=255, verbose_name="Who created")
    openid = models.CharField(max_length=255, verbose_name="Openid")
    is_delete = models.BooleanField(default=False, verbose_name='Delete Label')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="Create Time")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="Update Time")

    class Meta:
        db_table = 'shoptype'
        verbose_name = 'Shop Type'
        verbose_name_plural = "Shop Type"
        ordering = ['shop_type']
