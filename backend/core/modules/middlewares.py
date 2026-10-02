from time import time
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from utils.models import RequestLog
from threading import Thread
from inspect import iscoroutinefunction

class SaveRequestLogMiddleware(MiddlewareMixin):
    def __call__(self, request):
        if iscoroutinefunction(self):
            return self.__acall__(request)
        response = None
        if hasattr(self, "process_request"):
            response = self.process_request(request)
        response = response or self.get_response(request)
        if hasattr(self, "process_response"):
            response = self.process_response(request, response)
        return response

    def process_request(self, request):
        request.start_t = time()
        request.datetime_create = timezone.now()

    def process_response(self, request, response):
        try:
            start_t = getattr(request, 'start_t', None)
            datetime_create = getattr(request, 'datetime_create', None)

            if start_t and datetime_create:
                during_t = int((time() - start_t) * 1000)
                datetime_save = timezone.now()
                headers = request.headers.keys()
                device_id = ''
                referer = ''
                for header in headers:
                    header_check = header.upper().replace('_', '-')
                    if header_check == 'DEVICE-CLIENT-USER':
                        device_id = request.headers.get(header, '')
                    elif header_check == 'CLIENT-USER-REFERER':
                        referer = request.headers.get(header, '')

                try:
                    request_log = RequestLog(
                        endpoint_url=request.get_full_path(),
                        response_code=response.status_code,
                        method=request.method,
                        remote_address=self.get_client_ip(request),
                        exec_time=during_t,
                        datetime_created=datetime_create,
                        datetime_response_received=datetime_save,
                        device_id=device_id,
                        referer=referer
                    )
                except Exception as e:
                    print(e)
                    return response
                if not request.user.is_anonymous:
                    request_log.user_name = request.user.username

                try:
                    request_log.save()
                    try:
                        if str(response.status_code).startswith('5'):
                            from auth_app.models import ExtendedUser
                            from utils.modules.farapayamak import FaraPayamak
                            from utils.serializers import RequestLogSerializer
                            admins = list(ExtendedUser.objects.filter(roles__role_title='devs').values_list('user__username', flat=True))
                            # client = FaraPayamak(admins)
                            # client.type_send('ERROR_500_ADMIN', **RequestLogSerializer(request_log, many=False).data)
                            # del client
                    except:
                        pass
                except Exception as e:
                    print(f'Error saving request log synchronously: {e}')
                    return response
            return response
        except Exception as e:
            print(e)
            return response

    def process_exception(self, request, exception):
        print(f'Exception encountered: {exception}')
        return None

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    @staticmethod
    def save_request_log_async(request_log):
        def save_log():
            try:
                request_log.save()
            except Exception as e:
                print(f'Error saving request log asynchronously: {e}')
        Thread(target=save_log).start()