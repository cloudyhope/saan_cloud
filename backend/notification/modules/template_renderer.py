from main.models import Config
from ..models import MessageTemplate
from string import Template


class NotificationTemplateRenderer:
    def __new__(cls, message_template_key=None, *args, **kwargs):
        instance = super().__new__(cls)
        
        instance.text = ''
        instance.message_template_key = message_template_key

        return instance.get_message(*args, **kwargs)

    def __del__(self):
        self.text = ''
        self.message_template_key = None

    def get_message(self, *args, **kwargs):

        category_type = f'SMS_{self.message_template_key.upper()}'
        configs = Config.objects.filter(category=category_type)

        subs = {}
        if configs.exists():
            for per_config in configs:
                if per_config.key and per_config.value:
                    subs.update({per_config.key: per_config.value})
                else:
                    self.text = None
                    return None

        message_text = MessageTemplate.objects.filter(key=self.message_template_key.upper(), is_deleted=False).first()
        if message_text is None:
            self.text = None
            return None
        if not message_text.msg_template:
            self.text = None
            return None
        template = Template(message_text.msg_template)
        mapping = {**subs, **kwargs}
        self.text = template.substitute(**mapping)
        return self.text