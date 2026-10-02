
from decimal import Decimal
from datetime import datetime
from rest_framework import serializers
from collections import OrderedDict


class AdditionalSerializer(serializers.ModelSerializer):

    def number_seprator(self, number, by=','):
        if number is None or not str(number).isnumeric():
            return 0
        return f'{int(number):{by}}'

    def translate_number_to_persian(self, number):
        if number is None or not str(number).isnumeric():
            return 0
        # Fa_to_En= str.maketrans({"۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4", "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9"," ":"",})
        En_to_Fa = str.maketrans(
            {"0": "۰", "1": "۱", "2": "۲", "3": "۳", "4": "۴", "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹",
             " ": "", })
        return str(number).translate(En_to_Fa)

    def datetime_to_jalali(self, d):
        from persiantools.jdatetime import JalaliDateTime
        from dateutil import parser
        from datetime import timedelta
        date = parser.parse(d)
        now = list(str(JalaliDateTime.to_jalali(date) + timedelta(minutes=210)).split())
        year = now[0].replace('-', '/')
        hour = now[1].split('.')[0]
        final = f"{year} {hour}"
        return final

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        s = OrderedDict()
        # print(representation)
        for field, value in representation.items():
            s[field] = value
            special_value = value
            special_value = self.translate_number_to_persian(self.number_seprator(special_value))
            # print(field, type(value), value)
            if isinstance(value, (int, float, Decimal)):
                # print('find')
                s[f'{field}_separate'] = self.number_seprator(value)
                s[f'{field}_persian'] = self.translate_number_to_persian(value)
            if isinstance(value, str) and 'date' in field:
                s[f'{field}_fa'] = self.datetime_to_jalali(value)
        return s

