from minio_storage.storage import MinioMediaStorage, MinioStaticStorage
import os, sys
storage_names = os.environ.get('STORAGES', '')
print(storage_names)
current_module = sys.modules[__name__]
_storages = {}


def get_storage_class_name(storage_name):
    return f'{storage_name[0].upper()}{storage_name[1:].lower()}Storage'

def generate_storage_class(storage_name):
    storage_class_name = get_storage_class_name(storage_name)
    storage_connection_dict = {
        'endpoint': os.environ.get(f'{storage_name.upper()}_STORAGE_ENDPOINT', ''), # 'https://s3.amazonaws.com'
        'bucket_name': os.environ.get(f'{storage_name.upper()}_STORAGE_BUCKET_NAME', ''), # 'user-uploads'
        'base_url': os.environ.get(f'{storage_name.upper()}_STORAGE_BASE_URL', ''), # 'https://cdn.example.com/uploads/'
        'access_key': os.environ.get(f'{storage_name.upper()}_STORAGE_ACCESS_KEY', ''), # 'AWS_ACCESS_KEY'
        'secret_key': os.environ.get(f'{storage_name.upper()}_STORAGE_SECRET_KEY', ''), # 'AWS_SECRET_KEY'
    }
    if os.environ.get(f'{storage_name.upper()}_STORAGE_TYPE', '').lower() in ['staticfiles', 'static', 'static-files', 'staticfile', 'static-file']:
        return type(storage_class_name, (MinioStaticStorage,), storage_connection_dict)
    elif os.environ.get(f'{storage_name.upper()}_STORAGE_TYPE', '').lower() in ['media', '']:
        return type(storage_class_name, (MinioMediaStorage,), storage_connection_dict)

for storage_name in storage_names.split(','):
    if storage_name == '' or storage_name is None:
        continue
    if storage_name.lower() in ['staticfiles', 'static', 'static-files', 'staticfile', 'static-file'] and os.environ.get(f'{storage_name.upper()}_STORAGE_TYPE', '').lower() in ['staticfiles', 'static', 'static-files', 'staticfile', 'static-file']:
        _storages['staticfiles'] = {
            'BACKEND': f'main.modules.storage.{get_storage_class_name(storage_name)}',
        }
    else:
        _storages[storage_name.lower()] = {
            'BACKEND': f'main.modules.storage.{get_storage_class_name(storage_name)}',
        }
    setattr(current_module, get_storage_class_name(storage_name), generate_storage_class(storage_name)) 
setattr(current_module, 'STORAGES', _storages)
