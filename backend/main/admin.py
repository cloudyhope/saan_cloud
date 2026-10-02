from django.contrib import admin
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered
import inspect
import sys

# Get the current module (this file)
current_module = sys.modules[__name__]

# Get the app label by inspecting the module path
# This assumes your admin.py is in the app's directory
module_path = current_module.__package__
app_label = module_path.split('.')[-1]  # Get last component of the path


models = apps.get_models()

app_models = apps.get_app_config(app_label).get_models()
for model in app_models:
    try:
        admin.site.register(model)
    except: AlreadyRegistered