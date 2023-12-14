import asyncio
import json
import secrets
import threading
import os
import signal

import websockets


import logging

logging.basicConfig(format="%(message)s", level=logging.DEBUG)


async def error(websocket, message):
    """
    Send an error message.

    """
    event = {
        "type": "error",
        "message": message,
    }
    await websocket.send(json.dumps(event))

async def action(websocket, data):
    """
    Send an action.

    """
    event = {
        "type": "action",
        "action": data['action'],
        'data':json.dumps(data)
    }
    await websocket.send(json.dumps(event))

async def do_action(websocket, action, data):
    """
    Does an action.

    """
    print('Doing action', )
    event = {
        "type": "confirm",
    }
    await websocket.send(json.dumps(event))


async def handler(websocket):
    """
    Handle a connection and dispatch it according to who is connecting.

    """
    while True:
        # Receive and parse the "init" event from the UI.
        message = await websocket.recv()
        try:
            event = json.loads(message)
            if 'type' not in event:
                await error(websocket, 'No `type` provided.')
                

            else:
                print()
                print('INCOMING MESSAGE\n')
                print('Type:', event['type'])
                print('Data:\n', event)
                print()
                if event['type'] == 'action':
                    print('ACTION!', event['action'])
                    await do_action(websocket, event['action'], event['data'])
                elif event['type'] == 'wait':
                    print('Received ping from client')
                elif event['type'] =='connected':
                    event = {
                        "type": "confirm",
                        }
                    await websocket.send(json.dumps(event))
                else:
                    event = {
                        "type": "misunderstanding",
                    }
                    await websocket.send(json.dumps(event))
        except json.JSONDecodeError:
            exc = 'Failed to parse.'
            await error(websocket, 'Invalid JSON: ' + exc)
            
        

        

async def main():
    # Set the stop condition when receiving SIGTERM.
    loop = asyncio.get_running_loop()
    #stop = loop.create_future()
    #loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    port = int(os.environ.get("PORT", "8001"))
    async with websockets.serve(handler, "", port):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
