from sms_ir import SmsIr
from main.models import Config
from ..models import MessageTemplate

# params = {
#     'sender':'["1000011001200","1000011001200"]',
#     'receptor': '["09128334391","09378764114"]',
#     'message': '["تست ۱","تست ۲"]',
# }
class SMSdotIR:
    def __new__(cls, message_objects=[],  type="REGULAR", tokens=[], from_number=None, is_call=False):
        instance = super().__new__(cls)
        
        instance.message_objects = message_objects
        
        _API_KEY, _ = Config.objects.get_or_create(key='SMS_SMS_DOT_IR_API_KEY')
        instance.API_KEY = _API_KEY.value
        
        if from_number is None:
            _from_number, _ = Config.objects.get_or_create(key='SMS_SMS_DOT_IR_FROM_NUMBER')
            instance.from_number = _from_number.value
        else:
            instance.from_number = from_number

        _otp_template_id, _ = Config.objects.get_or_create(key='SMS_SMS_DOT_IR_OTP_TEMPLATE')
        instance.otp_template_id = _otp_template_id.value
        
        instance.tokens = tokens
        
        instance.client = SmsIr(_API_KEY.value, _from_number.value,)
        
        # Return the result of the appropriate method instead of the instance
        if type == "REGULAR":
            return instance.bulk_send()
        elif type == "OTP":
            return instance.otp()
        else:
            return instance  # Return instance for any other type
    
    def __init__(self, *args, **kwargs):
        pass

    def __del__(self):
        self.message_objects = None
    
    def send(self):
        self.bulk_send()
        return True

    def bulk_send(self):
        #TODO save in garbage storage.
        self.client.send_like_to_like(
            [message_object.to for message_object in self.message_objects],
            [f"{message_object.message_text}\nلغو۱۱" for message_object in self.message_objects],
            self.from_number,
            None,
        )
        return True

    def otp(self):
        self.client.send_verify_code(
            self.message_objects[0].to,
            self.otp_template_id,
            self.tokens,
        )
        return self.client.verify_lookup(body)