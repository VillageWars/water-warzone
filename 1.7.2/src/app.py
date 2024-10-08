import sys
import asyncio
import json
import secrets
import threading
import os
import signal
import requests
import websockets
import logging as log

log.basicConfig(level=log.INFO, format='%(asctime)s - %(message)s')

sys.path.append('../../')
from net2web import Server as ParentServer, Channel as ParentChannel

class Channel(ParentChannel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.special_event = False
        self.username = 'Anonymous'

    def Network_special(self, data):
        if not self.special_event:
            print('Received a special event!')
        self.special_event = True

    def Network_init(self, data):
        self.username = data.get('username', 'Anonymous')
        log.info('Username set to ' + self.username)

    def Network_debug_text(self, data):
        print(data['text'])
        self.Send({'action':'confirm', 'message':'Debug confirm. Text received.'}, force=True)
    
class Server(ParentServer):
    def __init__(self, *args, **kwargs):
        self.ChannelClass = Channel
        super().__init__(*args, **kwargs)

    def update(self):
        self.pump()

    def connection(self, channel):
        log.info('Channel %s connected' % channel.username)

    def disconnection(self, channel):
        log.info('Channel %s disconnected' % channel.username)

    


name = 'Water Warzone'
host = 'water-warzone-0fc31e47a670.herokuapp.com'
GAMEMODE = 'Classic'
#res = requests.get('https://villagewars.pythonanywhere.com/setserver/' + name + '/' + host + '/' + GAMEMODE)
#res.raise_for_status()
server = Server(host)
while True:
    server.update()
