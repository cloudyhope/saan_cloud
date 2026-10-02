import requests
import json
from main.models import Config
from ..models import MessageTemplate
from django.conf import settings
from string import Template
from django.conf import settings

from django.contrib.auth import get_user_model
User = get_user_model()

class SMS:
    #TODO ADD BLACKLIST SUPPORT.
    #TODO ADD FALLBACK SUPPORT.
    def __init__(self, message_objects=None):
        print("SMS instance is called!")
        self.message_objects = message_objects

    def __del__(self):
        self.to = None
        self.text = ''

    def get_gateway(self):
        default_gateway_config, _ = Config.objects.get_or_create(key="SMS_DEFAULT_GATEWAY")
        from .tools import get_the_class
        # Possible Values:
        # notification.modules.farapayamak.FaraPayamak
        # notification.modules.kavenegar.KaveNegar
        return get_the_class(default_gateway_config.value)

    def whitelist_check(self):
        if settings.PRODUCTION:
            return True
        whitelist_config, _ = Config.objects.get_or_create(key="SMS_WHITELIST_NUMBERS")
        white_list_numbers = [] if whitelist_config.value is None else whitelist_config.value.split(',')
        for message_object in self.message_objects:
            if not message_object.to in white_list_numbers:
                print("whitelist removed")
                self.message_objects.remove(message_object)
        return True

    def message_is_valid(self):
        for message_object in self.message_objects:
            if message_object.message_text is None or message_object.message_text == '':
                print("valid removed")
                self.message_objects.remove(message_object)
        return True

    def send(self):
        self.whitelist_check()
        if self.message_is_valid():
            #TODO ADD BROKER SUPPORT.
            gateway = self.get_gateway()
            result = gateway(self.message_objects)
            return result
        return False

