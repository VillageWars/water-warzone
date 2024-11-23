import websockets
import asyncio
import json
import secrets
import os
import signal
import threading
import secrets
import time
import copy

import logging as log

from .toolbox import Clock


class BaseChannel:
    '''
    Base class for handling WebSocket communication.

    Attributes:
        websocket: The WebSocket connection.
        messages: List of received messages.
        to_send: List of messages to be sent.
        id: Unique identifier for the channel.
        clock: Clock object to manage timing.
    '''
    def __init__(self):
        self.websocket = None
        self.messages = []
        self.to_send = []
        self.id = secrets.token_hex()
        self.clock = Clock(30)

    async def send(self, data):
        '''
        Send data through the WebSocket connection.
        '''
        await self.websocket.send(json.dumps(data))

    async def send_messages(self):
        '''
        Continuously send messages from the to_send list.
        '''
        while True:
            try:
                messages_to_send = copy.copy(self.to_send)
                self.to_send.clear()
                if len(messages_to_send) == 0:
                    await asyncio.sleep(self.clock.get_tick())
                    continue
                data = {'messages':[]}
                for message in messages_to_send:
                    data['messages'].append(message)
                await self.send(data)
                
                if len(data['messages']) > 0:
                    log.debug('Sent %s messages' % len(data))
            except (websockets.exceptions.ConnectionClosedError, websockets.ConnectionClosedOK):
                    break
        
    async def recv(self):
        '''
        Continuously receive messages and append them to the messages list.
        '''
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
        '''
        Handle a connection and manage sending and receiving messages.
        '''
        self.websocket = websocket
        task1 = asyncio.create_task(self.recv())
        task2 = asyncio.create_task(self.send_messages())
        await asyncio.gather(task1, task2)

class Channel:
    '''
    Channel class for managing communication with a server.

    Attributes:
        server: The server to which the channel is connected.
        async_server: Instance of BaseChannel for asynchronous operations.
        connected: Boolean indicating if the channel is connected.
    '''
    def __init__(self, server):
        self.server = server
        self.async_server = BaseChannel()
        self._connected = False
        
    @property
    def connected(self):
        return self._connected
        
    def pump(self):
        '''
        Process all pending messages.
        '''
        num = 0  # There's a small chance we will receive a new message during the pump
        while self.async_server.messages:
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

    def send(self, data, force=False):
        '''
        Send a message through the channel.

        Args:
            data (dict): The message data to be sent.
            force (bool): Force sending the message even if not connected.
        '''
        if self.connected or force:
            self.async_server.to_send.append(data)
        else:
            log.debug('Not yet connected, failed to send action "' + data['action'] + '"')

    Send = send  # Compatibility with PodSixNet

    def Network_connection(self, data):
        pass
        
    def Network_disconnected(self, data):
        pass

    def __hash__(self):
        return hash(self.async_server.id)

class BaseServer:
    '''
    Base class for a WebSocket server.

    Attributes:
        server: The server object.
        channels: List of connected channels.
        port: The port to listen on.
    '''
    def __init__(self, server, port=None):
        self.server = server
        self.channels = []
        self.port = port

    def start(self):
        '''
        Start the server.
        '''
        asyncio.run(self.main())

    async def main(self):
        await websockets.serve(self.handler, "", self.port)
        try:
            await asyncio.Future()
        except asyncio.CancelledError as exc:
            logging.error('Server stopped.')
            server.close()
            await server.wait_closed()
            
    async def handler(self, websocket):
        """
        Handle a connection and dispatch it according to who is connecting.
        """
        try:
            new_channel = self.server.ChannelClass(self.server)
            self.channels.append(new_channel)
            await new_channel.async_server.handler(websocket)
        except websockets.exceptions.InvalidHandshake as e:
            error_message = f'Failed to open a WebSocket connection: {e}'
            await websocket.send(error_message)

class Server():
    '''
    Main server class for managing channels and player connections.

    Attributes:
        async_server: Instance of BaseServer for asynchronous operations.
    '''
    def __init__(self, port=5555):
        self.async_server = BaseServer(self, port=port)
        self.async_server.thread = threading.Thread(target=self.async_server.start)
        self.async_server.thread.setDaemon(True)
        self.async_server.thread.start()
        if not hasattr(self, 'ChannelClass'):
            self.ChannelClass = Channel
        
    @property
    def players(self):
        return self.async_server.channels

    def pump(self):
        '''
        Process messages for all players.
        '''
        for player in self.players:
            player.pump()
            
    Pump = pump  # Compatibility with PodSixNet

    def connection(self, channel):
        '''
        Handle a new channel connection.
        '''
        log.info('Channel connected!')

    def disconnection(self, channel):
        '''
        Handle a channel disconnection.
        '''
        log.info('Channel disconnected')
