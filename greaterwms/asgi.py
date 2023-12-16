import os

from django.core.asgi import get_asgi_application
from utils.websocket import websocket_application
from myasgihandler.core import ASGIHandler
ENV = os.environ.get("GREATERWMS_ENV", "prod")
print(f'GREATERWMS_ENV: {ENV}')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greaterwms.settings.{0}'.format(ENV))

http_application = get_asgi_application()


async def application(scope, receive, send):
    if scope['type'] in ['http', 'https']:
        ASGIHandler.asgi_get_handler(scope)
        await http_application(scope, receive, send)
    elif scope['type'] in ['websocket']:
        await websocket_application(scope, receive, send)
    else:
        raise Exception('Unknown Type' + scope['type'])

