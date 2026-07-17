from django.apps import AppConfig
from django.contrib import admin


class BackendConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend"

    def ready(self):
        from django.conf import settings

        admin.site.site_header = f"{settings.COMPANY_NAME} Administration"
        admin.site.site_title = settings.COMPANY_NAME
        admin.site.index_title = f"Welcome to {settings.COMPANY_NAME}"

        from defaults.populate_json_data import load_JSON_data

        load_JSON_data()
