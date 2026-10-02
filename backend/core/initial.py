import inspect

from auth_app.models import ViewMethod, ModelField
from importlib import import_module
from django.conf import settings
from django.apps import apps
from core.urls import urlpatterns
from django.conf import settings


def init_permissions():
    code_classes = []

    for app_name in settings.PROJECT_APPS:
        import_path = "%s.%s" % (app_name, 'views')
        this_module = import_module(import_path)
        for name, obj in inspect.getmembers(this_module):
            if inspect.isclass(obj) and obj.__module__ == import_path and getattr(obj, 'is_view', False):
                code_classes.append(name)

    if not (len(code_classes) == len(set(code_classes))):
        seen = set()
        # A list to store duplicates found in the input list
        duplicates = []
        for i in code_classes:
            if i in seen:
                duplicates.append(i)
            else:
                seen.add(i)
        print("Code classes not unique: ", duplicates)
        raise ValueError(
            "The view_names in whole [PROJECT_APPS].views is not unique! Try changing the name of one of these classes.")

    # These scoped APIViews live outside the legacy app views modules.
    from visit.client_support import (
        ClientSupportTicketsAPIView, ClientSupportTicketDetailAPIView,
        ExpertSupportTicketsAPIView, ExpertSupportTicketDetailAPIView,
    )
    code_classes.extend(view.__name__ for view in (
        ClientSupportTicketsAPIView, ClientSupportTicketDetailAPIView,
        ExpertSupportTicketsAPIView, ExpertSupportTicketDetailAPIView,
    ))

    views = ViewMethod.objects.all()
    db_classes = list(views.values_list('view_name', flat=True).distinct())

    for db_view_name in db_classes:
        if db_view_name not in code_classes:
            obj = ViewMethod.objects.filter(view_name=db_view_name).all().delete()

    db_classes = list(views.values_list('view_name', flat=True).distinct())
    methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]

    for code_view_name in code_classes:
        try:
            for method in methods:
                if code_view_name not in db_classes:
                    db_obj = ViewMethod()
                    db_obj.view_name = code_view_name
                    db_obj.method = method
                    db_obj.save()
                if code_view_name in db_classes:
                    m = ViewMethod.objects.filter(view_name=code_view_name).all()
                    m = list(m.values_list('method', flat=True).distinct())
                    for method in methods:
                        if method not in m:
                            db_obj = ViewMethod()
                            db_obj.view_name = code_view_name
                            db_obj.method = method
                            db_obj.save()
        except Exception as e:
            print(f"Error saving ViewMethod for {code_view_name}: {e}")

    return True


def init_model():
    app_name_list = settings.PROJECT_APPS
    full_app_list = []
    full_model_list = []

    try:
        for app_name in app_name_list:
            full_app_list.append(apps.get_app_config(app_name))

        for app_name in full_app_list:
            full_model_list = list(apps.get_models(app_name))

        if not (len(full_model_list) == len(set(full_model_list))):
            print("Models name not unique")
            raise ValueError(
                "The models name in whole project is not unique! Try changing the name of one of these classes.")
    except:
        print("Error initializing model get data")

    db_classes = ModelField.objects.all()
    objs = []

    for model in full_model_list:
        for field in model._meta.get_fields():
            db_obj = db_classes.filter(model_name=model.__name__, field_name=field.name,
                                       field_type=type(field).__name__)
            try:
                is_exists = db_obj.exists()
                try:
                    for i in range(len(db_obj) - 1):
                        db_obj[i].delete()

                    db_obj = db_obj[0]
                except:
                    print('done')
            except :
                is_exists = False

            if not is_exists:
                db_obj = ModelField()
                db_obj.model_name = model.__name__
                db_obj.field_name = field.name
                db_obj.field_type = type(field).__name__
                db_obj.save()
                print(f"Model field {model.__name__}.{field.name} created")
            objs.append(db_obj.model_name)

    db_classes = list(db_classes.values_list('model_name', flat=True).distinct())

    for model in db_classes:
        if model not in objs:
            print(f"{model} must be deleted")
            model.delete()
    return True
