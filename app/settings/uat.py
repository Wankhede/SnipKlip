from .base import *
from django.contrib.messages import constants as messages

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env('SECRET_KEY', 'replace-me-in-uat')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = get_env('DEBUG', False, bool)
FTP = get_env('FTP', False, bool)

SERVER = get_env('SERVER', 1, int)

allowed_hosts = get_env('ALLOWED_HOSTS', 'uat-backend.snipklip.in,uat.snipklip.in,206.189.136.106,127.0.0.1,testserver,localhost')
if allowed_hosts == '*':
    ALLOWED_HOSTS = ['*']
elif isinstance(allowed_hosts, str):
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts.split(',') if host.strip()]
else:
    ALLOWED_HOSTS = list(allowed_hosts)
"""SERVER variable is used to identify the servers
    Value:
        0: local/development server
        1: staging/readonly server (Any server where development is not allowed)
        99: production server (Any final deployment server)
"""
# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': get_env('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': get_env('DB_NAME', 'uat_data'),
        'USER': get_env('DB_USER', 'app_user'),
        'PASSWORD': get_env('DB_PASSWORD', ''),
        'HOST': get_env('DB_HOST', '127.0.0.1'),
        'PORT': get_env('DB_PORT', '5432'),
    }
}

SITE_ID = 1

EMAIL_HOST = get_env('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_HOST_USER = get_env('EMAIL_HOST_USER', 'snipklip777@gmail.com')
EMAIL_HOST_PASSWORD = get_env('EMAIL_HOST_PASSWORD', '')
EMAIL_PORT = get_env('EMAIL_PORT', 587, int)
EMAIL_USE_TLS = get_env('EMAIL_USE_TLS', True, bool)
EMAIL_USE_OAUTH2 = get_env('EMAIL_USE_OAUTH2', True, bool)

GOOGLE_CAPTCHA_SECRET = get_env('GOOGLE_CAPTCHA_SECRET', '')
GOOGLE_CAPTCHA_KEY = get_env('GOOGLE_CAPTCHA_KEY', '')

MESSAGE_TAGS = {
    messages.ERROR:'danger'
}

SIMPLE_JWT = {
      "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
      "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
      "ROTATE_REFRESH_TOKENS": False,
      "BLACKLIST_AFTER_ROTATION": False,
      "UPDATE_LAST_LOGIN": False,

      "ALGORITHM": "HS256",
      "SIGNING_KEY": SECRET_KEY,
      "VERIFYING_KEY": "",
      "AUDIENCE": None,
      "ISSUER": None,
      "JSON_ENCODER": None,
      "JWK_URL": None,
      "LEEWAY": 0,

      "AUTH_HEADER_TYPES": ("Bearer",),
      "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
      "USER_ID_FIELD": "id",
      "USER_ID_CLAIM": "user_id",
      "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",

      "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
      "TOKEN_TYPE_CLAIM": "token_type",
      "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

      "JTI_CLAIM": "jti", 

      "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
      "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
      "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),

      "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
      "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
      "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
      "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
      "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
      "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}
