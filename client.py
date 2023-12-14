import asyncio
import websockets
import json
import sys
import random

# To test, run python -m websockets wss://websockets-test-001-91c83418594c.herokuapp.com/

#URI = 'wss://water-warzone-0fc31e47a670.herokuapp.com/'
URI = 'ws://localhost:8001'

ACTIONS = ['bruh', 'bill', 'duck', 'kitten', 'caden']
DATA = {"coords":(234, 3238)}

async def get_event(websocket):
    try:
        message = await websocket.recv()
        event = json.loads(message)
        return event
    except websockets.ConnectionClosedOK:
        print('Connection closed')
        sys.exit()

async def connect():
    print('Connecting...')
    async with websockets.connect(URI) as websocket:
        print('Connected!')
        message = {'action':'connected'}

        event = json.dumps(message)
        await websocket.send(event)
        event = await get_event(websocket)
        print(event)
        while True:
            action = random.choice(ACTIONS)
            event = DATA
            event['action'] = action
            event = json.dumps(event)
            input('Press enter to send ' + event)
            await websocket.send(event)
            event = await get_event(websocket)
            print()
            print('INCOMING MESSAGE\n')
            print('Action:', event['action'])
            print('Data:\n', event)
            print()


asyncio.get_event_loop().run_until_complete(connect())
