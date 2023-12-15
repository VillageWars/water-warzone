import asyncio
import websockets
import json
import sys
import random
from Translate import Client as ParentClient, getmyip
import pygame

import logging as log

log.basicConfig(level=log.INFO, format='%(message)s')

# To test, run python -m websockets wss://websockets-test-001-91c83418594c.herokuapp.com/

#host = 'water-warzone-0fc31e47a670.herokuapp.com/'
host = 'localhost'
port = 8001

username = input('Entor your username: ')

ACTIONS = ['bruh', 'bill', 'duck', 'kitten', 'caden']
DATA = {"coords":(234, 3238)}

class Client(ParentClient):
    def __init__(self, host, port, username=None):
        super().__init__(host=host, port=port)
        self.clock = pygame.time.Clock()
        if username:
            self.username = username
        else:
            self.username = getmyip(local=False)
        

    def Network_connected(self, data):
        log.info('Connected!')
        self.connected = True
        self.send({'action':'init', 'username':self.username})

    def update(self):
        
        self.pump()
        self.send({'action':'special'})
        self.clock.tick(30)

client = Client(host, port, username)
while True:
    client.update()
