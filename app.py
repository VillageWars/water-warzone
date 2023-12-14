import asyncio
import json
import secrets
import threading
import os
import signal
import requests
from Translate import Server as ParentServer

import websockets


import logging

logging.basicConfig(format="%(message)s", level=logging.DEBUG)


class Server(ParentServer):
    def __init__(self):
        super().__init__()
        self.connected = False

    def Network_connected(self, data):
        print('Connection!')
        self.connected = True

    def update(self):
        self.pump()


if __name__ == "__main__":
    name = 'Water Warzone'
    host = 'water-warzone-0fc31e47a670.herokuapp.com'
    GAMEMODE = 'Classic'
    res = requests.get('https://villagewars.pythonanywhere.com/setserver/' + name + '/' + host + '/' + GAMEMODE)
    res.raise_for_status()
    server = Server()
    while True:
        server.update()
