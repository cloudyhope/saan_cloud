from django.apps import AppConfig


class VisitConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'visit'

    def ready(self):
        from visit.priority import connect_signals
        connect_signals()
