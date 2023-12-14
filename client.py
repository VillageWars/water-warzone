import asyncio
import websockets
import json
import sys

# To test, run python -m websockets wss://websockets-test-001-91c83418594c.herokuapp.com/

#URI = 'wss://websockets-test-001-91c83418594c.herokuapp.com/'
URI = 'ws://localhost:8001'

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
        message = {'type':'connected'}

        event = json.dumps(message)
        await websocket.send(event)
        event = get_event(websocket)
        if event['type'] == 'confirm':
            print('Successful Back and forth connection!')
        else:
            sys.exit('Server Didn\'t confirm')
        while True:
            event = json.dumps({'type':'wait'})
            await websocket.send(event)
            event = get_event(websocket)
            print()
            print('INCOMING MESSAGE\n')
            print('Type:', event['type'])
            print('Data:\n', event)
            print()


asyncio.get_event_loop().run_until_complete(connect())
