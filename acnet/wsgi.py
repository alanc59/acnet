"""
WSGI config for acnet project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application
sys.path.append("/home/pi/virtualenvs/acnetv/acnet")
sys.path.append("/home/pi/python")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'acnet.settings')


application = get_wsgi_application()
