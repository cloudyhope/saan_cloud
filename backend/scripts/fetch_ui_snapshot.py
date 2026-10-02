"""Read a bounded production sample for the explicitly requested local preview."""
import argparse
import getpass
import concurrent.futures
import json
from pathlib import Path
import requests

parser = argparse.ArgumentParser(description='Download a bounded API sample for local UI development.')
parser.add_argument('--username')
parser.add_argument('--output', type=Path, default=Path('data/production-snapshot.json'))
args = parser.parse_args()
BASE = 'https://api.saanapp.ir'
username = args.username or input('Production username: ')
password = getpass.getpass('Production password: ')
login = requests.post(BASE + '/api/v1/username/password/token/', json={'username': username, 'password': password}, timeout=30)
if login.status_code != 200:
    raise SystemExit('Production login failed (HTTP ' + str(login.status_code) + ').')
HEADERS = {'Authorization': 'Bearer ' + login.json()['access']}
ENDPOINTS = {
    'menus': '/core/api/admin/menu/list/?p=1&is_active=true',
    'profile': '/core/api/active_project/retrieve/1/?p=1',
    'roles': '/core/api/auth/roles/list_create/?p=1&limit=100',
    'assignments': '/core/api/admin/role_assignment/list/?p=1&limit=100&ordering=-user',
    'cities': '/core/api/active_city/list/?p=1&limit=200',
    'visit_types': '/core/api/admin/visit_type/list_create/?p=1&limit=100',
    'visits': '/core/api/admin/visit_list/?p=1&limit=100&ordering=-datetime_created',
    'surveys': '/core/api/admin/survey/list_create/?p=1&limit=100',
    'survey_fillouts': '/core/api/admin/survey_fill_out/list_create/?p=1&limit=100&ordering=-datetime_created',
    'tickets': '/core/api/admin/ticket/list_create/?p=1&limit=100&ordering=-datetime_created',
    'ticket_messages': '/core/api/admin/ticket_message/list_create/?p=1&limit=100&ordering=-datetime_created',
    'ware_types': '/core/api/warehouse/v1/ware_type/list_create/?p=1&limit=100',
    'units': '/core/api/warehouse/v1/unit/list_create/?p=1&limit=100',
    'wares': '/core/api/warehouse/v1/ware/list_create/?p=1&limit=100',
    'locations': '/core/api/warehouse/v1/location/list_create/?p=1&limit=100',
    'clients': '/core/api/visit/ClientListCreate/?p=1&limit=100',
    'user_clients': '/core/api/visit/UserClientListCreate/?p=1&limit=100',
    'buildings': '/core/api/visit/BuildingListCreate/?p=1&limit=100',
    'elevators': '/core/api/visit/ElevatorListCreate/?p=1&limit=100',
    'building_elevators': '/core/api/visit/BuildingElevatorListCreate/?p=1&limit=100',
    'media_types': '/config/MediaType/List/?p=1&limit=100',
    'media': '/config/Media/List/?p=1&limit=100',
}

def fetch(item):
    key, path = item
    try:
        response = requests.get(BASE + path, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return key, {'status': response.status_code, 'path': path}
        data = response.json()
        count = data.get('count') if isinstance(data, dict) else len(data)
        return key, {'status': 200, 'path': path, 'count': count, 'data': data}
    except requests.RequestException as exc:
        return key, {'status': 0, 'path': path, 'error': type(exc).__name__}

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    snapshot = dict(pool.map(fetch, ENDPOINTS.items()))
def scrub(value):
    if isinstance(value, dict):
        return {key: scrub(item) for key, item in value.items() if key not in {'password', 'access', 'refresh', 'groups', 'user_permissions', 'is_superuser', 'is_staff'}}
    if isinstance(value, list):
        return [scrub(item) for item in value]
    return value

args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(scrub(snapshot), ensure_ascii=False), encoding='utf-8')
for key, result in snapshot.items():
    rows = result.get('data', [])
    if isinstance(rows, dict): rows = rows.get('results', [rows])
    print(key, 'HTTP', result['status'], 'sample', len(rows), 'total', result.get('count'))
