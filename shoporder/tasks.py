import json
import requests
from celery import shared_task, uuid, chord
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
    time_postfix = default_now.strftime("%Y%m%d%H%M%S")
    # remove first 2 chars to make sure the time_postfix' length is 12.
    # for example: 20240127094800 to 240127094800
    time_postfix = time_postfix[2:]
    start_time = time.time()
    celeryuser = get_user(name, password)
    openid = celeryuser['openid']
    parent_id = self.request.id
    staff_obj = StaffModel.objects.filter(staff_name=str(name)).first()
    staff_id = staff_obj.id
    shop_list = ShopModel.objects.filter(openid=openid, is_delete=False)
    tasks = []

    for shop in shop_list:
        shop_id = shop.id
        task_id = uuid()
        # 43685fdc-7295-423e-94e6-2116f2a597e5 to 43685fdc-7295-423e-94e6-240127094800
        task_id = re.sub('[^-]+$', time_postfix, task_id)
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
    default_now = datetime.now()
    time_postfix = default_now.strftime("%Y%m%d%H%M%S")
    # remove first 2 chars to make sure the time_postfix' length is 12.
    # for example: 20240127094800 to 240127094800
    time_postfix = time_postfix[2:]
    start_time = time.time()
    celeryuser = get_user(name, password)
    openid = celeryuser['openid']
    parent_id = self.request.id
    staff_obj = StaffModel.objects.filter(staff_name=str(name)).first()
    staff_id = staff_obj.id
    shop_list = ShopModel.objects.filter(openid=openid, is_delete=False)
    tasks = []

    for shop in shop_list:
        shop_id = shop.id
        task_id = uuid()
        # 43685fdc-7295-423e-94e6-2116f2a597e5 to 43685fdc-7295-423e-94e6-240127094800
        task_id = re.sub('[^-]+$', time_postfix, task_id)
        task_order_update_by_shopid.apply_async((shop_id, staff_id, parent_id, celeryuser), task_id=task_id)
        tasks.append(task_id)

    processing_time = time.time() - start_time
    logger.info(f'task_order_update, processing_time: {processing_time:.6f} seconds')

    return {
        'tasks': tasks,
        'status': 'success',
        'start_time': default_now.strftime("%Y-%m-%dT%H:%M:%SZ"),
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
    handle_init_shoporder(shop, celeryuser, staff_id, since=since, to=to, status=status)

    processing_time = time.time() - start_time
    logger.info(f'task_order_init_by_shopid for shop_id: {shop_id}, processing_time: {processing_time:.6f} seconds')

    return {
        'parent_id': parent_id,
        'shop_id': shop_id,
        'status': 'success',
        'processing_time': f'{processing_time:.6f} seconds'
    }

@shared_task(name='task_order_update_by_shopid')
def task_order_update_by_shopid(shop_id, staff_id, parent_id, celeryuser):
    start_time = time.time()
    shop = ShopModel.objects.filter(openid=celeryuser['openid'], id=str(shop_id), is_delete=False).first()
    shop_order_list = ListModel.objects.filter(Q(openid=celeryuser['openid'], shop_id=shop_id, is_delete=False) &
                                               ~Q(status=Status.Delivered)
                                               ).order_by('order_time')
    shop_order_first = shop_order_list.first()
    shop_order_last = shop_order_list.last()

    max_days = 30
    to = datetime.now()
    since = to + relativedelta(days=-max_days)
    to  = to.strftime("%Y-%m-%dT%H:%M:%SZ")
    since = since.strftime("%Y-%m-%dT%H:%M:%SZ")
    if shop_order_first:
        during_time = shop_order_last.order_time - shop_order_first.order_time
        # update order in 30 days at most.
        if during_time.total_seconds() < max_days * 24 * 3600:
            since = shop_order_first.order_time + relativedelta(days=-1)
            to = shop_order_last.order_time + relativedelta(days=1)
            since = since.strftime("%Y-%m-%dT%H:%M:%SZ")
            to = to.strftime("%Y-%m-%dT%H:%M:%SZ")

    # the shop_list has only one element at most.
    # update order
    handle_update_shoporder(shop, celeryuser, staff_id, since=since, to=to, status='')

    processing_time = time.time() - start_time
    logger.info(f'task_order_update_by_shopid for shop_id: {shop_id}, processing_time: {processing_time:.6f} seconds')

    return {
        'parent_id': parent_id,
        'shop_id': shop_id,
        'status': 'success',
        'processing_time': f'{processing_time:.6f} seconds'
    }

def handle_init_shoporder(shop, celeryuser, staff_id, **args):
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

def handle_update_shoporder(shop, celeryuser, staff_id, **args):
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
            platform_id = item['platform_id']
            shop_order = ListModel.objects.filter(openid=celeryuser['openid'], shop_id=shop_id, platform_id=platform_id, is_delete=False).first()
            if shop_order is None:
                # logger.info(f'Can not find shop order for shop_id: {shop_id}, platform_id: {platform_id}')
                continue
            url = f'{settings.INNER_URL}/shoporder/{shop_order.id}/'
            req_data = item
            headers = {
                'Authorization': f"Bearer {celeryuser['access_token']}",
                'Token': celeryuser['openid'],
                'Operator': str(staff_id)
            }

            response = requests.put(url, json=req_data, headers=headers)
            str_response = response.content.decode('UTF-8')
            json_response = json.loads(str_response)
            json_response_status = json_response.get('status_code')
            if response.status_code != 200 or (json_response_status and json_response_status != 200):
                # response.content: { status_code: 5xx, detial: 'xxx' }
                logger.info(f'task update order {platform_id} to {args["status"]} failed, response: {json_response}')
            processing_time = time.time() - start_time
            if processing_time > max_processing_time:
                max_processing_time = processing_time

        if seller_resp is None:
            break
        if not seller_resp.get('has_next', False):
            break
        offset = seller_resp['next']

    logger.info(f'task handle update order for shop_id: {shop_id}, count: {count}, max_processing_time: {max_processing_time:.6f} seconds')

def order_manual_init(data, celeryuser):
    default_now = datetime.now()
    time_postfix = default_now.strftime("%Y%m%d%H%M%S")
    # remove first 2 chars to make sure the time_postfix' length is 12.
    # for example: 20240127094800 to 240127094800
    time_postfix = time_postfix[2:]
    start_time = time.time()
    openid = celeryuser['openid']
    # create parent_id
    task_id = uuid()
    # 43685fdc-7295-423e-94e6-2116f2a597e5 to 43685fdc-7295-423e-94e6-240127094800
    task_id = re.sub('[^-]+$', time_postfix, task_id)
    parent_id = task_id
    staff_obj = StaffModel.objects.filter(staff_name=celeryuser['name']).first()
    staff_id = staff_obj.id

    shop_id = data.get('shop_id')
    if shop_id:
        shop_list = ShopModel.objects.filter(openid=celeryuser['openid'], id=str(shop_id), is_delete=False)
    else:
        shop_list = ShopModel.objects.filter(openid=celeryuser['openid'], is_delete=False)

    task_sig_list = []
    for shop_obj in shop_list:
        shop_id = shop_obj.id
        task_id = uuid()
        # 43685fdc-7295-423e-94e6-2116f2a597e5 to 43685fdc-7295-423e-94e6-240127094800
        task_id = re.sub('[^-]+$', time_postfix, task_id)
        task_sig = task_order_manual_init_by_shopid.s(shop_id, staff_id, parent_id, data, celeryuser).set(task_id=str(task_id))
        task_sig_list.append(task_sig)

    task_id = uuid()
    # 43685fdc-7295-423e-94e6-2116f2a597e5 to 43685fdc-7295-423e-94e6-240127094800
    task_id = re.sub('[^-]+$', time_postfix, task_id)
    callback_sig = task_order_manual_init_callback.s(staff_id, parent_id, celeryuser).set(task_id=str(task_id))
    res = chord(task_sig_list, callback_sig)()

    processing_time = time.time() - start_time
    logger.info(f'manual init order for shop_id: {shop_id}, processing_time: {processing_time:.6f} seconds')

    return res.id

@shared_task(name='task_order_manual_init_by_shopid')
def task_order_manual_init_by_shopid(shop_id, staff_id, parent_id, data, celeryuser):
    start_time = time.time()
    since = data.get('since')
    to = data.get('to')

    shop = ShopModel.objects.filter(openid=celeryuser['openid'], id=str(shop_id), is_delete=False).first()
    # init Awaiting_Review order
    status = Status.Awaiting_Review
    handle_init_shoporder(shop, celeryuser, staff_id, since=since, to=to, status=status)
    # init Awaiting_Deliver order
    status = Status.Awaiting_Deliver
    handle_init_shoporder(shop, celeryuser, staff_id, since=since, to=to, status=status)

    processing_time = time.time() - start_time
    logger.info(f'task_order_manual_init_by_shopid for shop_id: {shop_id}, processing_time: {processing_time:.6f} seconds')

    return {
        'parent_id': parent_id,
        'shop_id': shop_id,
        'status': 'success',
        'processing_time': f'{processing_time:.6f} seconds'
    }

@shared_task(name='task_order_manual_init_callback')
def task_order_manual_init_callback(ret, staff_id, parent_id, celeryuser):
    return {
        'parent_id': parent_id,
        'status': 'success'
    }

def order_manual_update(data, celeryuser):
    default_now = datetime.now()
    time_postfix = default_now.strftime("%Y%m%d%H%M%S")
    # remove first 2 chars to make sure the time_postfix' length is 12.
    # for example: 20240127094800 to 240127094800
    time_postfix = time_postfix[2:]
    start_time = time.time()
    openid = celeryuser['openid']
    # create parent_id
    task_id = uuid()
    # 43685fdc-7295-423e-94e6-2116f2a597e5 to 43685fdc-7295-423e-94e6-240127094800
    task_id = re.sub('[^-]+$', time_postfix, task_id)
    parent_id = task_id
    staff_obj = StaffModel.objects.filter(staff_name=celeryuser['name']).first()
    staff_id = staff_obj.id

    shop_id = data.get('shop_id')
    if shop_id:
        shop_list = ShopModel.objects.filter(openid=celeryuser['openid'], id=str(shop_id), is_delete=False)
    else:
        shop_list = ShopModel.objects.filter(openid=celeryuser['openid'], is_delete=False)

    task_sig_list = []
    for shop_obj in shop_list:
        shop_id = shop_obj.id
        task_id = uuid()
        # 43685fdc-7295-423e-94e6-2116f2a597e5 to 43685fdc-7295-423e-94e6-240127094800
        task_id = re.sub('[^-]+$', time_postfix, task_id)
        task_sig = task_order_manual_update_by_shopid.s(shop_id, staff_id, parent_id, data, celeryuser).set(task_id=str(task_id))
        task_sig_list.append(task_sig)

    task_id = uuid()
    # 43685fdc-7295-423e-94e6-2116f2a597e5 to 43685fdc-7295-423e-94e6-240127094800
    task_id = re.sub('[^-]+$', time_postfix, task_id)
    callback_sig = task_order_manual_update_callback.s(staff_id, parent_id, celeryuser).set(task_id=str(task_id))
    res = chord(task_sig_list, callback_sig)()

    processing_time = time.time() - start_time
    logger.info(f'manual update order for shop_id: {shop_id}, processing_time: {processing_time:.6f} seconds')

    return res.id

@shared_task(name='task_order_manual_update_by_shopid')
def task_order_manual_update_by_shopid(shop_id, staff_id, parent_id, data, celeryuser):
    start_time = time.time()
    since = data.get('since')
    to = data.get('to')

    shop = ShopModel.objects.filter(openid=celeryuser['openid'], id=str(shop_id), is_delete=False).first()
    handle_update_shoporder(shop, celeryuser, staff_id, since=since, to=to, status='')

    processing_time = time.time() - start_time
    logger.info(f'task_order_manual_update_by_shopid for shop_id: {shop_id}, processing_time: {processing_time:.6f} seconds')

    return {
        'parent_id': parent_id,
        'shop_id': shop_id,
        'status': 'success',
        'processing_time': f'{processing_time:.6f} seconds'
    }

@shared_task(name='task_order_manual_update_callback')
def task_order_manual_update_callback(ret, staff_id, parent_id, celeryuser):
    return {
        'parent_id': parent_id,
        'status': 'success'
    }

@app.task(bind=True, name='task_label_update')
def task_label_update(self, name, password):
    default_now = datetime.now()
    time_postfix = default_now.strftime("%Y%m%d%H%M%S")
    # remove first 2 chars to make sure the time_postfix' length is 12.
    # for example: 20240127094800 to 240127094800
    time_postfix = time_postfix[2:]
    start_time = time.time()
    celeryuser = get_user(name, password)
    openid = celeryuser['openid']
    parent_id = self.request.id
    staff_obj = StaffModel.objects.filter(staff_name=str(name)).first()
    staff_id = staff_obj.id
    shop_list = ShopModel.objects.filter(openid=openid, is_delete=False)
    tasks = []

    for shop in shop_list:
        shop_id = shop.id
        task_id = uuid()
        # 43685fdc-7295-423e-94e6-2116f2a597e5 to 43685fdc-7295-423e-94e6-240127094800
        task_id = re.sub('[^-]+$', time_postfix, task_id)
        task_label_update_by_shopid.apply_async((shop_id, staff_id, parent_id, celeryuser), task_id=task_id)
        tasks.append(task_id)

    processing_time = time.time() - start_time
    logger.info(f'task_label_update, processing_time: {processing_time:.6f} seconds')

    return {
        'tasks': tasks,
        'status': 'success',
        'start_time': default_now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        'processing_time': f'{processing_time:.6f} seconds'
    }


def label_manual_update(order_id_list, celeryuser):
    default_now = datetime.now()
    time_postfix = default_now.strftime("%Y%m%d%H%M%S")
    # remove first 2 chars to make sure the time_postfix' length is 12.
    # for example: 20240127094800 to 240127094800
    time_postfix = time_postfix[2:]
    start_time = time.time()
    openid = celeryuser['openid']
    # create parent_id
    task_id = uuid()
    # 43685fdc-7295-423e-94e6-2116f2a597e5 to 43685fdc-7295-423e-94e6-240127094800
    task_id = re.sub('[^-]+$', time_postfix, task_id)
    parent_id = task_id
    staff_obj = StaffModel.objects.filter(staff_name=celeryuser['name']).first()
    staff_id = staff_obj.id

    shops = {}
    order_id_list = list(set(order_id_list))
    for order_id in order_id_list:
        # find related shops
        shoporder_obj = ListModel.objects.filter(openid=openid, is_delete=False, id=order_id).first()
        if shoporder_obj is None:
            continue
        if shoporder_obj.order_label:
            continue
        shop = shoporder_obj.shop
        if not shop.is_delete:
            if shop.id not in shops:
                shops[shop.id] = []
            shops[shop.id].append(shoporder_obj.id)

    task_sig_list = []
    for shop_id in list(shops.keys()):
        shoporder_id_list = shops.get(shop_id, [])
        task_id = uuid()
        # 43685fdc-7295-423e-94e6-2116f2a597e5 to 43685fdc-7295-423e-94e6-240127094800
        task_id = re.sub('[^-]+$', time_postfix, task_id)
        task_sig = task_label_manual_update_by_shopid.s(shop_id, staff_id, parent_id, shoporder_id_list, celeryuser).set(task_id=str(task_id))
        task_sig_list.append(task_sig)

    task_id = uuid()
    # 43685fdc-7295-423e-94e6-2116f2a597e5 to 43685fdc-7295-423e-94e6-240127094800
    task_id = re.sub('[^-]+$', time_postfix, task_id)
    callback_sig = task_label_manual_update_callback.s(staff_id, parent_id, celeryuser).set(task_id=str(task_id))
    res = chord(task_sig_list, callback_sig)()

    processing_time = time.time() - start_time
    logger.info(f'label_manual_update, processing_time: {processing_time:.6f} seconds')

    return res.id

@shared_task(name='task_label_update_by_shopid')
def task_label_update_by_shopid(shop_id, staff_id, parent_id, celeryuser):
    start_time = time.time()

    # only update awaiting_deliver order's label for performance concern. If need to get other status order, please manual update it.
    shoporder_list = ListModel.objects.filter(openid=celeryuser['openid'], is_delete=False, shop_id=shop_id, order_label='',
                                              status=Status.Awaiting_Deliver)
    shoporder_id_list = [item.id for item in shoporder_list]

    seller_api = SELLER_API(shop_id)
    for order_id in shoporder_id_list:
        params = {
            'order_id': order_id,
        }
        file_path = seller_api.get_label(params)
        if not file_path:
            continue

        url = f'{settings.INNER_URL}/shoporder/{order_id}/'
        req_data = {
            'order_label': file_path
        }
        headers = {
            'Authorization': f"Bearer {celeryuser['access_token']}",
            'Token': celeryuser['openid'],
            'Operator': str(staff_id)
        }

        response = requests.patch(url, json=req_data, headers=headers)
        str_response = response.content.decode('UTF-8')
        json_response = json.loads(str_response)
        json_response_status = json_response.get('status_code')
        if response.status_code != 200 or (json_response_status and json_response_status != 200):
            # response.content: { status_code: 5xx, detial: 'xxx' }
            logger.info(f'task label of orderid: {order_id} update failed, response: {json_response}')


    processing_time = time.time() - start_time
    logger.info(f'task_label_update_by_shopid for shop_id: {shop_id}, processing_time: {processing_time:.6f} seconds')

    return {
        'parent_id': parent_id,
        'shop_id': shop_id,
        'status': 'success',
        'processing_time': f'{processing_time:.6f} seconds'
    }

@shared_task(name='task_label_manual_update_by_shopid')
def task_label_manual_update_by_shopid(shop_id, staff_id, parent_id, shoporder_id_list, celeryuser):
    start_time = time.time()

    seller_api = SELLER_API(shop_id)
    for order_id in shoporder_id_list:
        params = {
            'order_id': order_id,
        }
        file_path = seller_api.get_label(params)
        if not file_path:
            continue

        url = f'{settings.INNER_URL}/shoporder/{order_id}/'
        req_data = {
            'order_label': file_path
        }
        headers = {
            'Authorization': f"Bearer {celeryuser['access_token']}",
            'Token': celeryuser['openid'],
            'Operator': str(staff_id)
        }

        response = requests.patch(url, json=req_data, headers=headers)
        str_response = response.content.decode('UTF-8')
        json_response = json.loads(str_response)
        json_response_status = json_response.get('status_code')
        if response.status_code != 200 or (json_response_status and json_response_status != 200):
            # response.content: { status_code: 5xx, detial: 'xxx' }
            logger.info(f'task label of orderid: {order_id} manual update failed, response: {json_response}')

    processing_time = time.time() - start_time
    logger.info(f'task_stock_manual_update_by_shopid for shop_id: {shop_id}, processing_time: {processing_time:.6f} seconds')

    return {
        'parent_id': parent_id,
        'shop_id': shop_id,
        'status': 'success',
        'processing_time': f'{processing_time:.6f} seconds'
    }

@shared_task(name='task_label_manual_update_callback')
def task_label_manual_update_callback(ret, staff_id, parent_id, celeryuser):
    return {
        'parent_id': parent_id,
        'status': 'success'
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
        'user_id': user_id,
        'name': name
    }
    cache.set(f'celeryuser:{name}', celeryuser)
    return celeryuser