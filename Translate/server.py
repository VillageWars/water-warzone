import websockets
import asyncio
import json
import secrets
import os
import signal
import threading

import logging as log


class BaseChannel:
    def __init__(self, host=None, port=None):
        self.websocket = None
        self.messages = []
        self.to_send = []
        

    async def send(self, data):
        """
        Send a message.

        """
        await self.websocket.send(json.dumps(data))

    async def send_messages(self):
        compilation = {'messages':[]}
        for message in self.to_send:
            compilation['messages'].append(message)
        self.to_send = []
        await self.send(compilation)
        if len(compilation['messages']) > 0:
            log.debug('Sent %s messages' % len(compilation))
            return
        

    async def handler(self, websocket):
        """
        Handle a connection and dispatch it according to who is connecting.

        """
        self.websocket = websocket
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
            self.messages.append({'action':'disconnected'})
            return

    
        
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
        self.messages = []
        self.async_server.messages = self.messages
        self.connection = False


        
    def pump(self):
        num = 0  # There's a small chance we will receive a new message during the pump
        while len(self.messages):
            message = self.messages.pop(0)
            num += 1
            if hasattr(self, 'Network_' + message['action']):
                getattr(self, 'Network_' + message['action'])(message)  # Calls the `Network_<action>` function to handle an action. `message` will hold the data.
            else:
                log.warning('No Network_' + message['action'] + ' found.')
        if num > 0:
            log.debug('Pumped %s messages successfully' % num)
            return
    def error(self, message):
        self.async_server.error(message)

    def send(self, data):
        if self.connection:
            self.async_server.to_send.append(data)
        else:
            log.error('Not yet connected, failed to send', data['action'])

    def Network_error(self, data):
        log.error('Error:', data['message'])

    def Network_confirm(self, data):
        pass  # Confirmation message
        
    def Network_connection(self, data):
        self.connection = True
        self.send({'action':'connected'})
        self.server.connection(self)
        
    def Network_disconnected(self, data):
        self.connection = False
        self.server.players.remove(self)
        self.server.disconnection(self)

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
            self.port = os.environ.get("PORT", "8001")
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
        new_channel = self.server.ChannelClass(self.server)
        self.channels.append(new_channel)
        await new_channel.async_server.handler(websocket)


    

class Server():
    def __init__(self):
        self.async_server = BaseServer(self)
        self.thread = threading.Thread(target=self.async_server.start)
        self.thread.start()
        self.players = self.async_server.channels

    def pump(self):
        for player in self.players:
            player.pump()

    def connection(self, channel):
        log.info('Channel connected!')

    def disconnection(self, channel):
        log.info('Channel disconnected')
