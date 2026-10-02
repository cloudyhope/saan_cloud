from rest_framework.exceptions import APIException
from django.utils.translation import gettext_lazy as _

class CustomResponse(APIException):
    status_code = 201
    default_detail = _("Custom Response!")
    default_code = "Custom_Response"


class NotAcceptable(APIException):
    status_code = 406
    default_detail = _("Not Acceptable")
    default_code = "Not_Acceptable"


class NotFound(APIException):
    status_code = 404
    default_detail = _("Not Found")
    default_code = "Not_Found"


class InsufficientBalance(APIException):
    status_code = 402
    default_detail = _("Insufficient Balance")
    default_code = "Insufficient_Balance"


class AlreadyExists(APIException):
    status_code = 409
    default_detail = _("Already Exists")
    default_code = "Already_Exists"


class BadRequest(APIException):
    status_code = 400
    default_detail = _("Bad Request")
    default_code = "Bad_Request"

class TooLate(APIException):
    status_code = 419
    default_detail = _("Too Late")
    default_code = "Too_Late"

class ThirdPartyError(APIException):
    status_code = 428
    default_detail = _("Third Party Error")
    default_code = "Third_Party_Error"

class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = _("Sorry, Internal Temporary Problem, Try Again Later!")
    default_code = "Internal_Temporary_problem"

class UserNeedSubscription(APIException):
    status_code = 402
    default_detail = _("You are not subscribed to this account!")
    default_code = "User_Need_Subscription"
