import os
from datetime import timedelta
from pathlib import Path

from django.http import HttpRequest, HttpResponse

from .env import get_env
from app import snipklip_config as brand

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(__file__).resolve().parents[2]

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'backend',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'webpush',
    'drf_spectacular',
    'rest_framework_simplejwt',
    'social_django'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'app.middlewares.AccessControlMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            str(BASE_DIR / 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.contrib.messages.context_processors.messages',
                'backend.context_processors.verified_condition'
            ],
            'libraries': {
                'custom': 'backend.custom',
            }
        },
    },
]

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'offline',
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}

AUTHENTICATION_BACKENDS = (
    'api.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'social_core.backends.google.GoogleOAuth2'
)

WSGI_APPLICATION = 'app.wsgi.application'

AUTH_USER_MODEL = 'backend.User'

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'api.throttles.BurstRateThrottle',
        'api.throttles.SustainedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'burst': get_env('THROTTLE_BURST', '60/min'),
        'sustained': get_env('THROTTLE_SUSTAINED', '1000/day'),
        'assistant': get_env('THROTTLE_ASSISTANT', '20/hour'),
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': brand.API_TITLE,
    'DESCRIPTION': brand.API_DESCRIPTION,
    'VERSION': brand.API_VERSION,
}

WEBPUSH_SETTINGS = {
   "VAPID_PUBLIC_KEY": get_env('VAPID_PUBLIC_KEY', ''),
   "VAPID_PRIVATE_KEY": get_env('VAPID_PRIVATE_KEY', ''),
   "VAPID_ADMIN_EMAIL": get_env('VAPID_ADMIN_EMAIL', 'admin@example.com')
}

PRIVATE_KEY_WEB_PUSH = get_env('PRIVATE_KEY_WEB_PUSH', '')
API_KEY_WEB_PUSH = get_env('API_KEY_WEB_PUSH', '')

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_L10N = True
USE_TZ = True

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    str(BASE_DIR / "static"),
]

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
CORS_ALLOW_ALL_ORIGINS = get_env('CORS_ALLOW_ALL_ORIGINS', True, bool)
EMAIL_BACKEND = get_env('EMAIL_BACKEND', 'app.mail_backend.GmailOAuthEmailBackend')
EMAIL_HOST = get_env('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_HOST_USER = get_env('EMAIL_HOST_USER', 'snipklip777@gmail.com')
EMAIL_HOST_PASSWORD = get_env('EMAIL_HOST_PASSWORD', '')
SENDGRID_API_KEY = get_env('SENDGRID_API_KEY', get_env('EMAIL_HOST_PASSWORD', ''))
EMAIL_PORT = get_env('EMAIL_PORT', 587, int)
EMAIL_USE_TLS = get_env('EMAIL_USE_TLS', True, bool)
EMAIL_USE_OAUTH2 = get_env('EMAIL_USE_OAUTH2', True, bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = get_env('SECURE_SSL_REDIRECT', False, bool)
SESSION_COOKIE_SECURE = get_env('SESSION_COOKIE_SECURE', False, bool)
CSRF_COOKIE_SECURE = get_env('CSRF_COOKIE_SECURE', False, bool)
SECURE_HSTS_SECONDS = get_env('SECURE_HSTS_SECONDS', 0, int)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in get_env('CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip()]

RAZORPAY_KEY_ID = get_env('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = get_env('RAZORPAY_KEY_SECRET', '')

HUBSPOT_KEY = get_env('HUBSPOT_KEY', '')
CRON_JOB_TOKEN = get_env('CRON_JOB_TOKEN', '')
WHATSAPP_PHONE_NUMBER_ID = get_env('WHATSAPP_PHONE_NUMBER_ID', '')
FACEBOOK_ACCESS_TOKEN = get_env('FACEBOOK_ACCESS_TOKEN', '')
FAST2SMS_API_KEY = get_env('FAST2SMS_API_KEY', '')
LLM_API_BASE_URL = get_env('LLM_API_BASE_URL', 'https://api.openai.com/v1')
LLM_API_KEY = get_env('LLM_API_KEY', '')
LLM_MODEL = get_env('LLM_MODEL', '')
ASSISTANT_OFFLINE_MODE = get_env('ASSISTANT_OFFLINE_MODE', True, bool)
LLM_TIMEOUT_SECONDS = get_env('LLM_TIMEOUT_SECONDS', 15, int)
LLM_MAX_OUTPUT_TOKENS = get_env('LLM_MAX_OUTPUT_TOKENS', 350, int)
ASSISTANT_MAX_QUESTION_LENGTH = get_env('ASSISTANT_MAX_QUESTION_LENGTH', 600, int)
FERNET_KEY = get_env('FERNET_KEY', '')
FERNET_KEY_FILE = get_env('FERNET_KEY_FILE', 'secret.key')
DEFAULT_EMAIL = brand.DEFAULT_EMAIL
DEFAULT_MOBILE_NUMBER = get_env('DEFAULT_MOBILE_NUMBER', brand.CONTACT_NUMBER)
DEFAULT_FROM_EMAIL = brand.DEFAULT_FROM_EMAIL
DEFAULT_FROM_NAME = brand.DEFAULT_FROM_NAME
COMPANY_NAME = brand.COMPANY_NAME
COMPANY_WEBSITE = brand.COMPANY_WEBSITE
SUPPORT_EMAIL = brand.SUPPORT_EMAIL
ADMIN_EMAIL = brand.ADMIN_EMAIL
CONTACT_NUMBER = brand.CONTACT_NUMBER
CONTACT_RECIPIENTS = brand.CONTACT_RECIPIENTS
SOCIAL_LINKS = brand.SOCIAL_LINKS
LOGO = brand.LOGO
BROCHURE_LINK = brand.BROCHURE_LINK
FRONTEND_LINK = get_env('FRONTEND_LINK', 'http://localhost:8083')

LOGGING = {
    'version': 1,  # Required
    'disable_existing_loggers': False,  # Set to False to preserve existing loggers
    'handlers': {
        'console': {  # Define a console handler that logs to the console
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple'
        },
        'file': {  # Define a file handler that logs to a file
            'class': 'logging.FileHandler',
            'filename': 'django.log',
            'level': 'DEBUG',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {  # Set the logging level and handlers for the django logger
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,  # Set to True to propagate to the root logger
        },
        'backend': {  # Set the logging level and handlers for the myapp logger
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,  # Set to False to prevent propagation to the root logger
        },
    },
    'formatters': {
        'simple': {  # Define a simple formatter for console output
            'format': '%(levelname)s %(message)s'
        },
        'verbose': {  # Define a verbose formatter for file output
            'format': '%(asctime)s %(levelname)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
}


SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = get_env('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = get_env('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')



def get_base_url(request):
    scheme = request.scheme
    host = request.get_host()
    return f'{scheme}://{host}'

def GET_BASE_URL(request):
    base_url = get_base_url(request)
    return base_url

