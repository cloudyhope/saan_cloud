from elasticsearch import Elasticsearch
import os
import json

class ElasticLog:

    def __init__(self) -> None:
        self.env = os.environ.get("Environment", None)
        self.es = Elasticsearch('http://10.1.10.8:9200', basic_auth=("elastic", 'Veig5uk-udae7eiM8pha.h6wo5taep5g_ooPhaen'))

    def index_log(self, log_level, log):
        # print("INJAAAAAAAAAAAAAAAAAAAA", (str('log' + log_level + '-' + str(self.env))).lower())
        self.es.index(index=(str('log' + log_level + '-' + str(self.env))).lower(), document=log)

class ElasticLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            logger = ElasticLog()
            # REQUEST:
            req = request.__dict__
            req_keys = req.keys()
            my_request = {}
            for i in req_keys:
                if i in ['path', 'method', ]:
                    my_request[i] = req[i]
            # RESPONSE:
            resp = response.__dict__
            my_response = {}
            resp_keys = resp.keys()
            for i in resp_keys:
                if i in ['status_code', 'data', ]:
                    my_response[i] = resp[i]
            logger.index_log('info', {"request": my_request, "resp": my_response})
        except:
            pass
        return response