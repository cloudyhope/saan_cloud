from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework import exceptions, generics, serializers
from auth_app.models import *
from auth_app.user_serializers import SafeUserSerializer, UserSerializer

class UserOnlySerializer(SafeUserSerializer):
    pass

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'


class DocumentPhotoSerializer(serializers.ModelSerializer):
    document = DocumentSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    file = serializers.SerializerMethodField()

    class Meta:
        model = DocumentPhoto
        fields = '__all__'

    def get_file(self, obj):
        from core.media_access import media_read_url
        return media_read_url(obj.file, self.context.get('request'), storage='docs')


class DocumentPhotoOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentPhoto
        fields = '__all__'


class DocumentPhotoInputSerializer(serializers.ModelSerializer):
    document = DocumentSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    file = serializers.SerializerMethodField()

    class Meta:
        model = DocumentPhoto
        fields = '__all__'

    def get_file(self, obj):
        from core.media_access import media_read_url
        return media_read_url(obj.file, self.context.get('request'), storage='docs')


class DocumentPhotoOnlyInputSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True)

    class Meta:
        model = DocumentPhoto
        fields = ('document', 'file')

    def validate(self, attrs):
        unexpected = set(self.initial_data) - {'document', 'file'}
        if unexpected:
            raise serializers.ValidationError({field: 'این فیلد از این مسیر قابل ثبت نیست.'
                                               for field in unexpected})
        return attrs


class DocumentPhotoReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentPhoto
        fields = ('supervisor_confirm', 'confirm_status', 'is_checked')

    def validate(self, attrs):
        unexpected = set(self.initial_data) - set(self.fields)
        if unexpected:
            raise serializers.ValidationError({field: 'این فیلد از این مسیر قابل ویرایش نیست.'
                                               for field in unexpected})
        return attrs


class SingInExtendedUserSerializer(serializers.ModelSerializer):
    user = UserOnlySerializer()

    class Meta:
        model = ExtendedUser
        fields = '__all__'



class SingInExtendedUserOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtendedUser
        fields = '__all__'


# class UserOnlySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = '__all__'

class ExtendedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtendedUser
        fields = '__all__'

class LiteExtendedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtendedUser
        fields = '__all__'

class LiteUserSerializer(serializers.ModelSerializer):
    extended = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'extended',)

    def get_extended(self, obj):
        query = ExtendedUser.objects.filter(user = obj)
        if len(query) > 0:
            return LiteExtendedUserSerializer(query[0], many=False).data
        else:
            return LiteExtendedUserSerializer(ExtendedUser(), many=False).data


# todo refactor from view

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'
