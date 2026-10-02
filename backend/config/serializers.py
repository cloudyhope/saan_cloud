from rest_framework import serializers


class HealCheckSerializer(serializers.Serializer):
    detail = serializers.CharField(allow_null=True, allow_blank=True)

    class Meta:
        fields = '__all__'


from rest_framework import serializers
from config.models import (
    Config,
    NavMenu,
    MediaManager,
    TagManager,
    TagType,
    MediaType
)
from auth_app.serializers import RoleSerializer

from core.modules.serializers import AdditionalSerializer



class ConfigSerializer(AdditionalSerializer):
    class Meta:
        model = Config
        fields = '__all__'


class NavMenuSerializer(AdditionalSerializer):
    role = RoleSerializer()

    class Meta:
        model = NavMenu
        fields = '__all__'


class NavMenuOnlySerializer(AdditionalSerializer):
    class Meta:
        model = NavMenu
        fields = '__all__'


class MediaTypeSerializer(AdditionalSerializer):
    class Meta:
        model = MediaType
        fields = '__all__'


class MediaManagerSerializer(AdditionalSerializer):
    type = MediaTypeSerializer()
    class Meta:
        model = MediaManager
        fields = '__all__'

class OnlyMediaManagerSerializer(AdditionalSerializer):
    class Meta:
        model = MediaManager
        fields = '__all__'

class TagTypeSerializer(AdditionalSerializer):
    class Meta:
        model = TagType
        fields = '__all__'



class OnlyTagManagerSerializer(AdditionalSerializer):
    class Meta:
        model = TagManager
        fields = '__all__'


class TagManagerSerializer(AdditionalSerializer):
    type = TagTypeSerializer()

    class Meta:
        model = TagManager
        fields = '__all__'

