import requests
import json
from main.models import Config
from notification.models import *
from django.conf import settings
from string import Template
from ..models import MessageTemplate
from kavenegar import KavenegarAPI
from django.utils.translation import gettext_lazy as _


# params = {
#     'sender':'["1000011001200","1000011001200"]',
#     'receptor': '["09128334391","09378764114"]',
#     'message': '["تست ۱","تست ۲"]',
# }
class KaveNegar:
    def __new__(cls,  message_objects=[], type="REGULAR", tokens=[], from_number=None, is_call=False):
        print("kavenegar instance created.")
        instance = super().__new__(cls)

        if len(message_objects) == 0:
            raise ValueError(_("No message object recieved!"))
        instance.message_objects = message_objects

        _API_KEY, _tmp = Config.objects.get_or_create(key='SMS_KAVENEGAR_API_KEY')
        instance.API_KEY = _API_KEY.value

        _otp_template_id, _tmp = Config.objects.get_or_create(key='SMS_KAVENEGAR_OTP_TEMPLATE')
        instance.otp_template_id = _otp_template_id.value

        if from_number is None:
            _from_number, _tmp = Config.objects.get_or_create(key='SMS_KAVENEGAR_FROM_NUMBER')
            instance.from_number = _from_number.value
        else:
            instance.from_number = from_number
        
        instance.is_call = is_call

        instance.tokens = tokens
        
        instance.client = KavenegarAPI(instance.API_KEY)
        
        # Return the result of the appropriate method instead of the instance
        if type == "REGULAR":
            if len(message_objects) > 1:
                print("kvaenegar bulk send going to call")
                return instance.bulk_send()
            print("kvaenegar send going to call")
            return instance.send()
        elif type == "OTP":
            return instance.otp()
        else:
            return instance  # Return instance for any other type
    
    def __init__(self, *args, **kwargs):
        pass

    def __del__(self):
        self.to = []
        self.text = ""
    
    def send(self):
        #TODO save in garbage storage.
        print("in send kavenegar")
        result = self.client.sms_send({ 
            'sender': self.from_number,
            'receptor': self.message_objects[0].to,
            'message': self.message_objects[0].message_text,
        })
        print("result: ", result)
        return True

    def bulk_send(self):
        #TODO save in garbage storage.
        self.client.sms_sendarray({ 
            'sender': [self.from_number for _ in self.message_objects],
            'receptor': [message_object.to for message_object in self.message_objects],
            'message': [message_object.message_text for message_object in self.message_objects],
        })
        return True

    def otp(self):
        body = {
            'receptor': self.to[0],
            'template': self.otp_template_id,
            'token': self.tokens[0],
            'type': 'call' if self.is_call else 'sms', # sms vs call  
        }

        for token_counter in range(len(self.tokens) - 1):
            key = 'token' + str(token_counter)
            body[key] = self.tokens[token_counter]
        return self.client.verify_lookup(body)