from minio_storage.storage import MinioMediaStorage, MinioStaticStorage
from django.conf import settings
import os, sys
"""
import it in settings.py with this:

from main.modules import storage
STORAGES = storage.STORAGES

"""
storage_names = os.environ.get('STORAGES', '')
print(f"Configuring storages: {storage_names}")
current_module = sys.modules[__name__]
_storages = {}

def get_storage_class_name(storage_name):
    return f'{storage_name[0].upper()}{storage_name[1:].lower()}Storage'

def get_storage_config(storage_name):
    """Get configuration for a storage from environment variables"""
    prefix = f'{storage_name.upper()}_STORAGE'
    return {
        'endpoint': os.environ.get(f'{prefix}_ENDPOINT', 'localhost:9000'),
        'access_key': os.environ.get(f'{prefix}_ACCESS_KEY', 'minioadmin'),
        'secret_key': os.environ.get(f'{prefix}_SECRET_KEY', 'minioadmin'),
        'bucket_name': os.environ.get(f'{prefix}_BUCKET_NAME', f'{storage_name.lower()}-bucket'),
        'base_url': f"{os.environ.get(f'{prefix}_BASE_URL', '')}/{os.environ.get(f'{prefix}_BUCKET_NAME', f'{storage_name.lower()}-bucket')}",
        'use_https': os.environ.get(f'{prefix}_USE_HTTPS', 'False').lower() == 'true',
        'auto_create_bucket': os.environ.get(f'{prefix}_AUTO_CREATE_BUCKET', 'True').lower() == 'true',
        'storage_type': os.environ.get(f'{prefix}_TYPE', 'media').lower(),
    }

def generate_storage_class(storage_name):
    """Generate a dynamic storage class with environment-based configuration"""
    storage_class_name = get_storage_class_name(storage_name)
    config = get_storage_config(storage_name)
    
    # Determine if this is static or media storage
    is_static = config['storage_type'] in ['staticfiles', 'static', 'static-files', 'staticfile', 'static-file']
    
    if is_static:
        base_class = MinioStaticStorage
    else:
        base_class = MinioMediaStorage
    
    class ConfigurableMinioStorage(base_class):
        def __init__(self):
            # Set MinIO settings before parent initialization
            self._configure_minio_settings()
            super().__init__()
        
        def _configure_minio_settings(self):
            """Configure MinIO settings from environment variables"""
            # Set the common MinIO settings
            setattr(settings, 'MINIO_STORAGE_ENDPOINT', config['endpoint'])
            setattr(settings, 'MINIO_STORAGE_ACCESS_KEY', config['access_key'])
            setattr(settings, 'MINIO_STORAGE_SECRET_KEY', config['secret_key'])
            setattr(settings, 'MINIO_STORAGE_USE_HTTPS', config['use_https'])
            setattr(settings, 'MINIO_STORAGE_AUTO_CREATE_POLICY', True)
            
            # Set additional settings if they don't exist
            if not hasattr(settings, 'MINIO_STORAGE_REGION'):
                setattr(settings, 'MINIO_STORAGE_REGION', 'us-east-1')
            
            # Set storage-specific settings based on type
            if is_static:
                # For static files, set the static-specific settings
                setattr(settings, 'MINIO_STORAGE_STATIC_BUCKET_NAME', config['bucket_name'])
                setattr(settings, 'MINIO_STORAGE_AUTO_CREATE_STATIC_BUCKET', config['auto_create_bucket'])
                setattr(settings, 'MINIO_STORAGE_AUTO_CREATE_STATIC_POLICY', 'GET_ONLY')
                if config['base_url']:
                    setattr(settings, 'MINIO_STORAGE_STATIC_URL', config['base_url'])
            else:
                # For media files, set the media-specific settings
                setattr(settings, 'MINIO_STORAGE_MEDIA_BUCKET_NAME', config['bucket_name'])
                setattr(settings, 'MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET', config['auto_create_bucket'])
                if config['base_url']:
                    setattr(settings, 'MINIO_STORAGE_MEDIA_URL', config['base_url'])
        
        def url(self, name):
            """Override URL generation if base_url is provided"""
            if config['base_url']:
                return f"{config['base_url'].rstrip('/')}/{name}"
            return super().url(name)
    
    # Set proper class attributes
    ConfigurableMinioStorage.__name__ = storage_class_name
    ConfigurableMinioStorage.__qualname__ = storage_class_name
    ConfigurableMinioStorage.__module__ = __name__
    
    return ConfigurableMinioStorage

# Process and create storage classes
processed_storages = []
for storage_name in storage_names.split(','):
    storage_name = storage_name.strip()
    if not storage_name:
        continue
    
    processed_storages.append(storage_name)
    config = get_storage_config(storage_name)
    storage_class = generate_storage_class(storage_name)
    class_name = get_storage_class_name(storage_name)
    
    # Register the class in the module
    setattr(current_module, class_name, storage_class)
    globals()[class_name] = storage_class
    
    # Add to STORAGES configuration
    is_static = config['storage_type'] in ['staticfiles', 'static', 'static-files', 'staticfile', 'static-file']
    
    if is_static:
        _storages['staticfiles'] = {
            'BACKEND': f'main.modules.storage.{class_name}',
        }
        print(f"Configured staticfiles storage: {class_name}")
    else:
        _storages[storage_name.lower()] = {
            'BACKEND': f'main.modules.storage.{class_name}',
        }
        print(f"Configured {storage_name.lower()} storage: {class_name}")

# Ensure we have a default storage
if 'default' not in _storages:
    # Find the first media storage to use as default
    media_storages = {k: v for k, v in _storages.items() if k != 'staticfiles'}
    if media_storages:
        first_media_key = next(iter(media_storages.keys()))
        _storages['default'] = media_storages[first_media_key]
        print(f"Set default storage to: {first_media_key}")
    else:
        # Create a basic default storage
        print("Creating default media storage")
        default_class = generate_storage_class('default')
        setattr(current_module, 'DefaultStorage', default_class)
        globals()['DefaultStorage'] = default_class
        _storages['default'] = {
            'BACKEND': 'main.modules.storage.DefaultStorage',
        }

print(f"Final STORAGES configuration: {_storages}")
setattr(current_module, 'STORAGES', _storages)