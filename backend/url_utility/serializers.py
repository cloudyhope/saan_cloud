from rest_framework import serializers

from url_utility.models import *

from auth_app.serializers import UserSerializer

# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = '__all__'


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'


# todo remove exclude after sms and payment and advertise
class UserPlanSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    plan = PlanSerializer()

    class Meta:
        model = UserPlan
        fields = '__all__'
        # exclude = ['payment', 'sms', 'advertise']


class UserPlanOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPlan
        fields = '__all__'
        # exclude = ['payment', 'sms', 'advertise']


class ShortUrlOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShortUrl
        fields = '__all__'


class UserPlanOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPlan
        fields = '__all__'
        # exclude = ['payment', 'sms', 'advertise']


class ShortUrlOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShortUrl
        fields = '__all__'


class ShortUrlSerializer(serializers.ModelSerializer):
    user_plan = UserPlanSerializer()

    class Meta:
        model = ShortUrl
        fields = '__all__'


class ClickLogOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = ClickLog
        fields = '__all__'


class ClickLogSerializer(serializers.ModelSerializer):
    short_url = ShortUrlSerializer()
    user_plan = UserPlanSerializer()

    class Meta:
        model = ClickLog
        fields = '__all__'


class ShortURLMicroServiceGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShortUrl
        fields = ['url', 'long_url', 'user_plan']
