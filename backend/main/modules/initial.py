import inspect
from importlib import import_module
from django.conf import settings
from main.models import ViewMethod

# This module will makes you to define classbased views only.
# this will check for all view classes in app_name.views and
# add them to DB to check for view_methods dynamically.
# wrote by mmzadfalah@gmail.com


def print_repeated_dicts(dict_list):
    """
    Finds and prints all dictionaries that appear more than once in the input list.
    
    Args:
        dict_list (list): A list of dictionaries to check for duplicates
    """
    # Convert each dict to a frozenset of items for hashability
    seen = {}
    
    for i, d in enumerate(dict_list):
        # Convert the dict to a hashable representation
        dict_hash = frozenset(d.items())
        
        if dict_hash in seen:
            seen[dict_hash].append(i)
        else:
            seen[dict_hash] = [i]
    
    # Print repeated dictionaries
    repeated_found = False
    
    for dict_hash, indices in seen.items():
        if len(indices) > 1:
            repeated_found = True
            original_dict = dict(dict_hash)
            print(f"Dictionary {original_dict} appears at indices: {indices}")
    
    if not repeated_found:
        print("No repeated dictionaries found.")


def init_view_methods():
    print("APPS: ", settings.PROJECT_APPS)
    # list values in the db:

    # db_classes = list(view_methods.values_list('view_name', flat=True).distinct())
    
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
        print_repeated_dicts(code_classes) 
        raise ValueError(
            "The view_names in whole [PROJECT_APPS].views is not unique! Try changing the name of one of these classes.")
    # print(code_classes)
    # get all view_methods:
    view_methods = ViewMethod.objects.all()
    # check for the deleted or renamed views, we can't handle rename here, so the rename is adding one new record and deletes the old one.
    for db_view_name in view_methods:
        # print("db_view_name", db_view_name)
        db_view_dict = {
            "view_name": db_view_name.view_name,
            "method": db_view_name.method
        }
        if db_view_dict not in code_classes:
            # db_classes is just calculated from the database, so it should exists!
            db_obj = ViewMethod.objects.get(**db_view_dict)
            db_obj.delete()

    # create views that doesn't exists:
    for code_class in code_classes:
        # print("code_class", code_class)
        if not ViewMethod.objects.filter(**code_class).exists():
            p = ViewMethod()
            p.view_name = code_class['view_name']
            p.method = code_class['method']
            p.save()

    return True
