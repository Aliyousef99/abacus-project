from django.apps import AppConfig


class IndexConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'index'

    def ready(self):
        # Import signals to auto-create IndexProfile for new Lineage agents
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass

