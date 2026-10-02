import datetime
import random
import string

from django.contrib.auth.models import User
from django.db import models
from urllib.parse import urlsplit
from django.core.validators import MinValueValidator

'''
Plan is going to create by us!
If any New plan is required please set is_active to False and create a new one. 
you may be able to have duplicate plan!
plans are not changeable!
On save , checks if min and max are not mis placed 
 '''


class Plan(models.Model):
    title = models.TextField(max_length=255, blank=True, null=True)
    description = models.TextField(max_length=255, blank=True, null=True)
    limited_create_number = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1)])
    duration_day = models.IntegerField(default=90, blank=True, validators=[MinValueValidator(1)], null=True)
    max_length = models.IntegerField(default=8, validators=[MinValueValidator(1)])
    min_length = models.IntegerField(default=6, validators=[MinValueValidator(1)])
    extera_back_half_allowed = models.BooleanField(default=True, blank=True)
    back_half_allowed = models.BooleanField(default=True, blank=True)
    lower_case_characters = models.BooleanField(default=True, blank=True)
    number_characters = models.BooleanField(default=True, blank=True)
    upper_case_characters = models.BooleanField(default=True, blank=True)
    other_characters = models.BooleanField(default=True, blank=True)
    eternal_allowed = models.BooleanField(default=False, blank=True)
    price = models.IntegerField(blank=True, null=True, default=None)
    has_advertise_plan = models.BooleanField(default=False, blank=True)
    has_sms_plan = models.BooleanField(default=False, blank=True)
    is_active = models.BooleanField(default=True, blank=True)
    datetime_created = models.DateTimeField(auto_now_add=True, blank=True)

    #todo validate price
    def save(self, *args, **kwargs):
        if self.max_length >= self.min_length:
            return super(Plan, self).save(*args, **kwargs)
        max_len = max(self.max_length, self.min_length)
        min_len = min(self.min_length, self.max_length)
        self.max_length = max_len
        self.min_length = min_len
        return super(Plan, self).save(*args, **kwargs)

    # todo stop it from being deleted with sub records


# todo sms plan and advertise plan and payment
# class AdvertisePlan(models.Model):
#     pass
#
#
# class SMSPlan(models.Model):
#     pass
#
#
# class Payment(models.Model):
#     pass


'''
each user have a plan to separate advertise plan or sms plan bace on person. it is a todo now:)
it is changeable
'''


# todo Automatic renewal
class UserPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    datetime_created = models.DateTimeField(auto_now_add=True, blank=True)
    datetime_last_change = models.DateTimeField(auto_now=True, blank=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    # advertise = models.ForeignKey(AdvertisePlan, on_delete=models.CASCADE, null=True, blank=True)
    # sms = models.ForeignKey(SMSPlan, on_delete=models.CASCADE, null=True, blank=True)
    # payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=True, blank=True)
    is_deleted = models.BooleanField(default=False, blank=True)

    # todo check sms and avertise in plan, check payment and date add to expires
    def save(self, *args, **kwargs):
        # if self.expires_at is None and self.plan.duration_day:
        #     duration_day = self.plan.duration_day  # todo recheck
        #     self.expires_at = datetime.datetime.now() + datetime.timedelta(days=duration_day)
        #     return super(UserPlan, self).save(*args, **kwargs)
        return super(UserPlan, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        return super(UserPlan, self).save(*args, **kwargs)


''' 
long url witch needs to detected in API before generating is in url
in save method we replace it with LongURL (get or create) , then
ShortUrl is going to save in url and we can use it.
get_usage_data is base on plan limitation.   
'''


# todo other kind of Long_url check and support
class ShortUrl(models.Model):
    user_plan = models.ForeignKey(UserPlan, on_delete=models.CASCADE)
    long_url = models.TextField(max_length=255, unique=True)
    url = models.TextField(max_length=255, blank=True, null=True)
    title = models.TextField(max_length=255, blank=True, null=True)
    description = models.TextField(max_length=255, blank=True, null=True)
    is_eternal = models.BooleanField(default=False, blank=True)
    back_half = models.TextField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True, blank=True)
    is_deleted = models.BooleanField(default=False, blank=True)
    datetime_last_change = models.DateTimeField(auto_now=True, blank=True)
    datetime_created = models.DateTimeField(auto_now_add=True, blank=True)
    domain = models.CharField(max_length=255, blank=True, default=None, null=True)

    def get_usage_data(self):
        CHARACTERS = ''
        if self.user_plan.plan.lower_case_characters:
            CHARACTERS += string.ascii_lowercase.replace('i', '').replace('o', '').replace('l', '')
        if self.user_plan.plan.upper_case_characters:
            CHARACTERS += string.ascii_uppercase.replace('I', '').replace('O', '').replace('L', '')
        if self.user_plan.plan.other_characters:
            CHARACTERS += r"""!&()*+-.:;=?@_"""
        if self.user_plan.plan.number_characters:
            CHARACTERS += string.digits.replace('0', '').replace('1', '')

        limited_create_number = self.user_plan.plan.limited_create_number
        eternal_allowed = self.user_plan.plan.eternal_allowed
        max_length = self.user_plan.plan.max_length
        min_length = self.user_plan.plan.min_length
        back_half_allowed = self.user_plan.plan.back_half_allowed
        extera_back_half_allowed = self.user_plan.plan.extera_back_half_allowed

        data = {'CHARACTERS': CHARACTERS, 'limited_create_number': limited_create_number,
                'eternal_allowed': eternal_allowed, 'max_length': max_length, 'min_length': min_length,
                'back_half_allowed': back_half_allowed, 'extera_back_half_allowed': extera_back_half_allowed, }
        return data

    def generate_short_url(self, data) -> str:
        if data['back_half_allowed']:
            if self.back_half:
                short_url = self.back_half + '/'
            else:
                short_url = ''
            exist_values = ShortUrl.objects.filter(user_plan__plan=self.user_plan.plan,
                                                   url__startswith=f'{self.back_half}').count()
            if exist_values < (len(data['CHARACTERS']) ** (data['max_length'] - data['min_length'] - 1)):
                while True:
                    length = random.randint(data['min_length'], data['min_length'])
                    short_url += ''.join(
                        random.choice(data['CHARACTERS'])
                        for _ in range(length + 1)
                    )
                    if not ShortUrl.objects.filter(url=short_url).first():
                        return short_url
            elif data['extera_back_half_allowed'] and exist_values < (
                    ((len(data['CHARACTERS']) ** data['min_length'])) * (
                    len(data['CHARACTERS']) ** (data['max_length'] - data['min_length'] - 1))):
                while True:
                    length = random.randint(data['min_length'], data['min_length'])
                    back_length = random.randint(0, data['min_length'])
                    short_url += ''.join(
                        random.choice(data['CHARACTERS'])
                        for _ in range(back_length + 1)
                    )
                    short_url += '/'
                    short_url += ''.join(
                        random.choice(data['CHARACTERS'])
                        for _ in range(length + 1)
                    )
                    if ShortUrl.objects.filter(url=short_url).first() is None:
                        return short_url
            else:
                return 'No More space for this plan'
        else:
            exist_values = ShortUrl.objects.filter(user_plan__plan=self.user_plan.plan).count()
            if exist_values < (len(data['CHARACTERS']) ** (data['max_length'] - data['min_length'] - 1)):
                while True:
                    length = random.randint(data['min_length'], data['min_length'])

                    short_url = ''.join(
                        random.choice(data['CHARACTERS'])
                        for _ in range(length + 1)
                    )
                    if not ShortUrl.objects.filter(url=short_url).first():
                        return short_url
            elif data['extera_back_half_allowed'] and exist_values < (
                    len(data['CHARACTERS']) ** (data['max_length'] - data['min_length'] - 1)):
                while True:
                    length = random.randint(data['min_length'], data['min_length'])
                    back_length = random.randint(0, data['min_length'])
                    short_url = ''.join(
                        random.choice(data['CHARACTERS'])
                        for _ in range(back_length + 1)
                    )
                    short_url += '/'
                    short_url += ''.join(
                        random.choice(data['CHARACTERS'])
                        for _ in range(length + 1)
                    )
                    if ShortUrl.objects.filter(url=short_url).first() is None:
                        return short_url
            else:
                return 'No More space for this plan'

    '''
         The maximum length of a full host name is 253 characters per RFC 1034
         section 3.1. It's defined to be 255 bytes or less, but this includes
         one byte for the length of the name and one byte for the trailing dot
         that's used to indicate absolute names in DNS.
     '''

    def set_domain(self):
        schemes = ["http", "https", "ftp", "ftps"]
        unsafe_chars = frozenset("\t\r\n")

        if not isinstance(self.long_url, str) or unsafe_chars.intersection(self.long_url):
            return None

        try:
            splitted_url = urlsplit(self.long_url)
            unsplit_scheme = self.long_url.split("://")[0].lower()
            if splitted_url.hostname is None or len(splitted_url.hostname) > 253 or unsplit_scheme not in schemes:
                return None
            scheme, netloc, path, query, fragment = splitted_url
            return netloc
        except 'not a valid URL':
            return None

    # todo move No spase to view
    def save(self, *args, **kwargs):
        short_url = self.generate_short_url(self.get_usage_data())
        self.domain = self.set_domain()
        if short_url == 'No More space for this plan':
            return 'No More space for this plan'
        self.url = short_url
        return super(ShortUrl, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        return super(ShortUrl, self).save(*args, **kwargs)


class ClickLog(models.Model):
    user_plan = models.ForeignKey(UserPlan, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField(protocol='both', null=True, blank=True)
    short_url = models.ForeignKey(ShortUrl, on_delete=models.CASCADE, null=True, blank=True)
    # browser = models.CharField(max_length=255, null=True, blank=True)
    # device = models.CharField(max_length=255, null=True, blank=True)
    datetime_created = models.DateTimeField(auto_now_add=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
