import os
import requests
import json

class FaraPayamak():
    send_url = "https://rest.payamak-panel.com/api/SendSMS/SendSMS"
    delivery_check_url = "https://rest.payamak-panel.com/api/SendSMS/GetDeliveries2"
    from_number = os.environ.get("FARAPAYAMAK_FROM_NUMBER", "")
    username = os.environ.get("FARAPAYAMAK_USERNAME", "")
    password = os.environ.get("FARAPAYAMAK_PASSWORD", "")
    @staticmethod
    def send_otp(self, to, code):
        text = "\nکد تایید: "
        header = {
            "content-type": "application/x-www-form-urlencoded; charset=utf-8"
        }
        payload='username=' + self.username + '&password=' + self.password + '&from=' + self.from_number + '&to=' + to + '&text=' + str(text) + str(code) + '\nلغو11' + '&isFlash=false'
        payload = payload.encode("utf-8")
        #print(header)
        #print(payload)
        response = requests.request("POST", url = self.send_url, headers=header, data=payload)
        #print(response.status_code)
        #print(response.text)
        response_dict = json.loads(response.text)
        if response.status_code == 200 or response.status_code == 201:
            response_dict["core_status"] = True
        else:
            response_dict["core_status"] = False
        return response_dict

    def send_to_many(self, message, to_numbers):
        text = message
        header = {
            "content-type": "application/x-www-form-urlencoded; charset=utf-8"
        }
        numbers = ""
        for i in to_numbers:
            if numbers == "":
                numbers = numbers + i
            else:
                numbers = numbers + ',' + i
        payload='username=' + self.username + '&password=' + self.password + '&from=' + self.from_number + '&to=' + numbers + '&text=' + str(text) + '\nلغو11' + '&isFlash=false'
        payload = payload.encode("utf-8")
        #print(header)
        #print(payload)
        response = requests.request("POST", url = self.send_url, headers=header, data=payload)
        #print(response.status_code)
        #print(response.text)
        response_dict = json.loads(response.text)
        if response.status_code == 200 or response.status_code == 201:
            response_dict["core_status"] = True
        else:
            response_dict["core_status"] = False
        return response_dict

    def send_regular_sms(self, to, text):
        header = {
            "content-type": "application/x-www-form-urlencoded; charset=utf-8"
        }
        payload='username=' + self.username + '&password=' + self.password + '&from=' + self.from_number + '&to=' + to + '&text=' + str(text) + '\nلغو11' + '&isFlash=false'
        payload = payload.encode("utf-8")
        #print(header)
        #print(payload)
        response = requests.request("POST", url = self.send_url, headers=header, data=payload)
        #print(response.status_code)
        #print(response.text)
        response_dict = json.loads(response.text)
        if response.status_code == 200 or response.status_code == 201:
            response_dict["core_status"] = True
        else:
            response_dict["core_status"] = False
        return response_dict


    @staticmethod
    def send_phone_verification_code(self, to, code, text):
        # text = "\nکد تایید: "
        header = {
            "content-type": "application/x-www-form-urlencoded; charset=utf-8"
        }
        payload='username=' + self.username + '&password=' + self.password + '&from=' + self.from_number + '&to=' + to + '&text=' + str(text) + str(code) + '\nلغو11' + '&isFlash=false'
        payload = payload.encode("utf-8")
        #print(header)
        #print(payload)
        response = requests.request("POST", url = self.send_url, headers=header, data=payload)
        #print(response.status_code)
        #print(response.text)
        response_dict = json.loads(response.text)
        if response.status_code == 200 or response.status_code == 201:
            response_dict["core_status"] = True
        else:
            response_dict["core_status"] = False
        return response_dict
