from django.apps import AppConfig, apps
from django.db import transaction

class NotificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notification'

    REQUIRED_APPS = [
        'main',
    ]

    def ready(self):
        # Import models here to avoid AppRegistryNotReady error
        
        from main.models import Config
        
        # Initialize configurations
        # Connect to post_migrate signal for database initialization
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver
        @receiver(post_migrate, sender=self)
        def initialization(sender, **kwargs):
            self.initialize_configurations()
    
    def check_all_dependencies(self):
        """Check all dependencies and configuration"""
        self.check_installed_apps()
        self.check_app_order()

    def check_installed_apps(self):
        """Check if all required apps are installed"""
        missing_apps = []
        
        for app_name in self.REQUIRED_APPS:
            if not apps.is_installed(app_name):
                missing_apps.append(app_name)
        
        if missing_apps:
            raise ImproperlyConfigured(
                f"Missing required apps for '{self.name}': \n"
                f"Please add these to INSTALLED_APPS: \n"
                f"- {chr(10).join(missing_apps)}"
            )
    
    def check_app_order(self):
        """Ensure this app comes after its dependencies"""
        installed_apps = list(settings.PROJECT_APPS)
        
        try:
            my_app_index = installed_apps.index(self.name)
            
            for dep_app in self.REQUIRED_APPS:
                if dep_app in installed_apps:
                    dep_index = installed_apps.index(dep_app)
                    if dep_index > my_app_index:
                        logger.warning(
                            f"App '{dep_app}' should come before '{self.name}' "
                            f"in INSTALLED_APPS for optimal functionality."
                        )
        except ValueError:
            # This app not in INSTALLED_APPS (shouldn't happen)
            pass

    def initialize_configurations(self):
        from main.models import Config
        
        # Use transaction to ensure data consistency
        with transaction.atomic():
            # Create default configurations
            default_configs = [
                {'key': 'SMS_FARAPAYAMAK_USERNAME'},
                {'key': 'SMS_FARAPAYAMAK_PASSWORD'},
                {'key': 'SMS_FARAPAYAMAK_OTP_TEMPLATE'},
                {'key': 'SMS_FARAPAYAMAK_FROM_NUMBER'},
                {'key': 'SMS_KAVENEGAR_API_KEY'},
                {'key': 'SMS_KAVENEGAR_OTP_TEMPLATE'},
                {'key': 'SMS_KAVENEGAR_FROM_NUMBER'},
                {'key': 'SMS_SMS_DOT_IR_API_KEY'},
                {'key': 'SMS_SMS_DOT_IR_FROM_NUMBER'},
                {'key': 'SMS_SMS_DOT_IR_OTP_TEMPLATE'},
                {'key': 'SMS_DEFAULT_GATEWAY'},
                {'key': 'SMS_WHITELIST_NUMBERS'},
            ]
            
            for config in default_configs:
                Config.objects.get_or_create(
                    key=config['key'],
                )
            
            print(f"Initialized {len(default_configs)} default configs for app {self.name}")
