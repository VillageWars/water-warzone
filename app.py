# Values
PORT = 5555  # Overwritten in WaterWarzone
__version__ = '1.7.2'

# Python Standard Library Modules Import

import logging as logging
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

ONLINE = 'Procfile' in os.listdir()
sys.path.append(os.path.abspath('./' + __version__ + '/src'))
import configuration as conf
PATH = conf.PATH

# Third-Party Imports

import requests

# Personal Module Imports

import GameServer
from net2web import getmyip

def send_confirmation():  # Tell villagewars.pythonanywhere.com that the server is still running
    try:
        res = requests.get(remote_application + 'confirm_server/' + name)
        res.raise_for_status()
        log.debug('Confirming server broadcast')
    except:
        conf.INTERNET = False

log.debug('Identifying local IP (host)')
if not conf.INTERNET:
    log.warning('No Internet connection')
    try:
        ip = getmyip()
    except:
        ip = '127.0.0.1'
elif ONLINE:
    ip = 'water-warzone-0fc31e47a670.herokuapp.com'  # DYNO means Heroku; Heroku means WaterWarzone
    port = None
else:
    ip = getmyip()

log.debug('Identifying connection port')
port = PORT

__version__ = conf.VERSION
log.info('VillageWars Server ' + __version__)

log.debug('Identifying gamemode')
# Set the gamemode to one of these: 'Classic' or 'Express' or 'Extended' or 'OP' or 'Mutated' or 'Immediate'
if port:
    GAMEMODE = input('Gamemode = ') or 'Classic'
else:
    GAMEMODE = 'Classic'
log.info('Gamemode set to', GAMEMODE)
GameServer.eval_gamemode(GAMEMODE)  # Figure out how many minutes for the Walls
log.debug('Identifying server name')
if port:
    hostname = socket.gethostname()
    name = input('Please input the server\'s name (leave blank for "%s") : ' % hostname) or hostname
else:
    name = 'WaterWarzone'

log.debug('Launching server')
if port:
    server = GameServer.Server(__version__, host=ip, port=port)
else:
    server = GameServer.Server(__version__, host=ip)
remote_application = 'https://villagewars.pythonanywhere.com/'

if conf.INTERNET:
    log.debug('Broadcasting server IP')
    res = requests.get(remote_application + 'setserver/' + name + '/' + ip + '/' + GAMEMODE)
    res.raise_for_status()

log.setLevel(logging.INFO)  # Get rid of debug

log.info(('Server "%s" launched with ip ' % name) + ip)

STARTTIME = time.monotonic()
while not server.tired:
    server.Update()
    if conf.INTERNET and time.monotonic() - STARTTIME > 100:  # Send Confirmation that the server is running (1 minute, 40 seconds)
        thread = threading.Thread(target=send_confirmation)
        thread.start()
        STARTTIME = time.monotonic()
