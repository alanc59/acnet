"""
WSGI config for acnet project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import sys
#import site

#site.addsitedir('/usr/lib/python3/dist-packages')

sys.path.append("/home/pi/src/python/acnet")
sys.path.append("/home/pi/src/python")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'acnet.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
