import websockets
import asyncio
import json
import secrets
import os
import signal
import threading


class BaseServer:
    def __init__(self, host=None, port=None):
        if host:
            self.host = host
        else:
            self.host = 'water-warzone-0fc31e47a670.herokuapp.com',
        if port:
            self.port = port
        else:
            self.port = os.environ.get("PORT", "8001")
        self.websocket = None
        self.messages = []
        
    def start(self):
        asyncio.run(self.main())

    async def handler(self, websocket):
        """
        Handle a connection and dispatch it according to who is connecting.

        """
        self.websocket = websocket
        while True:
            message = await websocket.recv()
            try:
                event = json.loads(message)
                self.messages.append(event)
                await self.response('Received message.')
            except json.JSONDecodeError:
                exc = 'Failed to parse.'
                await self.error('Invalid JSON: ' + exc)

    async def main(self):

        # Set the stop condition when receiving SIGTERM.
        loop = asyncio.get_running_loop()
        stop = loop.create_future()
        #loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

        async with websockets.serve(self.handler, "", self.port):
            await stop
        
    async def error(self, message):
        """
        Send an error message.

        """
        event = {
            "action": "error",
            "message": message,
        }
        await self.websocket.send(json.dumps(event))
        
    async def response(self, message):
        """
        Send an error message.

        """
        event = {
            "action": "confirm",
            "message": message,
        }
        await self.websocket.send(json.dumps(event))

class Server:
    def __init__(self, host=None, port=None):
        self.async_server = BaseServer(host=host, port=port)
        self.messages = []
        self.async_server.messages = self.messages
        self.thread = threading.Thread(target=self.async_server.start)
        self.thread.start()
    def pump(self):
        num = 0  # There's a small chance we will receive a new message during the pump
        while len(self.messages):
            message = self.messages.pop(0)
            num += 1
            if hasattr(self, 'Network_' + message['action']):
                getattr(self, 'Network_' + message['action'])(message)  # Calls the Network function to handle an action. `message` will hold the data.
            else:
                print('Warning: No Network_' + message['action'] + ' found.')
        if num > 0:
            print('Pumped %s messages successfully' % num)
    def error(self, message):
        self.thread = threading.Thread(target=asyncio.run, args=[self.async_server.error(message)])
        self.thread.start()

    def Network_error(self, data):
        print('Error:', data['message'])
