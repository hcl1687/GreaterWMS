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
from staff.models import ListModel as StaffModel
from utils.seller_api import SELLER_API
import re
from django.core.cache import cache
from utils.shopsku import Shopsku
from utils.cache_tool import CacheTool
from shopsku.models import ListModel as ShopskuModel

logger = logging.getLogger(__name__)

@app.task(bind=True, name='task_stock_patch')
def task_stock_patch(self, name, password, *args):
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
    tasks = []
    goods_code_dict = CacheTool.lock_and_clear_sku()
    goods_code_list = list(goods_code_dict.keys())
    shops = {}
    for goods_code in goods_code_list:
        # find related shops
        shopsku_list = ShopskuModel.objects.filter(openid=openid, is_delete=False, goods_code=goods_code)
        for shopsku_item in shopsku_list:
            shop = shopsku_item.shop
            if shop is None:
                continue
            if not shop.is_delete and shop.sync:
                if shop.id not in shops:
                    shops[shop.id] = []
                shops[shop.id].append(goods_code)

    for shop_id in list(shops.keys()):
        goods_code_list = shops.get(shop_id, [])
        task_id = uuid()
        # 43685fdc-7295-423e-94e6-2116f2a597e5 to 43685fdc-7295-423e-94e6-240127094800
        task_id = re.sub('[^-]+$', time_postfix, task_id)
        task_stock_patch_by_shopid.apply_async((shop_id, staff_id, parent_id, goods_code_list, celeryuser), task_id=task_id)
        tasks.append(task_id)

    processing_time = time.time() - start_time
    logger.info(f'task_stock_patch, processing_time: {processing_time:.6f} seconds')

    return {
        'tasks': tasks,
        'status': 'success',
        'start_time': default_now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        'processing_time': f'{processing_time:.6f} seconds'
    }

@app.task(bind=True, name='task_stock_update')
def task_stock_update(self, name, password):
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
    shop_list = ShopModel.objects.filter(openid=openid, is_delete=False, sync=True)
    tasks = []

    for shop in shop_list:
        shop_id = shop.id
        task_id = uuid()
        # 43685fdc-7295-423e-94e6-2116f2a597e5 to 43685fdc-7295-423e-94e6-240127094800
        task_id = re.sub('[^-]+$', time_postfix, task_id)
        task_stock_update_by_shopid.apply_async((shop_id, staff_id, parent_id, celeryuser), task_id=task_id)
        tasks.append(task_id)

    processing_time = time.time() - start_time
    logger.info(f'task_stock_update, processing_time: {processing_time:.6f} seconds')

    return {
        'tasks': tasks,
        'status': 'success',
        'start_time': default_now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        'processing_time': f'{processing_time:.6f} seconds'
    }

def stock_manual_update(goods_code_list, celeryuser):
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
    for goods_code in goods_code_list:
        # find related shops
        shopsku_list = ShopskuModel.objects.filter(openid=openid, is_delete=False, goods_code=goods_code)
        for shopsku_item in shopsku_list:
            shop = shopsku_item.shop
            if shop is None:
                continue
            if not shop.is_delete and shop.sync:
                if shop.id not in shops:
                    shops[shop.id] = []
                shops[shop.id].append(goods_code)

    task_sig_list = []
    for shop_id in list(shops.keys()):
        goods_code_list = shops.get(shop_id, [])
        task_id = uuid()
        # 43685fdc-7295-423e-94e6-2116f2a597e5 to 43685fdc-7295-423e-94e6-240127094800
        task_id = re.sub('[^-]+$', time_postfix, task_id)
        task_sig = task_stock_manual_update_by_shopid.s(shop_id, staff_id, parent_id, goods_code_list, celeryuser).set(task_id=str(task_id))
        task_sig_list.append(task_sig)

    task_id = uuid()
    # 43685fdc-7295-423e-94e6-2116f2a597e5 to 43685fdc-7295-423e-94e6-240127094800
    task_id = re.sub('[^-]+$', time_postfix, task_id)
    callback_sig = task_stock_manual_update_callback.s(staff_id, parent_id, celeryuser).set(task_id=str(task_id))
    res = chord(task_sig_list, callback_sig)()

    processing_time = time.time() - start_time
    logger.info(f'stock_manual_update, processing_time: {processing_time:.6f} seconds')

    return res.id

@shared_task(name='task_stock_patch_by_shopid')
def task_stock_patch_by_shopid(shop_id, staff_id, parent_id, goods_code_list, celeryuser):
    start_time = time.time()

    Shopsku.update_stock(shop_id, goods_code_list, celeryuser)

    processing_time = time.time() - start_time
    logger.info(f'task_stock_patch_by_shopid for shop_id: {shop_id}, processing_time: {processing_time:.6f} seconds')

    return {
        'parent_id': parent_id,
        'shop_id': shop_id,
        'status': 'success',
        'processing_time': f'{processing_time:.6f} seconds'
    }

@shared_task(name='task_stock_update_by_shopid')
def task_stock_update_by_shopid(shop_id, staff_id, parent_id, celeryuser):
    start_time = time.time()

    shopsku_list = ShopskuModel.objects.filter(openid=celeryuser['openid'], is_delete=False, shop_id=shop_id)
    goods_code_list = [item.goods_code for item in shopsku_list]
    Shopsku.update_stock(shop_id, goods_code_list, celeryuser)

    processing_time = time.time() - start_time
    logger.info(f'task_stock_update_by_shopid for shop_id: {shop_id}, processing_time: {processing_time:.6f} seconds')

    return {
        'parent_id': parent_id,
        'shop_id': shop_id,
        'status': 'success',
        'processing_time': f'{processing_time:.6f} seconds'
    }

@shared_task(name='task_stock_manual_update_by_shopid')
def task_stock_manual_update_by_shopid(shop_id, staff_id, parent_id, goods_code_list, celeryuser):
    start_time = time.time()

    Shopsku.update_stock(shop_id, goods_code_list, celeryuser)

    processing_time = time.time() - start_time
    logger.info(f'task_stock_manual_update_by_shopid for shop_id: {shop_id}, processing_time: {processing_time:.6f} seconds')

    return {
        'parent_id': parent_id,
        'shop_id': shop_id,
        'status': 'success',
        'processing_time': f'{processing_time:.6f} seconds'
    }

@shared_task(name='task_stock_manual_update_callback')
def task_stock_manual_update_callback(ret, staff_id, parent_id, celeryuser):
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