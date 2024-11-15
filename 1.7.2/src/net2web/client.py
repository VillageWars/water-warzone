import websockets
import asyncio
import json
import secrets
import os
import signal
import threading
import sys
import socket
import time
import logging as log

from .toolbox import Clock



class BaseClient:
    def __init__(self, uri=None):
        self.uri = uri or 'ws://127.0.0.1:5000'
        self.websocket = None
        self.messages = []
        self.to_send = []
        self.clock = Clock(30)

        
    def start(self):
        asyncio.run(self.main())

    async def send_messages(self):
        while True:
            try:
                messages_to_send = self.to_send[:]
                if len(messages_to_send) == 0:
                    await asyncio.sleep(self.clock.get_tick())
                    continue
                self.to_send = []
                compilation = {'messages':[]}
                for message in messages_to_send:
                    compilation['messages'].append(message)
                self.to_send = []
                await self.send(compilation)
                
                if len(compilation['messages']) > 0:
                    log.debug('Sent %s messages' % len(compilation))
            except (websockets.exceptions.ConnectionClosedError, websockets.ConnectionClosedOK):
                    break
        

    async def send(self, data):
        """
        Send a message.

        """
        await self.websocket.send(json.dumps(data))


    async def recv(self):
        while True:
            try:
                message = await self.websocket.recv()
                self.messages.extend(json.loads(message)['messages'])
            except (websockets.exceptions.ConnectionClosedError, websockets.ConnectionClosedOK):
                log.error('Connection Closed from server-side')
                self.messages.append({'action':'disconnected'})
                break

    async def main(self):
        print('URI:', self.uri)
        log.info('Connecting to ' + self.uri + '...')
        async with websockets.connect(self.uri) as websocket:
            self.websocket = websocket
            self.to_send.append({'action':'connection'})
            log.debug('Sending initial message')
            task1 = asyncio.create_task(self.recv())
            task2 = asyncio.create_task(self.send_messages())

            # Wait for tasks to complete
            await asyncio.gather(task1, task2)


class Client:
    def __init__(self, uri=None):
        self.async_client = BaseClient(uri=uri)
        self.async_client.thread = threading.Thread(target=self.async_client.start)
        self.async_client.thread.setDaemon(True)
        self.async_client.thread.start()
        self._connected = False
        
    @property
    def connected(self):
        return self._connected
        
    def pump(self):
        num = 0  # There's a small chance we will receive a new message during the pump
        while len(self.async_client.messages):
            message = self.async_client.messages.pop(0)
            num += 1
            if message['action'] == 'connected':
                self._connected = True
            if message['action'] == 'disconnected':
                self.Network_disconnected(message)
                log.info('Disconnection.')
                sys.exit()
            if hasattr(self, 'Network_' + message['action']):
                getattr(self, 'Network_' + message['action'])(message)  # Calls the Network function to handle an action. `message` will hold the data.
                log.debug(f'Calling Network_{message["action"]}({repr(message)})')
            else:
                log.warning('No Network_' + message['action'] + ' found.')
        if num > 0:
            log.debug('Pumped %s messages successfully' % num)
            return
    Pump = pump  # Compatibility with PodSixNet
    
    def error(self, message):
        self.async_client.error(message)
        
    def send(self, data, force=False):
        if self.connected or force:
            self.async_client.to_send.append(data)
        else:
            log.debug('Not yet connected, failed to send action "' + data['action'] + '"')
            
    Send = send  # Compatible with PodSixNet
        
    def Network_error(self, data):
        log.error('Error:', data['message'])
        
    def Network_connected(self, data):
        log.info('Connected!')
    def Network_disconnected(self, data):
        pass
        
