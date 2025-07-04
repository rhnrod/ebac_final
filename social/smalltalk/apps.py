from django.apps import AppConfig


class SmalltalkConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'smalltalk'

    def ready(self):
        import smalltalk.signals
