import websockets
import asyncio
import json
import secrets
import os
import signal
import threading
import sys

import logging as log


class BaseClient:
    def __init__(self, host=None, port=None):
        if host:
            self.host = host
        else:
            self.host = 'water-warzone-0fc31e47a670.herokuapp.com',
        if port:
            self.port = port
        else:
            self.port = 8001
        self.websocket = None
        self.messages = []
        self.to_send = []

        
    def start(self):
        asyncio.run(self.main())

    async def send_messages(self):
        messages_to_send = self.to_send[:]
        self.to_send = []
        compilation = {'messages':[]}
        for message in messages_to_send:
            compilation['messages'].append(message)
        self.to_send = []
        await self.send(compilation)
        if len(compilation['messages']) > 0:
            #print('Sent %s messages' % len(compilation))
            return
        

    async def send(self, data):
        """
        Send a message.

        """
        await self.websocket.send(json.dumps(data))



    async def main(self):
        if 'localhost' in self.host:
            URI = 'ws://' + self.host + ':' + str(self.port)
        else:
            URI = 'wss://' + self.host
        log.info('Connecting...')
        async with websockets.connect(URI) as websocket:
            self.websocket = websocket
            self.to_send.append({'action':'connection'})
            await self.send_messages()
            log.debug('Sent initial message')
            try:
                while True:
                    message = await websocket.recv()
                    try:
                        messages = json.loads(message)
                        for event in messages['messages']:
                            self.messages.append(event)
                        await self.send_messages()
                    except json.JSONDecodeError as exc:
                        await self.error('Invalid JSON: ' + exc)
            except (websockets.exceptions.ConnectionClosedError, websockets.ConnectionClosedOK):
                log.error('Connection Closed from server-side')

        
    async def error(self, message):
        """
        Send an error message.

        """
        event = {
            "action": "error",
            "message": message,
        }
        self.to_send.append(json.dumps(event))
        
    async def response(self, message):
        """
        Send an error message.

        """
        event = {
            "action": "confirm",
            "message": message,
        }
        self.to_send.append(json.dumps(event))

class Client:
    def __init__(self, host=None, port=None):
        self.async_client = BaseClient(host=host, port=port)
        self.messages = []
        self.async_client.messages = self.messages
        self.thread = threading.Thread(target=self.async_client.start)
        self.thread.start()
        self.connected = False
        
    def pump(self):
        num = 0  # There's a small chance we will receive a new message during the pump
        while len(self.messages):
            message = self.messages.pop(0)
            num += 1
            if hasattr(self, 'Network_' + message['action']):
                getattr(self, 'Network_' + message['action'])(message)  # Calls the Network function to handle an action. `message` will hold the data.
            else:
                log.warning('No Network_' + message['action'] + ' found.')
        if num > 0:
            #print('Pumped %s messages successfully' % num)
            return
            
    def error(self, message):
        self.async_client.error(message)
        
    def send(self, data):
        if self.connected:
            self.async_client.to_send.append(data)
        

    def Network_error(self, data):
        log.error('Error:', data['message'])

    def Network_confirm(self, data):
        pass  # Confirmation message
        
    def Network_connected(self, data):
        log.info('Connected!')
        self.connected = True
