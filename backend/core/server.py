from rest_framework.response import Response
from auth_app.views import UserManagementView
post_method = lambda *args, **kwargs: Response(data= args, status=200)
def get_view_instance(view_name, *args, **kwargs): 
    view = globals()[view_name]
    view.post = post_method
    return view