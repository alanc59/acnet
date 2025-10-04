from django.conf import settings

def ap_settings(request):
    return {
        "AP_REFRESH_DOMAIN": settings.AP_REFRESH_DOMAIN,
    }
