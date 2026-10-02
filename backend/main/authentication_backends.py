from django.contrib.auth import get_user_model

from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.tokens import RefreshToken


#################################
### Generating JWT Tokens:
#################################


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    update_last_login(None, user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


