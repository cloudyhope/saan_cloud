import os
import requests
import json
from config.models import Config
from utils.models import Message
from core.settings import production
from string import Template


class FaraPayamak:
    white_list_numbers = [number.strip() for number in os.environ.get("FARAPAYAMAK_LOCAL_WHITELIST", "").split(",") if number.strip()]
    send_url = "https://rest.payamak-panel.com/api/SendSMS/SendSMS"
    delivery_check_url = "https://rest.payamak-panel.com/api/SendSMS/GetDeliveries2"
    inbox_url = "https://rest.payamak-panel.com/api/SendSMS/GetMessages"
    from_number = os.environ.get("FARAPAYAMAK_FROM_NUMBER", "")
    linkable_from_number = os.environ.get("FARAPAYAMAK_LINKABLE_FROM_NUMBER", "")
    username = os.environ.get("FARAPAYAMAK_USERNAME", "")
    password = os.environ.get("FARAPAYAMAK_PASSWORD", "")

    def __init__(self, to=None, from_number=None):
        self.to = to
        self.text = ''
        self.from_number = from_number or type(self).from_number

    def __del__(self):
        self.to = None

    def whitelist_checks(self, to=None):
        if to is not None:
            self.to = to
        if type(self.to) == str:
            self.to = [self.to,]
        if production:
            return True
        config_whitelist = Config.objects.filter(key="SMS_WHITELIST")
        if config_whitelist.count() > 0:
            numbers_config = config_whitelist[0].value
            new_white_list_numbers = list(map(str, numbers_config.split(',')))
            self.white_list_numbers = new_white_list_numbers
        if type(self.to) is list:
            new_to = [i for i in self.to if i in self.white_list_numbers]
            self.to = new_to
        return True

    def assemble_numbers(self):
        if len(self.to) == 0:
            return None
        return_val = ""
        for number in self.to:
            if number.isnumeric():
                return_val += number
                return_val += ','
        return return_val[:-1]


    def send(self, to=None):
        headers = {
            "content-type": "application/x-www-form-urlencoded; charset=utf-8"
        }
        if to is None:
            to = self.to
        if self.text is None or self.text == "":
            return {"our_status": False}
        self.whitelist_checks(to=to)
        to = self.assemble_numbers()
        if to is None:
            return {"our_status": False}
        payload = 'username=' + self.username + '&password=' + self.password + '&from=' + self.from_number + '&to=' + to + '&text=' + str(
            self.text) + '\nلغو11' + '&isFlash=false'
        payload = payload.encode("utf-8")
        response = requests.request("POST", url=self.send_url, headers=headers, data=payload)
        response_dict = json.loads(response.text)
        if response.status_code in [200, 201, 202, 203, 204, 205, 206]:
            response_dict["our_status"] = True
        else:
            response_dict["our_status"] = False
        return response_dict

    def repeated_code(self):
        self.get_message(type='REPEATED')
        return self.send()

    def send_otp(self):
        self.get_message(type='OTP')
        return self.send()

    # def send_to_many(self, to_numbers, message=None):
    #     if message is not None:
    #         self.text = message
    #     numbers = ""
    #     for i in to_numbers:
    #         if numbers == "":
    #             numbers = numbers + i
    #         else:
    #             numbers = numbers + ',' + i
    #     return self.send(to=numbers)

    def send_regular_sms(self, to, text):
        self.to = to
        self.text = text
        return self.send()

    def check_inbox(self):
        header = {
            "content-type": "application/x-www-form-urlencoded"
        }
        payload = 'username=' + self.username + '&password=' + self.password + '&location=' + "1" + '&from=' + self.from_number + '&index=' + '0' + '&count=' + '100'
        response = requests.request("POST", url=self.inbox_url, headers=header, data=payload)
        response_dict = json.loads(response.text)
        return response_dict

    def send_invalid(self):
        self.get_message(type='INVALID_CODE')
        return self.send()

    def send_validation(self):
        self.get_message(type='SUCCESS_CODE')
        return self.send()

    def send_first_time(self, to):
        self.get_message(type='FIRST_TIME')
        return self.send()

    def get_message(self, message_type,  *args, **kwargs):

        category_type = f'SMS_{message_type.upper()}'
        configs = Config.objects.filter(category=category_type)

        subs = {}
        if configs.exists():
            for per_config in configs:
                if per_config.key and per_config.value:
                    subs.update({per_config.key: per_config.value})
                else:
                    self.text = None
                    return {"our_status": False}

        message_text = Message.objects.filter(type=message_type.upper(), is_deleted=False).first()
        if message_text is None:
            return {"our_status": False}
        if not message_text.msg_pattern:
            return {"our_status": False}
        template = Template(message_text.msg_pattern)
        mapping = {**subs, **kwargs}
        self.text = template.substitute(**mapping)
        
    def flatten_dict(self, d, parent_key='', sep='__'):
        if type(d) == str:
            import json
            d = json.loads(d)
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def type_send(self, message_type, to=None, *args, **kwargs):
        if to is not None:
            self.to = to
        self.get_message(message_type, *args, **kwargs)
        return self.send()
