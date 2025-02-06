from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        # This import ensures that your central admin.py is loaded after apps are ready.
        import api.admin
