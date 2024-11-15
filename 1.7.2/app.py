PORT = 5555  # Overwritten in WaterWarzone
GAMEMODE = 'Classic'  # Can be modified in the lobby
SERVER_NAME = None  # Defaults to the device's name

# Python Standard Library Modules Import

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')  # Set up logging
log = logging.getLogger()
log.debug('Loading environment')
import socket
import os
import json
import sys
import time
import threading

# Configuration

sys.path.append(os.path.abspath('./src'))
import configuration as conf
PATH = conf.PATH
__version__ = conf.VERSION

# Personal Module Imports

import GameServer
from net2web import getmyip

log.info(f'VillageWars Server {__version__}')

log.debug('Identifying host information')
if 'DYNO' in os.environ:  # Online server (WaterWarzone)  
    os.environ['IP'] = 'water-warzone-0fc31e47a670.herokuapp.com'
    os.environ['PORT'] = os.environ.get('PORT', str(PORT))
    server_name = 'WaterWarzone'
else:       
    os.environ['IP'] = getmyip() # LAN server
    os.environ['PORT'] = str(PORT)
    server_name = SERVER_NAME or socket.gethostname()

log.setLevel(logging.INFO)  # Get rid of all the debug messages sent by the websocket connection
GameServer.main(name=server_name, gamemode=GAMEMODE)
