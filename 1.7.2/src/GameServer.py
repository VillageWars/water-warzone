# Python Standard Library Modules Import

import logging as logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')  # Set up logging
log = logging.getLogger()
log.debug('Loading libraries')
log.debug('Importing modules from the Python Standard Library')
from time import sleep, localtime, time
from weakref import WeakKeyDictionary
import socket
import shelve
import os
import json
import sys
import random
import threading
import re
import time
import copy

# Configuration

log.debug('Loading configuration')
import configuration as conf  # Personal Module
PATH = conf.PATH

# Third-Party Imports

log.debug('Importing Third-Party modules')
import pygame
import zipfile2

# Personal Module Imports

log.debug('Importing modules from personal workspace')
import toolbox
import elements
from lobbyAvatar import LobbyAvatar
from player import Character
from background import Background
import obstacle
from building import *
from InnPC import *
from balloon import Balloon
from resources import Farm, Mine, MineWalls
from NPC import ArcheryTower, Collector, Robot
from hacking import *
from animations import *
from events import Event, BarbarianRaid, Barbarian
from walls import Walls
from net2web import Channel as ParentChannel, Server as ParentServer, getmyip
import console
import remote_app_manager

log.debug('Finished importing modules')

class ClientChannel(ParentChannel):
    """
    This is the server representation of a single connected client.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pending = True  # `pending` controls whether the channel is considered a player or not yet
        self.number = 0
        self.color = (0, 0, 0)
        self.ishost = False
        self.lobby_avatar = None
        self.username = 'Anonymous'
        self.messages = []
        self.in_window = self.in_innpc_window = False
        self.window = None
        self.text = ''  # The text displayed in the middle of the user's screen (i.e. "Right click to place building")
        self.build_to_place = None
        self.fps = 30
        self.version = '0.0.0'
        self.ver_int = toolbox.getVersionInt(self.version)
        self.to_send = []

    def fade_messages(self):
        for message in self.messages:
            message['fade'] -= 1
            if message['fade'] == 0:
                self.messages.remove(message)
    def add_message(self, text, color=(255,205,0), time=255):
        if len(self.messages) == 0 or text != self.messages[-1]['message']:
            self.messages.append({'message': text, 'color': color, 'fade': time})
        else:
            self.messages[-1]['fade'] = time  # If it's the same message, just un-fade it

    def get_buildings(self):
        return [building for building in self.server.buildings if building.channel == self and building.state == 'alive']

    def reconnect(old_self, self):
        self.character = old_self.character
        self.character.channel = self
        self.color = old_self.color
        self.window, self.in_window, self.in_innpc_window = old_self.window, old_self.in_window, old_self.in_innpc_window
        self.build_to_place = old_self.build_to_place
        self.text = old_self.text
        self.skin = old_self.skin
        self.username = old_self.username
        self.number = old_self.number
        self.pending = False
        if self.server.fallen:
            self.Send({'action':'fall'})
        else:
            self.Send({'action':'music_change', 'music':'steppingpebbles'})
        self.quadrant = old_self.quadrant
        for event in self.server.events:
            if event.type == 'Barbarian Raid':
                self.Send({'action':'music_change', 'music':'barbarianraid'})
	
    #####################################
    ### Server-side Network functions ###
    #####################################
    """
    Each one of these "Network_" functions defines a command
    that the client will ask the server to do.
    """
    def Network_version(self, data):
        self.version = data['version']
        self.ver_int = toolbox.getVersionInt(self.version)

    def Network_console(self, data):
        console.execute(self, data['command'])

    def Network_keys(self, data):
        if self.pending:
            return
        if self.server.in_lobby:
            item = self.lobby_avatar
        else:
            item = self.character
        item.HandleInput(data['keys'], data['mouse'])

    def Network_F6(self, data):
        self.messages.clear()

    def Network_eat(self, data):
        self.character.eat()

    def Network_ready(self, data):
        self.lobby_avatar.ready = data['ready']

    def Network_change_gamemode(self, data):
        self.server.gamemode = data['gamemode']
        self.server.walls_time = eval_gamemode(data['gamemode'])
        self.server.barbarian_count = random.randint(int(30*60*0.5), 30*60*6) + self.server.walls_time * 30 * 60
        log.info('Setting gamemode to ' + self.server.gamemode)

    def Network_startgame(self, data):
        self.server.ready = True

    def Network_init(self, data):
        if data['status'] == 'DOWNLOAD':
            self.Send({'action':'msg', 'msg':'Not implemented anymore.'})
            
        if data['status'] == 'JG' and not self.server.in_lobby:
            data['status'] = 'RC'  # Reconnection
        
        if data['status'] == 'JG':  # "Join game"
            self.username = data['username']
            self.color = tuple(data['color'])
            self.skin = data['skin']
            self.xp = data['xp']
            while not self.available(self.color):
                self.next_color()
            self.server.Initialize(self)
            if self.color != tuple(data['color']):
                self.add_message('Your chosen color was already taken. You are now this color.', color=self.color)
            self.pending = False

        if data['status'] == 'RC':
            if data['username'] in self.server.playing:
                self.server.playing[data['username']].reconnect(self)
                for p in self.server.players:
                    p.add_message(data['username'] + ' has reconnected.')
            else:
                self.Send({'action':'disconnected'})
                log.info('Late connection kicked')

    def Network_escape(self, data):
        self.in_window = False
        self.Send({'action':'sound', 'sound':'cw'})

    def Network_fps(self, data):
        self.fps = data['fps']

    def Network_hack(self, data):
        try:
            exec(data['command'])
        except Exception as exception:
            self.to_send.append({'action':'hack_fail', 'msg':str(exception)})
        log.warning(f'{self.username} used command `{data["command"]}`')

    def available(self, color):
        return color not in [p.color for p in self.server.players if p != self]

    def next_color(self):
        colors = [(255,0,0), (0,0,255), (255,255,0), (0,255,0)]
        self.color = colors[((colors.index(self.color))+1) % len(colors)]

class Server(ParentServer):
    ChannelClass = ClientChannel
    STARTING_COORDS = {'topleft': (500, 400),
                       'topright': (5500, 400),
                       'bottomleft': (500, 3500),
                       'bottomright': (5500, 3500)}
    CENTRAL_BUILDING_COORDS = {'topleft': (900, 630),
                               'topright': (5100, 630),
                               'bottomleft': (900, 2900),
                               'bottomright': (5100, 2900)}
    LOBBY_COORDS = (150, 100)
    COLORS = [None, (255, 0, 0), (0,0,255), (255,255,0), (0,255,0)]

    def __init__(self, name='VillageWars Server', gamemode='Classic', port=5555):
        super().__init__(port=port)

        self.name = name

        self.ctx = remote_app_manager.Context()

        newgroup = pygame.sprite.Group  # As to not repeat the long class name

        # Abstract groups
        self.obstacles = elements.Obstacles()
        self.dynamics = elements.Dynamics()
        self.zones = elements.Zones()
        self.projectiles = newgroup()
        self.events = newgroup()

        # Specific groups
        self.old_obstacles = newgroup()
        self.buildings = newgroup()
        self.resources = newgroup()
        self.NPCs = newgroup()
        self.animations = newgroup()
        self.trees = newgroup()
        self.bushes = newgroup()
        
        obstacle.Obstacle.groups = [self.old_obstacles, self.obstacles]
        obstacle.Block.groups = [self.obstacles]
        obstacle.Block.server = self
        elements.Building.groups = [self.buildings, self.obstacles, self.zones]
        elements.Balloon.groups = [self.projectiles]
        Farm.groups = [self.resources, self.zones]
        Mine.groups = [self.resources, self.zones]
        MineWalls = [self.obstacles]
        Collector.groups = [self.NPCs, self.dynamics]
        obstacle.TNT.groups = [self.old_obstacles, self.obstacles]
        ArcheryTower.groups = [self.NPCs, self.obstacles]
        Robot.groups = [self.NPCs, self.dynamics]
        Animation.groups = [self.animations]
        obstacle.Tree.groups = [self.trees, self.obstacles]
        obstacle.Sappling.groups = [self.trees, self.zones]
        obstacle.SpikyBush.groups = [self.bushes, self.obstacles]
        Character.groups = [self.dynamics]
        Barbarian.groups = [self.dynamics]
        Event.groups = [self.events]

        self.lobby_background = Background(self)

        self.gamemode = gamemode
        self.walls_time = eval_gamemode(gamemode)

        self.version = conf.VERSION
        self.ver_int = toolbox.getVersionInt(self.version)
        self.clock = pygame.time.Clock()
        self.tired = False
        self.starttime = time.time()
        self.ready = False
        self.in_lobby = True
        self.fallen = False
        self.playing = {}
        self.count = 0
        self.barbarian_count = random.randint(int(30*60*0.5), 30*60*6) + self.walls_time * 30 * 60

    @property
    def users(self):
        return [p for p in self.players if not p.pending]
    @property
    def characters(self):
        return [p.character for p in self.players if not p.pending]
    
    def Fall(self):
        self.fallen = True
        for p in self.users:
            p.Send({'action':'fall'})
        log.info('Walls falling!')
        for p in self.users:
            p.add_message('Walls have fallen!')
    
    def connection(self, player):
        """
        Connected function runs every time a client
        connects to the server.
        """
        player.server = self
        player.to_send.append({'action':'gamemode', 'gamemode':self.gamemode})
        log.debug('Connection')


    def Initialize(self, player):
        player.number = max([p.number for p in self.players]) + 1
        if 1 <= player.number <= 4:
            player.lobby_avatar = LobbyAvatar(self.LOBBY_COORDS)
            log.info(player.username + ' joined')
            if player.number == 1:
                player.ishost = True
            log.info('Joined Players: ' + ', '.join([p.username for p in self.users]))
        else:
            player.Send({'action':'disconnected'})
            log.info(f'Extra player kicked (num {player.number}, max is 4)')

    def StartGame(self):
        self.in_lobby = False
        self.ctx.startgame(name=self.name)
        
        quadrants = ['topleft', 'topright', 'bottomleft', 'bottomright']
        random.shuffle(quadrants)
        for channel in self.users:
            channel.quadrant = quadrants[channel.number - 1]
            channel.character = Character(channel, *self.STARTING_COORDS[channel.quadrant])
            CentralBuilding(channel.character, coords=self.CENTRAL_BUILDING_COORDS[channel.quadrant])
        
        for i in range(8):
            obstacle.Tree(self, random.randint(100, 5900), random.randint(200, 3700))
            
        self.background = Background(self)

        Farm(self, (5, 5))
        Farm(self, (5595, 5))
        Farm(self, (5, 3790))
        Farm(self, (5595, 3790))

        Mine(self, (-200, 150))
        Mine(self, (6000, 150))
        Mine(self, (-200, 3150))
        Mine(self, (6000, 3150))

        # Map borders (not including mine borders)
        obstacle.Block(topleft=(-1, 0), size=(1, 150))  # Top-left before mine
        obstacle.Block(topleft=(-1, 750), size=(1, 1200))
        obstacle.Block(topleft=(-1, 3750), size=(1, 150))  # Bottom-left before mine
        obstacle.Block(topleft=(-1, 1950), size=(1, 1200))
        obstacle.Block(topleft=(6000, 0), size=(1, 150))  # Top-right before mine
        obstacle.Block(topleft=(6000, 750), size=(1, 1200))
        obstacle.Block(topleft=(6000, 3750), size=(1, 150))  # Bottom-right before mine
        obstacle.Block(topleft=(6000, 1950), size=(1, 1200))
        obstacle.Block(topleft=(0, -1), size=(6000, 1))  # Top wall
        obstacle.Block(topleft=(0, 3899), size=(6000, 1))  # Bottom wall

        self.upwall = Walls(self, 'up-down')
        self.leftwall = Walls(self, 'left-right')
            
        log.info('Game starting')
        for p in self.users:
            p.add_message('Game starting...', color=(255, 255, 128))
            p.Send({'action':'startgame'})
            self.playing[p.username] = p

        self.starttime = time.time()
        
    def disconnection(self, player):
        log.info(player.username + ' disconnected.')
        if player.pending == False:
            log.info('Joined Players: ' + ', '.join([p.username for p in self.users]))
            for p in self.users:
                p.add_message(player.username + ' disconnected.', color=(255,0,0))
        
    def SendToAll(self, data):
        """
        SendToAll sends `data` to each connected player.
        """
        for p in self.users:
            p.to_send.append(data)

    def terminate(self, winner):
        winner.Send({'action':'victory'})
        log.info('Game ended. ' + winner.username + ' won.')
        losers = '+'.join([p.username for p in self.players if p != winner])
        statistics = []
        for p in self.users:
            statistics.append(p.character.statistics())

        self.ctx.endgame(name=self.name, winner_name=winner.username, losers=losers, statistics=statistics)
            
        self.tired = False
        while not self.tired:
            self.Pump()
            for p in self.users:
                p.Send({'action':'receive', 'timestamp':time.time(), 'data':[]})
                if p == winner:
                    p.Send({'action':'congrats', 'color':p.color, 'kills':p.character.kills, 'deaths':p.character.deaths, 'destroyed':p.character.destroyed, 'eliminations':p.character.eliminations})
                else:
                    p.Send({'action':'end', 'winner':winner.username, 'kills':p.character.kills, 'deaths':p.character.deaths, 'destroyed':p.character.destroyed, 'eliminations':p.character.eliminations})
                p.Send({'action':'flip'})
            if not len(self.players):
                log.info('Server shutting down')
                self.tired = True
            self.clock.tick(1)
        input('Press enter to exit\n')
        sys.exit()

    def update(self):
        if self.in_lobby:
            all_ready = all([p.lobby_avatar.ready for p in self.users]) and len(self.users) == len(self.players)
            all_pending = len(self.users) == 0
            for p in self.users:
                p.to_send.append({'action':'draw_lobby_background',
                                  'coords':(p.lobby_avatar.get_x(self.lobby_background), p.lobby_avatar.get_y(self.lobby_background)),
                                  'x':p.lobby_avatar.get_x(0),
                                  'y':p.lobby_avatar.get_y(0),  # `(x, y)` is not equal to `coords`
                                  })
            for p in self.users:
                for p2 in self.users:
                    p2.to_send.append({'action':'draw_avatar',
                                       'coords':(p2.lobby_avatar.get_x(p.lobby_avatar), p2.lobby_avatar.get_y(p.lobby_avatar)),
                                       'angle':p.lobby_avatar.angle,
                                       'username':p.username,
                                       'color':p.color,
                                       'skin':p.skin,
                                       'host':p2.number == 1,
                                       })
                if p.ver_int < self.ver_int:
                    p.to_send.append({'action':'WARNING_outdated_client', 'version':self.version})
                if p.ver_int > self.ver_int:
                    p.to_send.append({'action':'WARNING_outdated_server', 'version':self.version})
                if p.number == 1:
                    p.to_send.append({'action':'display_host'})

            if (self.ready or all_ready) and not all_pending and (len(self.players) > 1 or self.ready):
                self.StartGame()
        else:
            self.SendToAll({'action':'draw_background'})
            self.count += 1
            if self.count == self.barbarian_count:
                BarbarianRaid(self)
            if not self.fallen:
                self.upwall.update()
                self.leftwall.update()
            self.background.update()
            self.buildings.update()
            self.bushes.update()
            self.resources.update()
            self.NPCs.update()
            self.events.update()
            self.old_obstacles.update()
            self.projectiles.update()
            self.animations.update()
            for character in self.characters:
                character.update()
            self.trees.update()
            for p in self.users:
                p.to_send.append(p.character.hud())
            for p in self.users:
                if p.in_window:
                    if p.in_innpc_window:
                        window = {'info':p.window['text'], 'options':[option['display'] for option in p.window['options']]}
                        p.to_send.append({'action':'draw_innpc_window', 'window':window})
                    else:
                        window = {'info':p.window['text'],
                                  'owner':p.window['object'].channel.username,
                                  '4th_info':p.window.get('4th_info', ('Error', '4th Info missing!')),
                                  'health':(round(p.window['health'][0]), p.window['health'][1]),
                                  'options':[option['display'] for option in p.window['options']],
                                  'level':p.window['level'],
                                  'color':p.window['object'].channel.color}
                        p.to_send.append({'action':'draw_window', 'window':window})
                if not p.in_window and not (p.text == '' and self.fallen):  # Display tips if walls haven't fallen
                        p.to_send.append({'action':'text','text':p.text})

                self.SendToAll({'action':'num_buildings',
                                'users':[{'name':p.username, 'color':p.color, 'num':p.number, 'bs':str(len(p.get_buildings()))} for p in self.users]})
                if not self.fallen:
                    self.SendToAll({'action':'time', 'time':toolbox.getTime(self)})
        
        self.Pump()
        for p in self.users:
            p.fade_messages()
            p.to_send.append({'action': 'chat', 'messages': p.messages})
            p.Send({'action': 'receive', 'data': p.to_send})
            p.to_send = []

        self.clock.tick(30)
        self.fps = self.clock.get_fps()

def eval_gamemode(gamemode):
    if gamemode == 'Classic':
        walls_time = 10  # In minutes
    elif gamemode == 'Express':
        walls_time = 3
    elif gamemode == 'Extended':
        walls_time = 12
    elif gamemode == 'OP':
        walls_time = 6
    elif gamemode == 'Mutated':
        walls_time = random.randint(3, 6)
    elif gamemode == 'Immediate':
        walls_time = 0.1 # Six seconds
    return walls_time

def main(**kwargs):
    global server  # For debugging if it crashes

    server_name = kwargs.get('name', socket.gethostname())
    server_gamemode = kwargs.get('gamemode', 'Classic')
    server_ip = os.environ['IP']
    server_port = os.environ['PORT']
    server_uri = toolbox.convert_to_uri(ip=server_ip, port=server_port)

    server = Server(name=server_name, gamemode=server_gamemode, port=server_port)
    server.ctx.broadcast_server(name=server_name, ip=server_ip, gamemode=server_gamemode)

    log.info(f'Server launched as "{server_name}".')
    log.info(f'IP: {server_ip}')
    log.info(f'PORT: {server_port}')
    log.info(f'URI: {server_uri}')

    while not server.tired:
        server.update()

if __name__ == '__main__':
    os.environ['IP'] = '127.0.0.1'
    os.environ['PORT'] = 5555
    main()