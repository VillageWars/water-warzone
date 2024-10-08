import websockets
import asyncio
import json
import secrets
import os
import signal
import threading
import secrets
import time

import logging as log

from .toolbox import Clock


class BaseChannel:
    def __init__(self, host=None, port=None):
        self.websocket = None
        self.messages = []
        self.to_send = []
        self.id = secrets.token_hex()
        self.clock = Clock(30)

    async def send(self, data):
        """
        Send a message.

        """
        await self.websocket.send(json.dumps(data))

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
                await self.send(compilation)
                
                if len(compilation['messages']) > 0:
                    log.debug('Sent %s messages' % len(compilation))
            except (websockets.exceptions.ConnectionClosedError, websockets.ConnectionClosedOK):
                    break
        
    async def recv(self):
        while True:
            try:
                message = await self.websocket.recv()
            
                messages = json.loads(message)
                for event in messages['messages']:
                    self.messages.append(event)
            except (websockets.exceptions.ConnectionClosedError, websockets.ConnectionClosedOK):
                    log.info('Connection Closed from client-side')
                    self.messages.append({'action':'disconnected'})
                    break

    async def handler(self, websocket):
        """
        Handle a connection and dispatch it according to who is connecting.
        """
        self.websocket = websocket
        task1 = asyncio.create_task(self.recv())
        task2 = asyncio.create_task(self.send_messages())

        # Wait for tasks to complete
        await asyncio.gather(task1, task2)

    
        
    def error(self, message):
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
        await self.websocket.send(json.dumps(event))

class Channel:
    def __init__(self, server):
        self.server = server
        self.async_server = BaseChannel()
        self._connected = False
        self._warned = []
        
    @property
    def connected(self):
        return self._connected
        
    def pump(self):
        num = 0  # There's a small chance we will receive a new message during the pump
        while len(self.async_server.messages):
            message = self.async_server.messages.pop(0)
            num += 1
            if message['action'] == 'connection':
                self._connected = True
                self.send({'action':'connected'})
                self.server.connection(self)
            if message['action'] == 'disconnected':
                self._connected = False
                self.server.players.remove(self)
                self.server.disconnection(self)
            if hasattr(self, 'Network_' + message['action']):
                getattr(self, 'Network_' + message['action'])(message)  # Calls the `Network_<action>` function to handle an action. `message` will hold the data.
                log.debug('Calling Network_' + message['action'])
            else:
                log.warning('No Network_' + message['action'] + ' found.')
        if num > 0:
            log.debug('Pumped %s messages successfully' % num)
            return
    def error(self, message):
        self.async_server.error(message)

    def send(self, data, force=False):
        if self.connected or force:
            self.async_server.to_send.append(data)
        else:
            log.debug('Not yet connected, failed to send action "' + data['action'] + '"')

    Send = send  # Compatibility with PodSixNet

    def Network_error(self, data):
        log.error('Error:', data['message'])

    def Network_connection(self, data):
        pass
        
    def Network_disconnected(self, data):
        pass

    def __hash__(self):
        return hash(self.async_client.id)

class BaseServer:
    def __init__(self, server, host=None, port=None):
        self.server = server
        if host:
            self.host = host
        else:
            self.host = 'water-warzone-0fc31e47a670.herokuapp.com',
        if port:
            self.port = port
        else:
            self.port = os.environ.get("PORT", "5555")
        self.channels = []

    def start(self):
        asyncio.run(self.main())

    async def main(self):

        # Set the stop condition when receiving SIGTERM.
        loop = asyncio.get_running_loop()
        stop = loop.create_future()
        try:
            loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
        except:
            log.warning('No SIGTERM')

        async with websockets.serve(self.handler, "", self.port):
            await stop
            
    async def handler(self, websocket):
        """
        Handle a connection and dispatch it according to who is connecting.
        """
        try:
            new_channel = self.server.ChannelClass(self.server)
            self.channels.append(new_channel)
            await new_channel.async_server.handler(websocket)
        except websockets.exceptions.InvalidHandshake as e:
            error_message = "Failed to open a WebSocket connection: invalid Connection header: close."
            # Customize the error message or perform any other desired actions
            # ...
            # Send the error message back to the client if needed
            await websocket.send(error_message)


    

class Server():
    def __init__(self, host=None, port=None):
        self.async_server = BaseServer(self, host=host, port=port)
        self.async_server.thread = threading.Thread(target=self.async_server.start)
        self.async_server.thread.setDaemon(True)
        self.async_server.thread.start()
        if not hasattr(self, 'ChannelClass'):
            self.ChannelClass = Channel
        
    @property
    def players(self):
        return self.async_server.channels

    def pump(self):
        
        for player in self.players:
            player.pump()
            
    Pump = pump  # Compatibility with PodSixNet

    def connection(self, channel):
        log.info('Channel connected!')

    def disconnection(self, channel):
        log.info('Channel disconnected')
