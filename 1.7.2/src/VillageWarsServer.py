# Python Standard Library Modules Import

import logging as logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')  # Set up logging
log = logging.getLogger()
log.debug('Loading environment')
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

# Configuration

log.debug('Loading configuration')
import configuration as conf  # Personal Module
PATH = conf.PATH
conf.init()

with open(PATH + 'conf/preferences.json', 'r') as fo:
    preferences = json.loads(fo.read())
    py = preferences.get('py', 'python')
    path = preferences.get('path', [])
    sys.path.extend(path)

# Third-Party Imports

log.debug('Importing Third-Party modules')
import pygame
import zipfile2
import requests

# Personal Module Imports

log.debug('Importing modules from personal workspace')
import toolbox
from lobbyAvatar import LobbyAvatar
from player import Character
from background import Background
import obstacle
from building import *
from balloon import Balloon
from resources import Farm, Mine
from NPC import *
from hacking import *
from animations import *
from events import *
from net2web import Channel as ParentChannel, Server as ParentServer, getmyip

log.debug('Finished importing modules')

BUILDINGS = CentralBuilding, PortableCentralBuilding, MinersGuild, FarmersGuild, Balloonist, Inn, FitnessCenter, Gym, RunningTrack, HealthCenter, ConstructionSite, RobotFactory, ArcheryTower, BarrelMaker, BotanistsLab, RepairCenter, Ranch, AlchemistsLab, Market, TownHall, AdvancedBalloonistBuilding, Builders, RetiredBarbarianOutpost, AdventuringCenter

def compress_version(skip=[]):
    global log
    log.debug('Starting Compression...')
    global version
    zipFilename = version + '.zip'
    log.debug(f'Creating {zipFilename}...')
    versionZip = zipfile2.ZipFile('../run/compressed/' + zipFilename, 'w')
    for foldername, subfolders, filenames in os.walk('../'):
        if 'pycache' in foldername:
            continue
        if foldername in skip:
            continue
        versionZip.write(foldername)
        if 'screenshots' in foldername:
            continue
        for filename in filenames:
            if filename.endswith('.zip'):
                continue
            if filename.endswith('serverlog.txt'):
                continue
            if os.path.basename(filename) in skip:
                continue
            log.debug(f'Adding {os.path.basename(filename)}...')
            versionZip.write(foldername + '/' + filename)

    log.debug('Wrapping Up...')
    versionZip.close()
    log.debug('Finished!')
        


def getVersionInt(version_str):
    parts = version_str.split('.')
    return int(parts[0]) * 10000 + int(parts[1]) * 100 + int(parts[2])


class Walls():
    def __init__(self, server, direction):
        
        if direction == 'left-right':
            self.innerrect = pygame.Rect(0, 1860, 6000, 180)
        elif direction == 'up-down':
            self.innerrect = pygame.Rect(2965, 0, 80, 3900)
        server.building_blocks.append(self.innerrect)
        self.dir = direction

        self.count = round(30 * 60 * WALLS_TIME)
        self.server = server
        server.obs.append(self)

        self.owner = None

    def update(self):
        if self.count > 0:
            self.count -= 1
            if self.count == 0:
                if self.dir == 'up-down':
                    self.server.Fall()
                self.server.building_blocks.remove(self.innerrect)
                self.server.obs.remove(self)

    def getHurt(self, damage, attacker):
        pass

    def isBuilding(self):
        return False

    def explode(self):
        pass
        





class ClientChannel(ParentChannel):
    """
    This is the server representation of a single connected client.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        self.ver_int = getVersionInt(self.version)
        
        
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
            self.messages.append({'message':param, 'color':(255,255,255), 'fade':255})
        elif param != self.messages[-1]['message']:
            self.messages.append({'message':param, 'color':(255,255,255), 'fade':255})
        else:
            self.messages[-1]['fade'] = 255
    @message.deleter
    def message(self):
        for message in self.messages:
            message['fade'] -= 1
            if message['fade'] == 0:
                self.messages.remove(message)

    def achievement(self, the_type):
        if self.com:
            return
        res = requests.get(remote_application + 'achievement/' + self.username + '/' + the_type)
        res.raise_for_status()
        #if the_type not in self.server.database[self.username]['achievements']:
        #    newdict = self.server.database[self.username]
        #    newdict['achievements'].append(the_type)
        #    fo = open('achievements.txt', 'r')
        #    achievements = fo.read().split('\n')
        #    if the_type in [achi.split(':')[0] for achi in achievements]:
        #        index = [achi.split(':')[0] for achi in achievements].index(the_type)
        #        newdict['coins'] += int([achi.split(':') for achi in achievements][index][1])
        #    self.server.database[self.username] = newdict
        if res.json()['new']:
            self.Send({'action':'achievement', 'type':the_type})
	
    def Close(self):
        self._server.DelPlayer(self)

    def isValid(self):
        return self.number >= 1 and self.number <= 4

    def get_buildings(self):
        self.buildings = []
        for b in self.server.buildings:
            if b.owner == self and b.state == 'alive':
                self.buildings.append(b)
        return self.buildings

    def reconnect(old_self, self):
        for b in self.server.buildings:
            if b.owner.username == old_self.username:
                b.owner = self
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
            self.to_send.append({'action':'music_change', 'music':'steppingpebbles'})
        self.loc_number = old_self.loc_number
        if self.server.event.__class__ == BarbarianRaid:
            self.to_send.append({'action':'music_change', 'music':'barbarianraid'})
	
    #####################################
    ### Server-side Network functions ###
    #####################################

    """
    Each one of these "Network_" functions defines a command
    that the client will ask the server to do.
    """
    def Network_version(self, data):
        self.version = data['version']
        self.ver_int = getVersionInt(self.version)


    def Network_keys(self, data):
        if self.server.in_lobby:
            item = self.lobby_avatar
        else:
            item = self.character
        if not self.server.paused and not self.pending:
            item.HandleInput(data['keys'], data['mouse'])

    def Network_F6(self, data):
        self.messages = [{'message':'', 'color':(255,255,255), 'fade':255}]
    
    def Network_pause(self, data):
        self.server.paused = not self.server.paused
        for p in self.server.players:
            p.Send({'action':'pause'})

    def Network_eat(self, data):
        self.character.eat()

    def Network_ready(self, data):
        self.lobby_avatar.ready = data['ready']

    def Network_change_gamemode(self, data):
        global GAMEMODE
        GAMEMODE = data['gamemode']
        eval_gamemode()

    def Network_startgame(self, data):
        self.server.ready = True


    def Download(self, namelist):
        print('Starting client download process. May take a few minutes.')
        global log
        skip = []
        for name in namelist:
            if name.endswith('.mp3') or name.endswith('.wav'):
                skip.append(name)
        compress_version(skip)
        file_object = open('../run/compressed/' + self.server.version + '.zip', 'rb')
        log.debug('Reading in binary...')
        file_in_bytes = file_object.read()
        file_object.close()
        max_len = len(repr(file_in_bytes))
        file_in_bytes = file_in_bytes.split(b'\n')
        div = len(file_in_bytes)
        log.debug('Sending data over to client...')
        self.Send({'action':'open', 'version':self.server.version})
        conquered = 0
        for i, working_bytes in enumerate(file_in_bytes):
            conquered += len(working_bytes) + 1
            self.Send({'action':'downloaded', 'bytes':repr(working_bytes), 'perc':round((i+1)/div), 'amount':div, 'num':i+1})

            
    def Network_init(self, data):
        if data['status'] == 'DOWNLOAD':
            thread = threading.Thread(target=self.Download, args=[data['namelist']])
            thread.start()
            return
        if data['status'] == 'COM':
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
            data['status'] = 'RC'
            
        
        if data['status'] == 'JG':
            self.username = data['username']

            if not self.server.in_lobby:
                
                for p in self.server.players:
                    p.message = data['username'] + ' joined to watch the game.'
                    p.message_count = 150
                    p.message_color = (255,255,0)
                    
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
        

        elif data['status'] == 'RC':
            if data['username'] in self.server.playing:
                self.server.playing[data['username']].reconnect(self)
                for p in self.server.players:
                    p.message = data['username'] + ' has reconnected.'
                    p.message_count = 160
                    p.message_color = (255,205,0)

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



class MyGameServer(ParentServer):
    
	
    def __init__(self, version, *args, **kwargs):
        """
        Server constructor function. This is the code that runs once
        when the server is made.
        """
        self.version = version
        self.ver_int = getVersionInt(self.version)

        self.paused = False
        
        super().__init__(*args, **kwargs)

        self.ChannelClass = ClientChannel
        
        self.clock = pygame.time.Clock()
        self.tired = False
        self.starttime = time.time()
        self.ready = False
        
        self.obstacles = pygame.sprite.Group()
        self.buildings = pygame.sprite.Group()
        self.balloons = pygame.sprite.Group()
        self.resources = pygame.sprite.Group()
        self.NPCs = pygame.sprite.Group()
        self.animations = pygame.sprite.Group()
        self.trees = pygame.sprite.Group()
        self.bushes = pygame.sprite.Group()
        
        obstacle.Obstacle.gp = self.obstacles
        Building.gp = self.buildings
        Balloon.gp = self.balloons
        Farm.gp = self.resources
        Mine.gp = self.resources
        Farmer.gp = self.NPCs
        Miner.gp = self.NPCs
        obstacle.TNT.gp = self.obstacles
        ArcheryTower.gp = self.NPCs
        Robot.gp = self.NPCs
        Animation.gp = self.animations
        obstacle.Tree.gp = self.trees
        obstacle.SpikyBush.gp = self.bushes
        self.lobby_background = Background(self)
        self.lobby_background.x = -1500
        self.lobby_background.y = -800

        self.obs = list(self.obstacles) + list(self.buildings)

        
        self.ST_COORDS = [None, (500, 400), (5500, 400), (500, 3500), (5500, 3500)]
        self.LOBBY_COORDS = [None, (150, 100), (150, 200), (150, 300), (150, 400)]
        self.COLORS = [None, (255, 0, 0), (0,0,255), (255,255,0), (0,255,0)]
        
        self.in_lobby = True

        global log
        log.info('VillageWars ' + self.version + ' server')

        self.fallen = False
        self.building_blocks = []

        self.playing = {}

        self.count = 0

        self.barbarian_count = random.randint(int(30*60*0.5), 30*60*6) + WALLS_TIME * 30 * 60

    #def save(self):
    #    global log
    #    log.debug('Saving data...')
    #    self.database.close()
    #    self.database = shelve.open('database/data')
    #    log.debug('Data saved!')

    def Fall(self):
        self.fallen = True

        for p in self.players:
            p.Send({'action':'fall'})
        global log
        log.info('Walls falling')
        
        for p in self.players:
            p.message = 'Walls have fallen!'
            p.message_count = 150
            p.message_color = (255, 205, 0)
    

    
    def connection(self, player):
        """
        Connected function runs every time a client
        connects to the server.
        """
        global GAMEMODE
        player.server = self
        player.to_send.append({'action':'gamemode', 'gamemode':GAMEMODE})

        global log
        log.info('Connection')


    def Initialize(self, player):
        global log
        if not player.com:
            self.PlayerNumber(player)
        if self.in_lobby:
            if player.isValid():
                
                self.PlayerLobbyAvatar(player)
                log.info(player.username + ' joined')
                if player.number == 1:
                    player.ishost = True
                self.PrintPlayers()
            else:
                player.Send({'action':'disconnected'})
                
                log.info('Extra player was kicked (num %s, max is 4)' % player.number)
        else:
            log.debug(player.username + " joined")
            player.server = self
            self.PrintPlayers()
            player.character = Character(player, 3000, 1900)
            player.character.dead = True
            player.color = (128,128,128)
            player.character.speed = 16
            

    def PlayerNumber(self, player):
        if self.in_lobby:
            used_numbers = [p.number for p in self.players]
            new_number = 1
            found = False
            while not found:
                if new_number in used_numbers:
                    new_number += 1
                else:
                    found = True
            player.number = new_number
        else:
            player.number = 99999
    def PlayerColor(self, player):
        player.color = self.COLORS[player.number]
            

    def PlayerLobbyAvatar(self, player):
        player.lobby_avatar = LobbyAvatar(self.LOBBY_COORDS[player.number])

    def getTime(self):
        if self.fallen:
            return '0'
        seconds = ((self.upwall.count // 30) % 60) + 1
        minutes = (self.upwall.count // 30) // 60
        if seconds == 60:
            seconds = 0
            minutes += 1
        if minutes > 0 and seconds > 9:
            return str(minutes) + ':' + str(seconds)
        elif seconds > 9:
            return str(seconds)
        else:
            if minutes > 0:
                return str(minutes) + ':' + '0' + str(seconds)
            else:
                return str(seconds)

    def StartGame(self):
        
        self.in_lobby = False
        global log, name
        if conf.INTERNET:
            try:
                res = requests.get(remote_application + 'startgame/' + name)
                res.raise_for_status()
            except:
                conf.INTERNET = False
        
        loc_numbers = list(range(4))
        random.shuffle(loc_numbers)
        for p in self.players:
            p.loc_number = loc_numbers[p.number - 1] + 1
            if p.isValid():
                p.character = Character(p, self.ST_COORDS[p.loc_number][0], self.ST_COORDS[p.loc_number][1])

            if p.loc_number == 1:
                CentralBuilding(self, 900, 630, p)
            if p.loc_number == 2:
                CentralBuilding(self, 5100, 630, p)
            if p.loc_number == 3:
                CentralBuilding(self, 900, 2900, p)
            if p.loc_number == 4:
                CentralBuilding(self, 5100, 2900, p)

                
                
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

        self.paused = False

        self.event = Event(self)

        self.upwall = Walls(self, 'up-down')
        self.leftwall = Walls(self, 'left-right')
            
        log.info('Game starting')
        
        for p in self.players:
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
        global log
        if player.pending == False:
            log.debug("Deleting Player")
            self.PrintPlayers()
            for p in self.players:
                p.message = player.username + ' left the game.'
                p.message_count = 150
                p.message_color = (255,0,0)

        
        log.info(player.username + ' disconnected.')

	
    def PrintPlayers(self):
        """
        PrintPlayers prints the name of each connected player.
        """
        global log
        log.info("Joined Players:" + ', '.join([p.username for p in self.players]))

        
    def SendToAll(self, data):
        """
        SendToAll sends 'data' to each connected player.
        """
        for p in self.players:
            p.to_send.append(data)

    def terminate(self, winner):
        winner.Send({'action':'victory'})
        


        global log
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
            for p in self.players:
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


        if GAMEMODE == 'Mutated' and round((time.time() - self.starttime) % 60) == 0:
            for p in self.players:
                if p.build_to_place is None:
                    p.message = 'You\'ve received a random building. Surprise!'
                    p.message_count = 150
                    p.message_color = (255, 255, 255)
                    p.build_to_place = random.choice(BUILDINGS)


        if self.in_lobby:
            all_ready = True
            all_pending = True
            for p in self.players:
                if not p.pending:
                    p.to_send.append({'action':'draw_lobby_background',
                                      'coords':(p.lobby_avatar.get_x(self.lobby_background), p.lobby_avatar.get_y(self.lobby_background)),
                                      'x':p.lobby_avatar.get_x(0),
                                      'y':p.lobby_avatar.get_y(0),})
            for p in self.players:
                if not p.pending:
                    for p2 in self.players:
                        if not p2.pending:
                            p2.to_send.append({'action':'draw_avatar',
                                        'coords':(p2.lobby_avatar.get_x(p.lobby_avatar), p2.lobby_avatar.get_y(p.lobby_avatar)),
                                        'ready':p.lobby_avatar.ready,
                                        'angle':p.lobby_avatar.angle,
                                        'username':p.username,
                                        'color':p.color,
                                        'skin':p.skin,
                                        'host':p2.ishost})
                    if p.ver_int < self.ver_int:
                        print(p.ver_int, '<', self.ver_int)
                        p.to_send.append({'action':'WARNING_outdated_client', 'version':self.version})
                    if p.ver_int > self.ver_int:
                        p.to_send.append({'action':'WARNING_outdated_server', 'version':self.version})
                    
                    if not p.pending:
                        all_pending = False
                    if not p.lobby_avatar.ready:
                        all_ready = False
                    if p.ishost:
                        p.to_send.append({'action':'display_host', 'enough?':len([p for p in self.players if not p.pending]) > 1})

            if (self.ready or all_ready) and not all_pending and (len(self.players) > 1 or self.ready):
                self.StartGame()
        else:
            
            if not self.paused:
                self.SendToAll({'action':'draw_background'})
                self.count += 1
                if not self.fallen:
                    self.upwall.update()
                    self.leftwall.update()

                
                if self.count == self.barbarian_count:
                    BarbarianRaid(self)
                
                self.background.update()
                self.buildings.update()
                self.obstacles.update()
                self.bushes.update()
                self.resources.update()
                self.NPCs.update()
                self.balloons.update()
                self.event.update()
                self.animations.update()
                
                
                for p in self.players:
                    if not p.pending:
                        p.character.update()

                        

                self.trees.update()

                for p in self.players:
                    if not p.pending:
                        p.to_send.append(p.character.hud())

                for p in self.players:

                    if p.in_window:

                        if p.in_innpc_window:
                            window = {'info':p.window['text'],
                                  'options':[item[0] for item in p.window['options']]}
                            p.to_send.append({'action':'draw_innpc_window',
                                       'window':window})
                    
                        else:
                            window = {'info':p.window['text'],
                                  'owner':p.window['building'].owner.username,
                                  '4th_info':p.window.get('4th_info', ('Error', '4th Info missing!')),
                                  'health':(round(p.window['health'][0]), p.window['health'][1]),
                                  'options':p.window['simp'],
                                  'level':p.window['level'],
                                  'color':p.window['building'].owner.color}

                    
                    
                            p.to_send.append({'action':'draw_window',
                                           'window':window})
                    

                    
                    
                        
                        
                    if not p.in_window and not (p.text == '' and self.fallen):
                        p.to_send.append({'action':'text','text':p.text})

                        

                users = []
                for p in self.players:
                    if not p.pending:
                        users.append({'name':p.username, 'color':p.color, 'num':p.number, 'bs':str(len(p.get_buildings()))})
                self.SendToAll({'action':'num_buildings', 'users':users})
                if not self.fallen:
                    self.SendToAll({'action':'time', 'time':self.getTime()})
        for p in self.players:
            del p.message
            p.to_send.append({'action':'chat', 'messages':p.message})


        for p in self.players:
            p.to_send.append({'action':'flip', 'paused':self.paused})
        self.clock.tick(30)
        
        for p in self.players:
            p.Send({'action':'receive', 'data':p.to_send, 'timestamp':round(time.time())})
            p.to_send = []        
        fps = self.clock.get_fps()

def eval_gamemode():
    global WALLS_TIME
    if GAMEMODE == 'Classic':
        WALLS_TIME = 10  # In minutes
    elif GAMEMODE == 'Express':
        WALLS_TIME = 3
    elif GAMEMODE == 'Extended':
        WALLS_TIME = 12
    elif GAMEMODE == 'OP':
        WALLS_TIME = 6
    elif GAMEMODE == 'Mutated':
        WALLS_TIME = random.randint(3, 6)
    elif GAMEMODE == 'Immediate':
        WALLS_TIME = 0.1 # Six seconds

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
else:
    ip = getmyip()

log.debug('Identifying connection port')
port = 5555

__version__ = conf.VERSION
log.info('VillageWars Server ' + __version__)

log.debug('Identifying gamemode')
# Set the gamemode to one of these: 'Classic' or 'Express' or 'Extended' or 'OP' or 'Mutated' or 'Immediate'
GAMEMODE = input('Gamemode = ') or 'Classic'
print('Gamemode set to', GAMEMODE)
eval_gamemode()
log.debug('Identifying server name')
hostname = socket.gethostname()
name = input('Please input the server\'s name (leave blank for "%s") : ' % hostname) or hostname

log.debug('Launching server')
server = MyGameServer(__version__, host=ip, port=port)
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
