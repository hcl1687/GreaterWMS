import json
import requests
from celery import shared_task
from django.core.cache import cache
import logging
import time
from django.conf import settings

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

@shared_task
def task_order_init(name, password):
    celeryuser = cache.get(f'celeryuser:{name}')
    if celeryuser is None:
        celeryuser = get_user(name, password)
    else:
        access_token = celeryuser['access_token']
        



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