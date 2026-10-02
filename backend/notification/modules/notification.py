from .message_object import MessageObject
from .template_renderer import NotificationTemplateRenderer
class Notification:
    def __new__(cls, to=None, message_template_key=None, gateway_type='SMS', *args, **kwargs):
        instance = super().__new__(cls)
        
        message_text = NotificationTemplateRenderer(message_template_key=message_template_key, *args, **kwargs)
        instance.message_object = MessageObject(to=to, message_text=message_text, gateway_type=gateway_type)
        return instance.send()

    def send(self):
        if self.message_object.gateway_type == "SMS":
            from .sms import SMS
            client = SMS(message_objects=[self.message_object])
            result = client.send()
            del client
            return result
        return False
