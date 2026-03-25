from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "monitoring"
    verbose_name = "Monitoring"

    def ready(self):
        from prometheus_client import REGISTRY

        from monitoring.metrics import FreeJobGNCollector

        REGISTRY.register(FreeJobGNCollector())
