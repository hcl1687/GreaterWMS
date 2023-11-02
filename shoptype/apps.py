from django.apps import AppConfig
from django.db.models.signals import post_migrate
import json

class ShoptypeConfig(AppConfig):
    name = 'shoptype'

    def ready(self):
        post_migrate.connect(do_init_data, sender=self)

def do_init_data(sender, **kwargs):
    init_category()

def init_category():
    """
        :return:None
    """
    try:
        from .models import ListModel as ls
        ozon_schema = json.dumps({
            'fields': [{
                'filed': 'api_url',
                'type': 'input'
            }, {
                'filed': 'client_id',
                'type': 'input'
            }, {
                'filed': 'api_key',
                'type': 'input'
            }]
        })
        wibe_schema = json.dumps({
            'fields': [{
                'filed': 'api_url',
                'type': 'input'
            }, {
                'filed': 'api_key',
                'type': 'input'
            }]
        })
        yade_schema = json.dumps({
            'fields': [{
                'filed': 'api_url',
                'type': 'input'
            }, {
                'filed': 'token',
                'type': 'input'
            }, {
                'filed': 'shop_id',
                'type': 'input'
            }, {
                'filed': 'warehouse_id',
                'type': 'input'
            }]
        })

        if ls.objects.filter(openid__iexact='init_data').exists():
            if ls.objects.filter(openid__iexact='init_data').count() != 3:
                ls.objects.filter(openid__iexact='init_data').delete()
                init_data = [
                    ls(id=1, openid='init_data', shop_type='OZON', shop_schema=ozon_schema, creater='GreaterWMS'),
                    ls(id=2, openid='init_data', shop_type='WIBE', shop_schema=wibe_schema, creater='GreaterWMS'),
                    ls(id=3, openid='init_data', shop_type='YADE', shop_schema=yade_schema, creater='GreaterWMS'),
                ]
                ls.objects.bulk_create(init_data, batch_size=100)
        else:
            init_data = [
                ls(id=1, openid='init_data', shop_type='OZON', shop_schema=ozon_schema, creater='GreaterWMS'),
                ls(id=2, openid='init_data', shop_type='WIBE', shop_schema=wibe_schema, creater='GreaterWMS'),
                ls(id=3, openid='init_data', shop_type='YADE', shop_schema=yade_schema, creater='GreaterWMS'),
            ]
            ls.objects.bulk_create(init_data, batch_size=100)
    except Exception as e:
        print(e)
        pass
