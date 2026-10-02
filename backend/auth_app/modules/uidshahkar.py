import json

import requests


class UIDShahkar:

    def __init__(self, national_id, birth_date=None, phone_number=None):
        self.birth_date = birth_date
        self.phone_number = phone_number
        self.national_id = national_id
        self.api_infos = {
            'phone_national_id': {"businessId": 'ffc2f799-5b41-4383-be4a-63eb0114808b', "businessToken": '5390bbad-6628-45ef-9aab-eaeb94e403d2', },
            'sheba_national_id': {"businessId": 'ffc2f799-5b41-4383-be4a-63eb0114808b', "businessToken": '5390bbad-6628-45ef-9aab-eaeb94e403d2', },
            }
        self.body = {
            "requestContext": {
                "apiInfo": {},
            },
        }

        self.urls = {'phone_national': 'https://json-api.uid.ir/api/inquiry/mobile/owner/v2',
                     'sheba_national': 'https://json-api.uid.ir/api/validate/iban/ownership',
                     }
        self.header = {
            "content-type": "application/x-www-form-urlencoded; charset=utf-8"
        }

    def phone_with_national_id(self, phone_number):
        self.body['mobileNumber'] = phone_number
        self.body['nationalId'] = self.national_id
        self.body['requestContext']['apiInfo'].update(self.api_infos['phone_national_id'])

        response = requests.request("POST", url=self.urls['phone_national'], headers=self.header, data=json.dumps(self.body))
        response_dict = response.json()
        if response.status_code == 200 or response.status_code == 201:
            if response_dict["isMatched"]:
                return True, response_dict["responseContext"]
            else:
                return False, response_dict['responseContext']
        else:
            return False, 'U-id error'

    def sheba_with_national_id(self, sheba_number, birth_date):
        self.body['iban'] = sheba_number
        self.body['nationalId'] = self.national_id
        self.body['birthDate'] = birth_date
        self.body['requestContext']['apiInfo'].update(self.api_infos['sheba_national_id'])

        response = requests.request("POST", url=self.urls['sheba_national'], headers=self.header, data=json.dumps(self.body))
        response_dict = response.json()
        if response.status_code == 200 or response.status_code == 201:
            if response_dict["isMatched"]:
                return True, response_dict["responseContext"]
            else:
                return False, response_dict['responseContext']
        else:
            return False, 'U-id error'



