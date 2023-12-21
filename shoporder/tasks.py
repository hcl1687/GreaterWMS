import json
import requests
from celery import shared_task, uuid
from django.core.cache import cache
import logging
from django.conf import settings
import jwt
from datetime import datetime
from dateutil.relativedelta import relativedelta
from shop.models import ListModel as ShopModel
from greaterwms.celery import app
import base64
import time

logger = logging.getLogger(__name__)

@shared_task
def task_send_dd_text(url, msg, atMoblies, atAll="flase"):
    """
    发送钉钉提醒
    :param url:
    :param msg:
    :param atMoblies:
    :param atAll:
    :return:
    """
    body = {
        "msgtype": "text",
        "text": {
            "content": msg
        },
        "at": {
            "atMobiles": atMoblies,
            "isAtAll": atAll
        }


    }
    headers = {'content-type': 'application/json',
               'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0'}
    # r = requests.post(url, headers=headers, data=json.dumps(body))
    print(body['text']['content'])

@app.task(bind=True, name='task_order_init')
def task_order_init(self, name, password):
    celeryuser = cache.get(f'celeryuser:{name}')
    if celeryuser is None:
        celeryuser = get_user(name, password)
    else:
        access_token = celeryuser['access_token']
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        exp = int(decoded['exp'])
        now = datetime.now().timestamp()
        # if the span between exp and now is less than 1 hour, relogin
        if exp - now < 3600:
            celeryuser = get_user(name, password)

    openid = celeryuser['openid']
    shop_list = ShopModel.objects.filter(openid=openid, is_delete=False)
    tasks = []
    for shop in shop_list:
        shop_id = shop.id
        task_id = uuid()
        task_order_init_by_shopid.apply_async((shop_id, celeryuser), task_id=task_id)
        tasks.append(task_id)

    return {
        'tasks': tasks,
        'status': 'success'
    }

@shared_task(name='task_order_init_by_shopid')
def task_order_init_by_shopid(shop_id, celeryuser):
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
        'Operator': str(celeryuser['user_id'])
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