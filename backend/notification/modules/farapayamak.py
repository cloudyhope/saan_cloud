import requests
import json
from main.models import Config
from .models import Message
from django.conf import settings
from string import Template

#TODO Can't handle many to many yet! just send first one only.

class FaraPayamak:
    send_url = "https://rest.payamak-panel.com/api/SendSMS/SendSMS"
    delivery_check_url = "https://rest.payamak-panel.com/api/SendSMS/GetDeliveries2"
    inbox_url = "https://rest.payamak-panel.com/api/SendSMS/GetMessages"

    def __new__(cls,  message_objects=[], type="REGULAR", tokens=[], from_number=None, is_call=False):
        instance = super().__new__(cls)

        _USERNAME, _ = Config.objects.get_or_create(key='SMS_FARAPAYAMAK_USERNAME')
        instance.USERNAME = _USERNAME.value
        _PASSWORD, _ = Config.objects.get_or_create(key='SMS_FARAPAYAMAK_PASSWORD')
        instance.USERNAME = _USERNAME.value

        if type(message_objects) == list:
            message_object = message_objects[0]
        instance.message_objects = message_objects
        instance.message_object = message_object
        

        _otp_template_id, _ = Config.objects.get_or_create(key='SMS_FARAPAYAMAK_OTP_TEMPLATE')
        instance.otp_template_id = _otp_template_id.value

        if from_number is None:
            _from_number, _ = Config.objects.get_or_create(key='SMS_FARAPAYAMAK_FROM_NUMBER')
            instance.from_number = _from_number.value
        else:
            instance.from_number = from_number
        
        instance.is_call = is_call

        instance.tokens = tokens
        
        instance.client = KavenegarAPI(instance.API_KEY)
        
        # Return the result of the appropriate method instead of the instance
        if type == "REGULAR":
            return instance.send()
        elif type == "OTP":
            return instance.otp()
        else:
            return instance  # Return instance for any other type

    def __init__(self, message_objects=None):
        pass

    def __del__(self):
        self.message_objects = None
        self.message_object = None

    # def assemble_numbers(self):
    #     if len(self.to) == 0:
    #         return None
    #     return_val = ""
    #     for number in self.to:
    #         if number.isnumeric():
    #             return_val += number
    #             return_val += ','
    #     return return_val[:-1]

    def send(self, payload=None):
        headers = {
            "content-type": "application/x-www-form-urlencoded; charset=utf-8"
        }
        if payload is None:
            payload = self.payload_assembler(self.USERNAME, self.PASSWORD, self.from_number, self.message_object.to, self.message_object.message_text)
        payload = payload.encode("utf-8")
        response = requests.request("POST", url=self.send_url, headers=headers, data=payload)
        response_dict = json.loads(response.text)
        #TODO ADD THIS TO GARBAGE STORAGE.
        if response.status_code in [200, 201, 202, 203, 204, 205, 206]:
            response_dict["our_status"] = True
        else:
            response_dict["our_status"] = False
        return response_dict["our_status"]
    
    def otp(self):
        self.send()
        return True

    def payload_assembler(self, to=None, message_text=None, username=None, password=None, from_number=None):
        _username= username if username is not None else self.username
        _password= password if password is not None else self.password
        _from_number= from_number if from_number is not None else self.from_number
        _to= to if to is not None else self.message_object.to
        _message_text= message_text if message_text is not None else self.message_object.message_text
        return 'username=' + _username + '&password=' + _password + '&from=' + _from_number + '&to=' + _to + '&text=' + str(
            _message_text) + '\nلغو11' + '&isFlash=false'

    def send_regular_sms(self, to, message_text):
        return self.send(payload=self.payload_assembler(to=to, message_text=message_text))

    def check_inbox(self):
        header = {
            "content-type": "application/x-www-form-urlencoded"
        }
        payload = 'username=' + self.username + '&password=' + self.password + '&location=' + "1" + '&from=' + self.from_number + '&index=' + '0' + '&count=' + '100'
        response = requests.request("POST", url=self.inbox_url, headers=header, data=payload)
        response_dict = json.loads(response.text)
        return response_dict
