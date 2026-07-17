"""
Central SnipKlip branding and contact configuration.

All values are loaded from environment variables (via django-environ-style
get_env). Import from Django settings in application code — do not hardcode
brand strings elsewhere.
"""
from app.settings.env import get_env


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(',') if item.strip()]


COMPANY_NAME = get_env('COMPANY_NAME', 'SnipKlip')
COMPANY_WEBSITE = get_env('COMPANY_WEBSITE', 'https://snipklip.in')
SUPPORT_EMAIL = get_env('SUPPORT_EMAIL', 'support@snipklip.in')
ADMIN_EMAIL = get_env('ADMIN_EMAIL', 'admin@snipklip.in')
CONTACT_NUMBER = get_env('CONTACT_NUMBER', get_env('DEFAULT_MOBILE_NUMBER', ''))
CONTACT_RECIPIENTS = _split_csv(get_env('CONTACT_RECIPIENTS', 'spwankhede007@gmail.com,admin@snipklip.in,support@snipklip.in'))

# TODO: Replace with SnipKlip-branded logo asset once supplied (static/branding/logo.png)
LOGO = get_env('LOGO', '/static/branding/logo.png')

# TODO: Replace with SnipKlip brochure PDF once supplied (static/branding/brochure.pdf)
BROCHURE_LINK = get_env('BROCHURE_LINK', f'{COMPANY_WEBSITE.rstrip("/")}/SnipKlip-Brochure.pdf')

SOCIAL_LINKS = {
    'instagram': get_env('SOCIAL_INSTAGRAM', ''),
    'facebook': get_env('SOCIAL_FACEBOOK', ''),
    'twitter': get_env('SOCIAL_TWITTER', ''),
    'linkedin': get_env('SOCIAL_LINKEDIN', ''),
    'youtube': get_env('SOCIAL_YOUTUBE', ''),
}

DEFAULT_FROM_NAME = get_env('DEFAULT_FROM_NAME', COMPANY_NAME)
DEFAULT_FROM_EMAIL = get_env('DEFAULT_FROM_EMAIL', 'snipklip777@gmail.com')
DEFAULT_EMAIL = get_env('DEFAULT_EMAIL', DEFAULT_FROM_EMAIL)

API_TITLE = get_env('API_TITLE', f'{COMPANY_NAME} REST API')
API_DESCRIPTION = get_env('API_DESCRIPTION', f'{COMPANY_NAME} salon management platform API')
API_VERSION = get_env('API_VERSION', '3.0.0')
