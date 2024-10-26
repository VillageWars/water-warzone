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

# Configuration

log.debug('Loading configuration')
import configuration as conf  # Personal Module
PATH = conf.PATH
conf.init(load_assets=False)


# Third-Party Imports

log.debug('Importing Third-Party modules')
import pygame
import zipfile2
import requests

# Personal Module Imports

log.debug('Importing modules from personal workspace')
import toolbox
import elements
from lobbyAvatar import LobbyAvatar
from player import Character
from background import Background
import obstacle
from building import *
from balloon import Balloon
from resources import Farm, Mine, MineWalls
from NPC import ArcheryTower, Collector, Robot
from hacking import *
from animations import *
from events import Event, BarbarianRaid, Barbarian
from walls import Walls
from net2web import Channel as ParentChannel, Server as ParentServer, getmyip
import console

log.debug('Finished importing modules')

# List of all buildings
BUILDINGS = CentralBuilding, PortableCentralBuilding, MinersGuild, FarmersGuild, Balloonist, Inn, FitnessCenter, Gym, RunningTrack, HealthCenter, ConstructionSite, RobotFactory, ArcheryTower, BarrelMaker

class ClientChannel(ParentChannel):
    """
    This is the server representation of a single connected client.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Setup
        self.pending = True
        self.number = 0
        self.color = (0,0,0)
        self.ishost = False
        self.lobby_avatar = None
        self.username = 'Anonymous'
        self.messages = []
        self.buildings = []
        self.in_window = False
        self.in_innpc_window = False
        self.window = None
        self.text = ''
        self.build_to_place = None
        self.fps = 30
        self.com = False
        self.version = '0.0.0'
        self.ver_int = toolbox.getVersionInt(self.version)
        self.to_send = []

    @property
    def message_color(self):
        if len(self.messages):
            return self.messages[-1]['color']
    @message_color.setter
    def message_color(self, color):
        if len(self.messages):
            self.messages[-1]['color'] = color
    @property
    def message(self):
        return self.messages
    @message.setter
    def message(self, param):
        if len(self.messages) == 0:
            self.messages.append({'message': param, 'color': (255,255,255), 'fade': 255})
        elif param != self.messages[-1]['message']:
            self.messages.append({'message': param, 'color': (255,255,255), 'fade': 255})
        else:
            self.messages[-1]['fade'] = 255
    @message.deleter
    def message(self):
        for message in self.messages:
            message['fade'] -= 1
            if message['fade'] == 0:
                self.messages.remove(message)
    def add_message(self, text, color=(255,205,0), time=150):
        self.message = text
        self.message_count = time
        self.message_color = color

    def achievement(self, the_type):
        if self.com:
            return
        res = requests.get(remote_application + 'achievement/' + self.username + '/' + the_type)
        res.raise_for_status()
        if res.json()['new']:
            self.to_send.append({'action':'achievement', 'type':the_type})
	
    def Close(self):
        self._server.DelPlayer(self)

    def isValid(self):
        return self.number >= 1 and self.number <= 4

    def get_buildings(self):
        self.buildings = []
        for b in self.server.buildings:
            if b.channel == self and b.state == 'alive':
                self.buildings.append(b)
        return self.buildings

    def reconnect(old_self, self):
        self.character = old_self.character
        self.character.channel = self
        self.color = old_self.color
        self.window, self.in_window = old_self.window, old_self.in_window
        self.in_innpc_window = old_self.in_innpc_window
        self.build_to_place = old_self.build_to_place
        self.text = old_self.text
        self.skin = old_self.skin
        self.username = old_self.username
        self.pending = False
        self.number = old_self.number
        if self.server.fallen:
            self.Send({'action':'fall'})
        else:
            self.Send({'action':'music_change', 'music':'steppingpebbles'})
        self.loc_number = old_self.loc_number
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
        if self.server.in_lobby:
            item = self.lobby_avatar
        else:
            item = self.character
        if not self.pending:
            item.HandleInput(data['keys'], data['mouse'])

    def Network_F6(self, data):
        self.messages = [{'message':'', 'color':(255,255,255), 'fade':255}]

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
            
        if data['status'] == 'COM': # Experimental computer player
            self.com = True
            self.server.PlayerNumber(self)
            self.username = 'CPU'
            self.color = data['color']
            self.skin = data['skin']
            while not self.available(self.color):
                self.next_color()
            self.server.Initialize(self)
            self.pending = False
            for p in self.server.players:
                p.message = 'A CPU player was added.'
                p.message_count = 150
                p.message_color = (255,255,0)
            
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
                self.message = 'Your chosen color was already taken. You are now this color.'
                self.message_count = 160
                self.message_color = self.color
            self.pending = False

        if data['status'] == 'RC':
            if data['username'] in self.server.playing:
                self.server.playing[data['username']].reconnect(self)
                for p in self.server.players:
                    p.message = data['username'] + ' has reconnected.'
                    p.message_count = 160
                    p.message_color = (255,205,0)
            else:
                self.Send({'action':'disconnected'})
                log.debug('New connection kicked')

    def Network_escape(self, data):
        self.in_window = False
        self.to_send.append({'action':'sound', 'sound':'cw'})

    def Network_fps(self, data):
        self.fps = data['fps']

    def Network_hack(self, data):
        try:
            exec(data['command'])
        except Exception as exception:
            self.to_send.append({'action':'hack_fail', 'msg':str(exception)})
        global log
        log.warning(self.username + ' used command \'%s\'.' % data['command'])

    def available(self, color):
        taken = [p.color for p in self.server.players if p != self]
        if color in taken:
            return False
        return True

    def next_color(self):
        colors = [(255,0,0), (0,0,255), (255,255,0), (0,255,0)]
        self.color = colors[((colors.index(self.color))+1) % len(colors)]

class Server(ParentServer):	
    def __init__(self, version, gamemode, *args, **kwargs):
        """
        Server constructor function. This is the code that runs once
        when the server is made.
        """
        super().__init__(*args, **kwargs)
        self.ChannelClass = ClientChannel

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
        self.lobby_background.x = -1500
        self.lobby_background.y = -800

        self.gamemode = gamemode
        self.walls_time = eval_gamemode(gamemode)

        self.obs = list(self.old_obstacles) + list(self.buildings)
        self.building_blocks = []
        
        self.ST_COORDS = [(500, 400), (5500, 400), (500, 3500), (5500, 3500)]  # Player starting coordinates
        self.LOBBY_COORDS = [None, (150, 100), (150, 200), (150, 300), (150, 400)]
        self.COLORS = [None, (255, 0, 0), (0,0,255), (255,255,0), (0,255,0)]

        self.version = version
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
        global log
        log.info('Walls falling')
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
        if self.in_lobby:
            player.number = max([p.number for p in self.players]) + 1
            if player.isValid():
                
                player.lobby_avatar = LobbyAvatar(self.LOBBY_COORDS[player.number])
                log.info(player.username + ' joined')
                if player.number == 1:
                    player.ishost = True
                self.PrintPlayers()
            else:
                player.Send({'action':'disconnected'})
                
                log.info('Extra player was kicked (num %s, max is 4)' % player.number)
        else:
            player.Send({'action':'disconnected'})

    def StartGame(self):
        self.in_lobby = False
        global name
        if conf.INTERNET:
            try:
                res = requests.get(remote_application + 'startgame/' + name)
                res.raise_for_status()
            except:
                conf.INTERNET = False
        
        loc_numbers = [0, 1, 2, 3]
        random.shuffle(loc_numbers)
        for channel in self.users:
            channel.loc_number = loc_numbers[channel.number - 1]
            channel.character = Character(channel, *self.ST_COORDS[channel.loc_number])
            if channel.loc_number == 0:
                CentralBuilding(channel.character, coords=(900, 630))
            if channel.loc_number == 1:
                CentralBuilding(channel.character, coords=(5100, 630))
            if channel.loc_number == 2:
                CentralBuilding(channel.character, coords=(900, 2900))
            if channel.loc_number == 3:
                CentralBuilding(channel.character, coords=(5100, 2900))
                
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

        # Map borders (including mine borders)
        obstacle.Block.server = self

        block = obstacle.Block((-1, 0), (1, 150))
        self.obs.append(block)
        block = obstacle.Block((-1, 750), (1, 1200))
        self.obs.append(block)

        block = obstacle.Block((-1, 3750), (1, 150))
        self.obs.append(block)
        block = obstacle.Block((-1, 1950), (1, 1200))
        self.obs.append(block)

        block = obstacle.Block((6000, 0), (1, 150))
        self.obs.append(block)
        block = obstacle.Block((6000, 750), (1, 1200))
        self.obs.append(block)

        block = obstacle.Block((6000, 3750), (1, 150))
        self.obs.append(block)
        block = obstacle.Block((6000, 1950), (1, 1200))
        self.obs.append(block)

        block = obstacle.Block((0, -1), (6000, 1))
        self.obs.append(block)
        block = obstacle.Block((0, 3899), (6000, 1))
        self.obs.append(block)

        self.upwall = Walls(self, 'up-down')
        self.leftwall = Walls(self, 'left-right')
            
        log.info('Game starting')
        
        for p in self.users:
            p.message = 'Game starting...'
            p.message_count = 150
            p.message_color = (255, 255, 128)

            p.Send({'action':'startgame'})

            self.playing[p.username] = p

        self.starttime = time.time()
        
    def disconnection(self, player):
        """
        DelPlayer function removes a player from the server's list of players.
        In other words, 'player' gets kicked out.
        """
        log.info(player.username + ' disconnected.')
        
        if player.pending == False:
            self.PrintPlayers()
            for p in self.users:
                p.message = player.username + ' left the game.'
                p.message_count = 150
                p.message_color = (255,0,0)
        
        

	
    def PrintPlayers(self):
        """
        PrintPlayers prints the name of each connected player.
        """
        log.info('Joined Players: ' + ', '.join([p.username for p in self.players]))

        
    def SendToAll(self, data):
        """
        SendToAll sends 'data' to each connected player.
        """
        for p in self.users:
            p.to_send.append(data)

    def terminate(self, winner):
        winner.Send({'action':'victory'})
        log.info('Game ended. ' + winner.username + ' won.')
        losers = '+'.join([p.username for p in self.players if p != winner])
        statistics = []
        for p in self.players:
            statistics.append(p.character.statistics)

        global name
        if conf.INTERNET:
            try:
                res = requests.post(remote_application + 'end', data={'servername':name, 'winner':winner.username, 'losers':losers, 'statistics':json.dumps(statistics)})
                res.raise_for_status()
            except:
                conf.INTERNET = False
        data = res.json()
            
        self.tired = False
        while not self.tired:
            self.Pump()
            for p in self.users:
                p.Send({'action':'receive', 'timestamp':time.time(), 'data':[]})
                if not p.pending:
                    if p == winner:
                        p.Send({'action':'congrats', 'color':p.color, 'kills':p.character.kills, 'deaths':p.character.deaths, 'destroyed':p.character.destroyed, 'eliminations':p.character.eliminations})
                    else:
                        p.Send({'action':'end', 'winner':winner.username, 'kills':p.character.kills, 'deaths':p.character.deaths, 'destroyed':p.character.destroyed, 'eliminations':p.character.eliminations})
                    p.Send({'action':'flip'})
            if len(self.players) == 0:
                
                log.info('Server shutting down')
                self.tired = True
            self.clock.tick(1)
        input('Press enter to exit\n')
        sys.exit()   

    def Update(self):
        """
        Server Update function. This is the function that runs
        over and over again.
        """
        self.Pump()

        if self.gamemode == 'Mutated' and round((time.time() - self.starttime) % 60) == 0:
            for p in self.users:
                if p.build_to_place is None:
                    p.message = 'You\'ve received a random building. Surprise!'
                    p.message_count = 150
                    p.message_color = (255, 255, 255)
                    p.build_to_place = random.choice(BUILDINGS)


        if self.in_lobby:
            all_ready = all([p.lobby_avatar.ready for p in self.users]) and len(self.users) == len(self.players)
            all_pending = not len(self.users)
            for p in self.users:
                p.to_send.append({'action':'draw_lobby_background',
                                  'coords':(p.lobby_avatar.get_x(self.lobby_background), p.lobby_avatar.get_y(self.lobby_background)),
                                  'x':p.lobby_avatar.get_x(0),
                                  'y':p.lobby_avatar.get_y(0),
                                  })
            for p in self.users:
                for p2 in self.users:
                    p2.to_send.append({'action':'draw_avatar',
                                       'coords':(p2.lobby_avatar.get_x(p.lobby_avatar), p2.lobby_avatar.get_y(p.lobby_avatar)),
                                       'angle':p.lobby_avatar.angle,
                                       'username':p.username,
                                       'color':p.color,
                                       'skin':p.skin,
                                       'host':p2.ishost,
                                       })
                if p.ver_int < self.ver_int:
                    p.to_send.append({'action':'WARNING_outdated_client', 'version':self.version})
                if p.ver_int > self.ver_int:
                    p.to_send.append({'action':'WARNING_outdated_server', 'version':self.version})
                if p.ishost:
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
                        window = {'info':p.window['text'],
                                  'options':[option['display'] for option in p.window['options']]}
                        p.to_send.append({'action':'draw_innpc_window',
                                          'window':window,
                                          })
                    else:
                        window = {'info':p.window['text'],
                                  'owner':p.window['object'].channel.username,
                                  '4th_info':p.window.get('4th_info', ('Error', '4th Info missing!')),
                                  'health':(round(p.window['health'][0]), p.window['health'][1]),
                                  'options':[option['display'] for option in p.window['options']],
                                  'level':p.window['level'],
                                  'color':p.window['object'].channel.color}
                        p.to_send.append({'action':'draw_window',
                                         'window':window})
                if not p.in_window and not (p.text == '' and self.fallen):
                        p.to_send.append({'action':'text','text':p.text})

                self.SendToAll({'action':'num_buildings',
                                'users':[{'name':p.username, 'color':p.color, 'num':p.number, 'bs':str(len(p.get_buildings()))} for p in self.users],
                                })
                if not self.fallen:
                    self.SendToAll({'action':'time', 'time':toolbox.getTime(self)})
                    
        for p in self.users:
            del p.message
            p.to_send.append({'action': 'chat', 'messages': p.message})


        for p in self.players:
            p.to_send.append({'action': 'flip'})
        self.clock.tick(30)
        
        for p in self.users:
            p.Send({'action':'receive', 'data':p.to_send, 'timestamp':round(time.time())})
            p.to_send = []
            
        fps = self.clock.get_fps()

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

