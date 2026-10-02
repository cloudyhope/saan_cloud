from rest_framework import serializers

from core.modules.serializers import AdditionalSerializer
from auth_app.serializers import LiteUserSerializer

from utils.models import RequestLog, Conversation, ConversationMessage


class RequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestLog
        fields = '__all__'


class ConversationSerializer(AdditionalSerializer):
    class Meta:
        model = Conversation
        fields = '__all__'


class ConversationMessageSerializer(AdditionalSerializer):

    class Meta:
        model = ConversationMessage
        fields = '__all__'

class ConversationSeenSerializer(serializers.Serializer):
    conversation_id = serializers.IntegerField()
    is_seen = serializers.BooleanField()

class FullConversationSerializer(AdditionalSerializer):
    creator = LiteUserSerializer(allow_null=True, required=False)
    unseen_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    def get_unseen_count(self, obj):
        return_val = ConversationMessage.objects.filter(conversation=obj, is_seen=False).count()
        return 0 if type(return_val) is not int else return_val

    def get_last_message(self, obj):
        last_msg = ConversationMessage.objects.filter(conversation=obj).order_by('-datetime_created').first()
        if last_msg is None:
            last_msg = ConversationMessage()
        return ConversationMessageSerializer(last_msg, many=False).data

    class Meta:
        model = Conversation
        fields = '__all__'



class FullConversationMessageWithOutParentSerializer(AdditionalSerializer):
    user = LiteUserSerializer(allow_null=True, required=False)
    conversation = ConversationMessageSerializer()

    class Meta:
        model = ConversationMessage
        fields = '__all__'


class FullConversationMessageSerializer(AdditionalSerializer):
    user = LiteUserSerializer()
    conversation = FullConversationSerializer()
    parent = ConversationMessageSerializer()

    class Meta:
        model = ConversationMessage
        fields = '__all__'