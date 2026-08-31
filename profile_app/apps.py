from django.apps import AppConfig


class ProfileAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'profile_app'
    verbose_name = 'Profile'

    def ready(self):
        import profile_app.models  # ensures the post_save signal gets registered