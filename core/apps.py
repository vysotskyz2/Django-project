from django.apps import AppConfig
from django.conf import settings

from core.logging import configure_logging


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self) -> None:
        configure_logging(base_dir=settings.BASE_DIR, debug=settings.DEBUG)
