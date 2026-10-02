"""Explicit user fields for API output; credentials and Django grants stay private."""
from django.contrib.auth.models import User
from rest_framework import serializers
from auth_app.models import City, Province, ExtendedUser


class SafeUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name', 'email',
            'is_active', 'date_joined', 'last_login',
        )
        read_only_fields = ('id', 'is_active', 'date_joined', 'last_login')


class UserProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = '__all__'


class UserCitySerializer(serializers.ModelSerializer):
    province = UserProvinceSerializer()

    class Meta:
        model = City
        fields = '__all__'


class UserExtendedSerializer(serializers.ModelSerializer):
    city = UserCitySerializer()

    class Meta:
        model = ExtendedUser
        fields = '__all__'


class UserSerializer(SafeUserSerializer):
    extended = serializers.SerializerMethodField()

    class Meta(SafeUserSerializer.Meta):
        fields = SafeUserSerializer.Meta.fields + ('extended',)

    def get_extended(self, obj):
        extended = ExtendedUser.objects.filter(user=obj).first()
        return UserExtendedSerializer(extended).data if extended else {}
