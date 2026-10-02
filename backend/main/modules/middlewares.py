import json
import time
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.contrib.auth import get_user_model
User = get_user_model()


class BaseMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_time = time.time()

    def process_response(self, request, response):
        # Calculate response time
        response_time = time.time() - request._start_time if hasattr(request, '_start_time') else None

        # Create single JSON-serializable variable
        captured_data = {
            'request_body': self.get_request_body(request),
            'response_body': self.get_response_body(response),
            'request_headers': dict(request.headers),
            'response_headers': dict(response.headers) if hasattr(response, 'headers') else {},
            'status_code': response.status_code,
            'response_time': response_time,
            'client_ip': self.get_client_ip(request),
            'method': request.method,
            'path': request.path,
            'view_name': self.get_view_name(request),
            'user_id': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
            'timestamp': time.time()
        }

        # Your custom logic here - captured_data is ready for MongoDB
        self.handle_captured_data(captured_data)
        
        return response

    def get_request_body(self, request):
        """Get request body as string or parsed JSON"""
        try:
            if hasattr(request, 'body') and request.body:
                body_str = request.body.decode('utf-8')
                # Try to parse as JSON for better structure
                try:
                    return json.loads(body_str)
                except json.JSONDecodeError:
                    return body_str
            return None
        except:
            return None

    def get_response_body(self, response):
        """Get response body as string or parsed JSON"""
        try:
            if hasattr(response, 'content') and response.content:
                content_str = response.content.decode('utf-8')
                # Try to parse as JSON for better structure
                try:
                    return json.loads(content_str)
                except json.JSONDecodeError:
                    return content_str
            return None
        except:
            return None

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def get_view_name(self, request):
        """Get view name if available"""
        try:
            if hasattr(request, 'resolver_match') and request.resolver_match:
                return request.resolver_match.view_name
            return None
        except:
            return None

    def handle_captured_data(self, captured_data):
        """
        Your custom logic here.
        captured_data is a single JSON-serializable dictionary ready for MongoDB
        """
        if 'notification' in settings.PROJECT_APPS:
            from notification.modules.tools import flatten_dict
            from notification.modules.notification import Notification
            from notification.models import MessageTemplate
            message_templates = MessageTemplate.objects.filter(view=captured_data['view_name'])
            for message_template in message_templates:
                if message_template.type == "SMS":
                    if message_template.to == "__me__" or message_template.to == "__ME__":
                        to = User.objects.get(id=captured_data['user_id']).username
                    else:
                        to = message_template.to
                elif message_template.type == "EMAIL":
                    if message_template.to == "__me__" or message_template.to == "__ME__":
                        to = User.objects.get(id=captured_data['user_id']).email
                    else:
                        to = message_template.to

                Notification(
                    to=to,
                    message_template_key=message_template.key,
                    type=message_template.type,
                    **flatten_dict(captured_data)
                )
        # Example: Print the data
        print(f"Captured data: {json.dumps(captured_data, indent=2)}")
        
        # Ready to save to MongoDB:
        # collection.insert_one(captured_data)
        pass
