

class MessageObject:
    # Valid Types: 'SMS' and 'EMAIL'
    def __init__(self, to=None, message_text=None, gateway_type='SMS'):
        self.to = to
        self.message_text = message_text
        self.gateway_type = gateway_type

    def __str__(self):
        return f'{self.gateway_type} - {self.to} - {self.message_text}'

    def __repr__(self):
        return str({
            "to": self.to,
            "message_text": self.message_text,
            "type": self.gateway_type,
        })
