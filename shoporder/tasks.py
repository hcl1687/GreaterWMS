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

logger = logging.getLogger(__name__)

@app.task(bind=True, name='task_order_init')
def task_order_init(self, name, password, *args):
    start_time = time.time()
    celeryuser = get_user(name, password)
    openid = celeryuser['openid']
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
            task_order_init_by_shopid.apply_async((shop_id, staff_id, celeryuser), task_id=task_id)
            tasks.append(task_id)

    processing_time = time.time() - start_time
    logger.info(f'task_order_init, processing_time: {processing_time:.6f} seconds')

    return {
        'tasks': tasks,
        'status': 'success',
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

    default_to = datetime.now()
    default_since = default_to + relativedelta(days=-7)
    default_to = default_to.strftime("%Y-%m-%dT%H:%M:%SZ")
    default_since = default_since.strftime("%Y-%m-%dT%H:%M:%SZ")
    if shop_order_first:
        default_since = shop_order_first.order_time + relativedelta(days=-1)
        default_since = default_since.strftime("%Y-%m-%dT%H:%M:%SZ")
    if shop_order_last:
        default_to = shop_order_last.order_time + relativedelta(days=1)
        default_to = default_to.strftime("%Y-%m-%dT%H:%M:%SZ")

    item = {
        'since': default_since,
        'to': default_to
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
        logger.error(f'update order failed, response: {str_response}')
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
def task_order_init_by_shopid(shop_id, staff_id, celeryuser):
    start_time = time.time()
    default_now = datetime.now()
    default_since = default_now + relativedelta(days=-1)
    default_now = default_now.strftime ("%Y-%m-%dT%H:%M:%SZ")
    default_since = default_since.strftime ("%Y-%m-%dT%H:%M:%SZ")

    item = {
        'shop_id': shop_id,
        'mode': 'task',
        'since': default_since,
        'to': default_now
    }
    url = f'{settings.INNER_URL}/shoporder/init/'
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
        logger.error(f'init order failed for shop_id {shop_id}, response: {str_response}')
        return {
            'shop_id': shop_id,
            'status': 'failed',
            'response': str_response
        }
    
    processing_time = time.time() - start_time
    logger.info(f'task_order_init_by_shopid for shop_id: {shop_id}, processing_time: {processing_time:.6f} seconds')

    return {
        'shop_id': shop_id,
        'status': 'success',
        'processing_time': f'{processing_time:.6f} seconds'
    }


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