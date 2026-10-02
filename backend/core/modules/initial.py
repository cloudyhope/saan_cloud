import inspect
from importlib import import_module
from django.conf import settings
from auth_app.models import Permission

# This module will makes you to define classbased views only.
# this will check for all view classes in app_name.views and
# add them to DB to check for permissions dynamically.
# wrote by mmzadfalah@gmail.com


def init_permissions():
    print("APPS: ", settings.PROJECT_APPS)
    # list values in the db:

    # db_classes = list(permissions.values_list('view_name', flat=True).distinct())
    
    # print("db", db_classes)
    # search for all view classes:
    code_classes = []
    for app_name in settings.PROJECT_APPS:
        import_path = "%s.%s" % (app_name, 'views')
        this_module = import_module(import_path)
        for name, obj in inspect.getmembers(this_module):
            if inspect.isclass(obj) and obj.__module__ == import_path and getattr(obj, 'is_view', False):
                instance = obj()
                for method in instance.methods:
                    code_classes.append(
                            {
                                "view_name": name,
                                "method": method
                            }
                        )
    # search for all view classes done.
    # check that view names are unique:
    unique_code_classes = set(tuple(sorted(d.items())) for d in code_classes)
    if not (len(code_classes) == len(unique_code_classes)):
        raise ValueError(
            "The view_names in whole [PROJECT_APPS].views is not unique! Try changing the name of one of these classes.")
    # print(code_classes)
    # get all permissions:
    permissions = Permission.objects.all()
    # check for the deleted or renamed views, we can't handle rename here, so the rename is adding one new record and deletes the old one.
    for db_view_name in permissions:
        # print("db_view_name", db_view_name)
        db_view_dict = {
            "view_name": db_view_name.view_name,
            "method": db_view_name.method
        }
        if db_view_dict not in code_classes:
            # db_classes is just calculated from the database, so it should exists!
            db_obj = Permission.objects.get(**db_view_dict)
            db_obj.delete()

    # create views that doesn't exists:
    for code_class in code_classes:
        # print("code_class", code_class)
        if not Permission.objects.filter(**code_class).exists():
            p = Permission()
            p.view_name = code_class['view_name']
            p.method = code_class['method']
            p.save()

    return True