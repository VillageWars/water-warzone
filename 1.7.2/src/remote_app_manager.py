import requests
import logging as log
import threading
import time
import json

REMOTE_DOMAIN = 'villagewars.pythonanywhere.com'

class Context:
    def __init__(self, timeout=3):
        self.session = requests.Session()
        self.timeout = timeout
        self.internet_connection = False
        self.test_internet_connection()
        self.thread = None

    def test_internet_connection(self):
        self.internet_connection = True
        log.debug('Testing Internet connection')
        try:
            self.session.head(f'https://{REMOTE_DOMAIN}/test_connection', timeout=self.timeout)
        except requests.exceptions.ConnectionError:
            self.internet_connection = False

    def _request(self, request_type, *args, **kwargs):
        if not self.internet_connection:
            return {}
        try:
            response = getattr(self.session, request_type)(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            self.enabled = internet_connection
            return {}
        try:
            response.raise_for_status()
        except Exception as exc:
            log.error(f'{request_type.upper()} request to {args[0]} failed: {exc}')
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            return {}

    def get(self, *args, **kwargs):
        return self._request('get', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._request('post', *args, **kwargs)

    def broadcast_server(self, name='VillageWars Server', ip='127.0.0.1', gamemode='Classic'):
        log.info('Broadcasting server IP')
        self.get(f'https://{REMOTE_DOMAIN}/setserver/{name}/{ip}/{gamemode}')
        if not self.internet_connection:
            return False
        def confirm_server_loop():
            while True:
                time.sleep(100)  # 1 minute, 40 seconds
                self.get(f'https://{REMOTE_DOMAIN}/confirm_server/{name}')
        self.thread = threading.Thread(target=confirm_server_loop)
        self.thread.start()
        return True

    def startgame(self, name='VillageWars Server'):
        return self.get(f'https://{REMOTE_DOMAIN}/startgame/{name}')

    def endgame(self, name='VillageWars Server', winner_name=None, losers=None, statistics=None):
        payload = {
            'servername': name,
            'winner': winner_name,
            'losers': losers,
            'statistics': json.dumps(statistics)
        }
        return self.post(f'https://{REMOTE_DOMAIN}/end', data=payload)

    def scan_for_servers(self):
        return self.get(f'https://{REMOTE_DOMAIN}/scan_for_servers').get('servers', [])

    def need_version_info(self, version=None):
        return self.get(f'https://{REMOTE_DOMAIN}/need_version_info/{version}').get('need')

    def update_user(self, username=None, color=None, skin=None):
        payload = {
            'username': username,
            'color': json.dumps(color),
            'skin': skin
        }
        return self.post(f'https://{REMOTE_DOMAIN}/updateUser', data=payload)

    def get_user(self, username=None, password=None):
        return self.get(f'https://{REMOTE_DOMAIN}/get_user/{username}/{password}')
    def create_account(self, username=None, password=None, name=None, email=None):
        payload = {
            'username': username,
            'password': password,
            'name': name,
            'email': email
        }
        return self.post(f'https://{REMOTE_DOMAIN}/create', data=payload)

    def all_users(self):
        return eval(self.get(f'https://{REMOTE_DOMAIN}/all_users')['users'])

    def stream_version_info(self):
        res = self.session.get(f'https://{REMOTE_DOMAIN}/download_version_info', stream=True)
        res.raise_for_status()
        return int(res.headers.get('Content-length', 2048)), res.iter_content

    def stream_version_download(self):
        res = self.session.get(f'https://{REMOTE_DOMAIN}/download_active_version', stream=True)
        res.raise_for_status()
        return int(res.headers.get('Content-length', 2048)), res.iter_content
        
