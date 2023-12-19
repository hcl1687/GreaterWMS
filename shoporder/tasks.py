import json
import requests
from celery import shared_task

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
