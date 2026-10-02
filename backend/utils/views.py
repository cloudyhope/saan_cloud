from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from core.modules.views import (
    List,
    Create,
    ListCreate,
    Retrieve,
    Update,
    Destroy,
    RetrieveDestroy,
    RetrieveUpdate,
    RetrieveUpdateDestroy,
    Generic,
    )
from auth_app.models import ExtendedUser
from utils.models import Conversation, ConversationMessage
from rest_framework.permissions import IsAuthenticated
from utils.serializers import (
    ConversationSerializer, 
    FullConversationSerializer, 
    ConversationMessageSerializer,
    FullConversationMessageSerializer, 
    ConversationSeenSerializer,
    )
from utils.modules.farapayamak import FaraPayamak
from django.utils.translation import gettext_lazy as _


class ConversationListCreateView(ListCreate):

    # permission_classes = [AllowAny]

    def get_queryset(self):
        from django.db.models import Q
        return Conversation.objects.filter(Q(creator=self.request.user) | Q(visit__in=StoreLoyaltyPlanPersonel.objects.filter(user=self.request.user).values_list('store_loyalty_plan', flat=True)), is_deleted=False)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return FullConversationSerializer
        return ConversationSerializer

    def perform_create(self, serializer):

        store_loyalty_plan_obj = serializer.validated_data['store_loyalty_plan']

        if not store_loyalty_plan_obj.is_active or (store_loyalty_plan_obj.datetime_valid < timezone.now()):
            raise PermissionDenied()

        serializer.validated_data['creator'] = self.request.user

        # client = FaraPayamak(self.request.user.username)
        # client.type_send("CONVERSATION_STARTED_FOR_USER", **serializer.validated_data)
        # del client
        from notification.modules.notification import Notification
        Notification(to=self.request.user.username, message_template_key="CONVERSATION_STARTED_FOR_USER", **serializer.validated_data)



        usernames_in_store = list(StoreLoyaltyPlanPersonel.objects.filter(store_loyalty_plan=store_loyalty_plan_obj).values_list('user__username', flat=True))
        # store_client = FaraPayamak(usernames_in_store)
        # store_client.type_send("CONVERSATION_STARTED_TO_STORE", **serializer.validated_data)
        # del store_client
        
        from notification.modules.notification import Notification
        for this_number in usernames_in_store:
            Notification(to=this_number, message_template_key="CONVERSATION_STARTED_TO_STORE", **serializer.validated_data)

        return super().perform_create(serializer)


class ConversationRetrieveUpdateDestroyView(RetrieveUpdateDestroy):

    def get_queryset(self):
        from django.db.models import Q
        return Conversation.objects.filter(Q(creator=self.request.user) | Q(store_loyalty_plan__in=StoreLoyaltyPlanPersonel.objects.filter(user=self.request.user).values_list('store_loyalty_plan', flat=True)), is_deleted=False)

    serializer_class = ConversationSerializer


class ConversationMessageListCreateView(ListCreate):

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from django.db.models import Q
        return ConversationMessage.objects.filter(Q(conversation__creator=self.request.user) | Q(conversation__store_loyalty_plan__in=StoreLoyaltyPlanPersonel.objects.filter(user=self.request.user).values_list('store_loyalty_plan', flat=True)), is_deleted=False)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return FullConversationMessageSerializer
        return ConversationMessageSerializer

    def perform_create(self, serializer):
        flag = False
        conversation_obj = serializer.validated_data['conversation']

        if not conversation_obj.store_loyalty_plan.is_active or (conversation_obj.store_loyalty_plan.datetime_valid < timezone.now()):
            raise PermissionDenied(_("Expired Store!"))

        usernames_in_store = list(StoreLoyaltyPlanPersonel.objects.filter(store_loyalty_plan=conversation_obj.store_loyalty_plan).values_list('user__username', flat=True))

        if self.request.user.username in usernames_in_store:
            flag = True
            serializer.validated_data['user'] = self.request.user
            # client = FaraPayamak(conversation_obj.creator.username)
            # client.type_send("CONVERSATION_MESSAGE_FOR_USER", **serializer.validated_data)
            # del client
            from notification.modules.notification import Notification
            Notification(to=conversation_obj.creator.username, message_template_key="CONVERSATION_MESSAGE_FOR_USER", **serializer.validated_data)


        if self.request.user == conversation_obj.creator:
            flag = True
            serializer.validated_data['user'] = self.request.user
            # stor_client = FaraPayamak(usernames_in_store)
            # stor_client.type_send("CONVERSATION_MESSAGE_FOR_STORE", **serializer.validated_data)
            # del stor_client
            from notification.modules.notification import Notification
            for this_number in usernames_in_store:
                Notification(to=this_number, message_template_key="CONVERSATION_MESSAGE_FOR_STORE", **serializer.validated_data)

        if flag:
            return super().perform_create(serializer)
        else:
            raise PermissionDenied


class ConversationMessageRetrieveUpdateDestroyView(RetrieveUpdateDestroy):

    def get_queryset(self):
        from django.db.models import Q
        return ConversationMessage.objects.filter(Q(conversation__creator=self.request.user) | Q(conversation__store_loyalty_plan__in=StoreLoyaltyPlanPersonel.objects.filter(user=self.request.user).values_list('store_loyalty_plan', flat=True)), is_deleted=False)

    serializer_class = ConversationMessageSerializer


class ConversationSeenCreateView(Generic):
    
    serializer_class = ConversationSeenSerializer
    queryset = Conversation.objects.all()
    

    def put(self, serializer):
        obj = Conversation.objects.filter(id=self.request.data['conversation_id']).first()
        if not self.request.data['is_seen'] or obj is None:
            from core.modules.exceptions import NotAcceptable
            raise NotAcceptable("Sorry, Nothing to do!")
        all_personels = StoreLoyaltyPlanPersonel.objects.filter(store_loyalty_plan=obj.store_loyalty_plan, store_loyalty_plan__datetime_valid__gte=timezone.now()).values_list('user', flat=True)
        all_messages = ConversationMessage.objects.filter(conversation=obj)
        if self.request.user == obj.creator:
            my_messages = all_messages.filter(user=self.request.user)
        elif self.request.user.id in all_personels:
            my_messages = all_messages.filter(user__id__in=all_personels)
        my_messages.update(is_seen=True)
        return Response({"detail": "ok"})


class AdminConversionList(List):
    def get_queryset(self):
        return Conversation.objects.all()
    serializer_class = FullConversationSerializer

class AdiminConversationMessageList(List):
    def get_queryset(self):
        return ConversationMessage.objects.all()
    serializer_class = FullConversationMessageSerializer

