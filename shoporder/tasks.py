import json
import requests
from celery import shared_task, uuid
from django.core.cache import cache
import logging
from django.conf import settings
from datetime import datetime
from dateutil.relativedelta import relativedelta
from shop.models import ListModel as ShopModel
from greaterwms.celery import app
import time
from .models import ListModel
from django.db.models import Q
from .status import Status
from staff.models import ListModel as StaffModel
from utils.seller_api import SELLER_API
import re

logger = logging.getLogger(__name__)

@app.task(bind=True, name='task_order_init')
def task_order_init(self, name, password, *args):
    default_now = datetime.now()
    time_prefix = default_now.strftime("%H:%M:%S")
    start_time = time.time()
    celeryuser = get_user(name, password)
    openid = celeryuser['openid']
    parent_id = self.request.id
    staff_obj = StaffModel.objects.filter(staff_name=str(name)).first()
    staff_id = staff_obj.id
    shop_list = ShopModel.objects.filter(openid=openid, is_delete=False)
    tasks = []
    count = 1
    if len(args) > 0:
        count = int(args[0])

    for i in range(count):
        for shop in shop_list:
            shop_id = shop.id
            task_id = uuid()
            # 43685fdc-7295-423e-94e6-2116f2a597e5 to 12:01:30-7295-423e-94e6-2116f2a597e5
            task_id = re.sub('^[^-]+', time_prefix, task_id)
            task_order_init_by_shopid.apply_async((shop_id, staff_id, parent_id, celeryuser), task_id=task_id)
            tasks.append(task_id)

    processing_time = time.time() - start_time
    logger.info(f'task_order_init, processing_time: {processing_time:.6f} seconds')

    return {
        'tasks': tasks,
        'status': 'success',
        'start_time': default_now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        'processing_time': f'{processing_time:.6f} seconds'
    }

@app.task(bind=True, name='task_order_update')
def task_order_update(self, name, password):
    start_time = time.time()
    celeryuser = get_user(name, password)
    openid = celeryuser['openid']
    staff_obj = StaffModel.objects.filter(staff_name=str(name)).first()
    staff_id = staff_obj.id
    shop_order_list = ListModel.objects.filter(Q(openid=openid, is_delete=False) &
                                               (Q(status=Status.Awaiting_Review) | Q(status=Status.Awaiting_Deliver))
                                               ).order_by('order_time')
    shop_order_first = shop_order_list.first()
    shop_order_last = shop_order_list.last()

    to = datetime.now()
    since = to + relativedelta(days=-7)
    to = to.strftime("%Y-%m-%dT%H:%M:%SZ")
    since = since.strftime("%Y-%m-%dT%H:%M:%SZ")
    if shop_order_first:
        since = shop_order_first.order_time + relativedelta(days=-1)
        since = since.strftime("%Y-%m-%dT%H:%M:%SZ")
    if shop_order_last:
        to = shop_order_last.order_time + relativedelta(days=1)
        to = to.strftime("%Y-%m-%dT%H:%M:%SZ")

    item = {
        'since': since,
        'to': to
    }
    url = f'{settings.INNER_URL}/shoporder/update/'
    req_data = item
    headers = {
        'Authorization': f"Bearer {celeryuser['access_token']}",
        'Token': celeryuser['openid'],
        'Operator': str(staff_id)
    }

    response = requests.post(url, json=req_data, headers=headers)
    str_response = response.content.decode('UTF-8')
    json_response = json.loads(str_response)
    json_response_status = json_response.get('status_code')
    if response.status_code != 200 or (json_response_status and json_response_status != 200):
        # response.content: { status_code: 5xx, detial: 'xxx' }
        logger.error(f'task update order failed, response: {str_response}')
        return {
            'status': 'failed',
            'response': str_response
        }

    processing_time = time.time() - start_time
    logger.info(f'task_order_update, processing_time: {processing_time:.6f} seconds')

    return {
        'status': 'success',
        'processing_time': f'{processing_time:.6f} seconds'
    }

@shared_task(name='task_order_init_by_shopid')
def task_order_init_by_shopid(shop_id, staff_id, parent_id, celeryuser):
    start_time = time.time()
    to = datetime.now()
    # search orders since 10 minutes ago to now
    since = to + relativedelta(minutes=-10)
    to = to.strftime ("%Y-%m-%dT%H:%M:%SZ")
    since = since.strftime ("%Y-%m-%dT%H:%M:%SZ")

    shop = ShopModel.objects.filter(openid=celeryuser['openid'], id=str(shop_id), is_delete=False).first()
    status = Status.Awaiting_Review
    handle_shoporder(shop, celeryuser, staff_id, since=since, to=to, status=status)

    processing_time = time.time() - start_time
    logger.info(f'task_order_init_by_shopid for shop_id: {shop_id}, processing_time: {processing_time:.6f} seconds')

    return {
        'parent_id': parent_id,
        'shop_id': shop_id,
        'status': 'success',
        'processing_time': f'{processing_time:.6f} seconds'
    }

def handle_shoporder(shop, celeryuser, staff_id, **args):
    shop_id = shop.id
    shopwarehouse_list = shop.shopwarehouse.filter(is_delete=False)
    warehosue_id = []
    for warehouse in shopwarehouse_list:
        warehosue_id.append(warehouse.platform_id)

    if len(warehosue_id) == 0:
        return

    seller_api = SELLER_API(shop_id)
    count = 0
    max_processing_time = 0
    offset = 0
    while True:
        params = {
            'offset': offset,
            'status':args['status'],
            'since': args['since'],
            'to': args['to'],
            'warehouse_id': warehosue_id
        }
        seller_resp = seller_api.get_orders(params)
        seller_resp_items = seller_resp.get('items', [])
        count = count + len(seller_resp_items)
        for item in seller_resp_items:
            start_time = time.time()
            item['shop'] = shop_id
            url = f'{settings.INNER_URL}/shoporder/'
            req_data = item
            headers = {
                'Authorization': f"Bearer {celeryuser['access_token']}",
                'Token': celeryuser['openid'],
                'Operator': str(staff_id)
            }

            response = requests.post(url, json=req_data, headers=headers)
            str_response = response.content.decode('UTF-8')
            json_response = json.loads(str_response)
            json_response_status = json_response.get('status_code')
            if response.status_code != 200 or (json_response_status and json_response_status != 200):
                # response.content: { status_code: 5xx, detial: 'xxx' }
                logger.error(f'task init Awaiting_Review order failed, response: {str_response}')
            processing_time = time.time() - start_time
            if processing_time > max_processing_time:
                max_processing_time = processing_time

        if seller_resp is None:
            break
        if not seller_resp.get('has_next', False):
            break
        offset = seller_resp['next']

    logger.info(f'task handle init order for shop_id: {shop_id}, count: {count}, max_processing_time: {max_processing_time:.6f} seconds')


def get_user(name, password):
    item = {
        'name': name,
        'password': password
    }
    url = f'{settings.INNER_URL}/login/'
    req_data = item
    headers = {}

    response = requests.post(url, json=req_data, headers=headers)
    str_response = response.content.decode('UTF-8')
    json_response = json.loads(str_response)
    json_response_status = json_response.get('status_code')
    if response.status_code != 200 or (json_response_status and json_response_status != 200):
        # response.content: { status_code: 5xx, detial: 'xxx' }
        logger.error(f'login failed, response: {str_response}')
    data = json_response.get('data', {})
    access_token = data.get('access_token')
    refresh_token = data.get('refresh_token')
    openid = data.get('openid')
    user_id = data.get('user_id')
    celeryuser = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'openid': openid,
        'user_id': user_id
    }
    cache.set(f'celeryuser:{name}', celeryuser)
    return celeryuser