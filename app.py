import asyncio
import json
import secrets
import threading
import os
import signal
import requests
from Translate import Server as ParentServer, Channel as ParentChannel

import websockets


import logging as log

log.basicConfig(level=log.INFO, format='%(asctime)s - %(message)s')

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
    
class Server(ParentServer):
    def __init__(self):
        self.ChannelClass = Channel
        super().__init__()

    def update(self):
        self.pump()

    def connection(self, channel):
        log.info('Channel %s connected' % channel.username)

    def disconnection(self, channel):
        log.info('Channel %s disconnected' % channel.username)

    

if __name__ == "__main__":
    name = 'Water Warzone'
    host = 'water-warzone-0fc31e47a670.herokuapp.com'
    GAMEMODE = 'Classic'
    res = requests.get('https://villagewars.pythonanywhere.com/setserver/' + name + '/' + host + '/' + GAMEMODE)
    res.raise_for_status()
    server = Server()
    while True:
        server.update()
