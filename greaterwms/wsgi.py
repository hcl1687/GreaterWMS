"""
WSGI config for django_wms project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

ENV = os.environ.get("GREATERWMS_ENV", "prod")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greaterwms.settings.{0}'.format(ENV))

application = get_wsgi_application()
