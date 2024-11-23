# Python Standard Library Modules Import

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

import shelve
import random
import json
import time
import threading
import re
import sys
import os

# Configuration

import configuration as conf  # Personal Module
PATH = conf.PATH
MAP_TEXTURE = conf.MAP_TEXTURE

# Third-Party Imports

import pygame
import pygame as p
from pygame.locals import *
from pymsgbox import alert, confirm, prompt, password

# Personal Module Imports

import toolbox
import toolbox as t
from net2web import Client as ParentClient
from remote_app_manager import Context

import __main__

answer = ''    

def get_setting(filepath):
    im = p.transform.scale(conf.images[filepath], (300,300))
    walls = conf.images['texture building/walls.png']
    setting = p.Surface((6000,3900))
    width = 6000//300
    height = 3900//300
    for y in range(height):
        for x in range(width):
            setting.blit(im, (x*300, y*300))
    setting2 = setting.__copy__()
    setting2.blit(walls, (0,0))
    return setting2, setting

def hack(self):
    fo = shelve.open('database/admin')
    admin_passwords = fo['passwords']
    fo.close()
    command = prompt('Enter the command:', title='VillageWars Console')
    if command is not None:
        attempt = password('You need an admin password to proceed.', title='VillageWars Console')
        if attempt in admin_passwords:
            self.Send({'action':'hack', 'command':command})
            alert('Password Accepted: Command Sent', title='VillageWars Console')
        else:
            alert('Password Incorrect', title='VillageWars Console')

def find_cursor(cursor_param):
    regex = re.compile(r'constant: SYSTEM_CURSOR_(.*)\)>')
    res = regex.search(repr(cursor_param))
    return res.group(1)

def shut_down():
    p.mixer.music.stop()
    p.quit()
    input('Press enter to shut down')
    sys.exit()


class Client(ParentClient):
    def __init__(self, uri='ws://127.0.0.1:5555', screen=None, username='ModestNoob', color=(255,0,0), skin=0, ctx=None):

        super().__init__(uri=uri)
        
        pygame.init()
        self.started = False
        self.screen = screen
        self.clock = p.time.Clock()
        self.skin = skin
        self.color = color
        self.ctx = ctx or Context()

        self.last_frame = pygame.Surface((1000, 650))

        self.fps_expected = 30

        self.toDraw = []
        self.toDrawNext = []

        self.disconnected = 0

        x, y, width, height = 700, 0, 300, 50
        self.dropdown_open = False
        self.dropdown_rect = pygame.Rect(x, y, width, height)
        
        self.gamemodes = ['Classic', 'Express', 'Immediate', 'OP']
        self.gamemode = 'Classic'

        self.back_pic = conf.images['BG_SciFi.png']
        self.ocean_pics = [conf.res('ocean/' + i, (1000, 1000)) for i in os.listdir(PATH + 'assets/ocean/')]
        self.ocean_frame = 0
        self.players = [(conf.res('Skins/%s.png' % (i), (50, 50)), conf.res('Skins/%sh.png' % (i), (50, 50))) for i in range(len(os.listdir('../assets/Skins'))//2)]
        self.archer = conf.res('Enemy_04.png', (50, 50))

        self.bolt = conf.images['barbarians/bolt.png']

        self.startgame_icon = conf.images['Startgame_btn.png']
        self.startgame_icon_over = conf.images['Startgame_btn_over.png']
        self.startgame_icon_locked = conf.images['Startgame_btn_locked.png']

        self.balloon = conf.images['balloon.png']
        self.op_balloon = conf.images['balloon2.png']
        self.speedy_plus_op = conf.images['Drop.png']
        self.speedy_balloon = conf.images['DropSmall.png']
        self.robot = conf.res('Enemy_05.png', (50, 50))
        self.robot_hurt = conf.res('Enemy_05_hurt.png', (50, 50))

        self.animations = {
            'Splash':(conf.images['splash1.png'], conf.images['splash2.png'], conf.images['splash3.png']),
            'Explosion':(conf.images['explode1.png'], conf.images['explode2.png'], conf.images['explode3.png']),
            'BAM':(conf.res('LargeExplosion1.png', (360, 360)), conf.res('LargeExplosion1.png', (360, 360)), conf.res('LargeExplosion2.png', (360, 360)), conf.res('LargeExplosion2.png', (360, 360)), conf.res('LargeExplosion3.png', (360, 360)), conf.res('LargeExplosion3.png', (360, 360)))
            }

        
        
        self.red = conf.images['buildings/red.png']
        self.blue = conf.images['buildings/blue.png']
        self.green = conf.images['buildings/green.png']
        self.yellow = conf.images['buildings/yellow.png']
        self.black = conf.images['buildings/black.png']
        self.preview = conf.images['buildings/preview.png']

        self.house = conf.images['buildings/House.png']
        self.house_burnt = conf.images['buildings/House_burnt.png']

        self.building_person = conf.res('Skins/4.png', (50, 50))
  
        self.miner = conf.res('Skins/2.png', (50, 50))
        self.farmer = conf.res('Skins/4.png', (50, 50))

        self.barbarians = {
            'leader':[conf.images['barbarians/leader.png'], conf.images['barbarians/leaderh.png'], conf.images['barbarians/leaderm.png']],
            'archer':[conf.images['barbarians/archer.png'], conf.images['barbarians/archerh.png']],
            'swordsman':[conf.images['barbarians/swordsman.png'], conf.images['barbarians/swordsmanh.png']]
            }
        self.barbarian_range = conf.res('barbarians/range.png', (700, 700))
        self.shield = conf.images['barbarians/shield.png']
        self.barbarian_banner = conf.res('barbarians/banner.png', (45, 90))

        for i, b in enumerate(self.barbarians['leader']):
            self.barbarians['leader'][i] = p.transform.scale(b, (50, 50))
        for i, b in enumerate(self.barbarians['archer']):
            self.barbarians['archer'][i] = p.transform.scale(b, (50, 50))
        for i, b in enumerate(self.barbarians['swordsman']):
            self.barbarians['swordsman'][i] = p.transform.scale(b, (50, 50))
        
        self.startgame_rect = self.startgame_icon.get_rect(topleft=(445, 400))

        self.Setting, self.no_walls_setting = get_setting('texture building/%s.png' % (MAP_TEXTURE))

        self.food_image = conf.images['food.png']
        self.food_used = conf.images['food_used.png']
        self.food_mine = conf.images['food_mine.png']

        self.plate = conf.res('meals/plate.png', (100, 100))
        self.meals = [conf.res('meals/meal%s.png' % (num - 1), (100, 100)) for num in range(len(os.listdir('../assets/meals'))) if num not in (0, 1)]

        self.gold_image = conf.res('gold.png', (45, 45))
        self.gold_mine = conf.res('gold_mine.png', (45, 45))

        self.mine = conf.images['mine.png']

        self.x = conf.images['x.png']
        self.x_hov = conf.images['x_hov.png']

        self.tree = conf.res('trees/tree1.png', (200, 280))
        self.sappling = conf.images['trees/sappling.png']

        self.large_font = p.font.SysFont('default', 80)
        self.medium_font = p.font.SysFont('default', 40)
        self.small_font = p.font.SysFont('default', 20)
        self.small_fantasy_font = p.font.SysFont('luminari', 20)

        self.crate = conf.res('crate.png', (50, 50))
        self.barrel = conf.res('Barrel.png', (50, 50))
        self.barrel_tnt = conf.res('BarrelTNT.png', (50, 50))
        self.barrel_broken = conf.res('BarrelRubble.png', (50, 50))
        
        self.tnt = conf.res('TNT.png', (50, 50))
        self.gate = conf.images['gate.png']
        self.spiky_bush = conf.images['spiky_bush.png']

        self.ready = False

        self.host_text = self.small_font.render('host', True, (255,0,0))
        self.escape_count = 0
        self.username = username

        p.mixer.init()
        self.sound_be = conf.audio['explosion-big.wav'] # be for big explosion
        self.sound_se = conf.audio['explosion-small.wav'] # se for small explosion
        self.sound_sp = conf.audio['splash.wav'] # sp for splash
        self.sound_sh = conf.audio['splash-heavy.wav'] # sh for splash heavy
        self.sound_shot = conf.audio['shot.wav']
        self.sound_bump = conf.audio['bump.wav']
        self.sound_ba = conf.audio['break.wav']  # ba for barrel
        self.sound_bb = conf.audio['building.wav'] # bb for broken building
        self.sound_ow = conf.audio['open_window.wav']
        self.sound_cw = conf.audio['close_window.wav']

        self.musics = {
            'steppingpebbles': conf.sfx_dir + 'stepPebblesLoop.mp3',
            'village': conf.sfx_dir + 'villageLoop.mp3',
            'barbarianraid': conf.sfx_dir + 'War song.mp3'
            }

        self.F3 = False

        with open('tips.json', 'r') as tipfile:
            tips = json.loads(tipfile.read())
            self.tips = tips['basic_tips']
            num_rare = random.choice([0,0,0,0,1,1,1,2,2,3])
            random.shuffle(tips['rare_tips'])
            for i, rare_tip in enumerate(tips['rare_tips'][:]):
                tips['rare_tips'][i] = '+' + rare_tip
            self.tips.extend(tips['rare_tips'][:num_rare])
        self.tip_frame = 0
        self.tip = 0


        self.achievement_pic = conf.res('achievement.png', (225, 50))
        
        self.achievement = [0, 'None']

        self.version = conf.VERSION
        

    def update(self):
        """
        Client update function. This is the function that runs over and
        over again, once every frame of the game.
        """

        self.mouseX, self.mouseY = p.mouse.get_pos()[:2]
        
        self._connected = False
        self.Pump()
        global running

        if answer == 'OK':
            p.quit()
            exit()

        global cursor
        old_cursor = p.mouse.get_cursor()
        if not find_cursor(cursor) == find_cursor(old_cursor):
            p.mouse.set_cursor(cursor)
        cursor = p.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW)

        if not self._connected:
            self.disconnected += 1
        else:
            self.disconnected = 0

        if self.escape_count:
            self.escape_count -= 1

        if self.disconnected == 50 and self.connected:
            c = confirm('Connection is low.', title='VillageWars', buttons=['Quit', 'Continue'])
            if c == 'Quit':
                shut_down()
        
        self.tip_frame += 1
        if self.tip_frame == 250:
            self.tip_frame = 0
            self.tip += 1
            if self.tip == len(self.tips):
                self.tip = 0
                random.shuffle(self.tips)
                if 'Always get a Miner\'s Guild and a Farmer\'s Guild first!' in self.tips:
                    self.tips.remove('Always get a Miner\'s Guild and a Farmer\'s Guild first!')

        
        # Set running to False if the player clicks the X
        global music_playing
        
        for event in pygame.event.get():
            if event.type == QUIT:
                def confirm_exit():
                    global answer
                    answer = confirm('The game is still going. Are you sure you want to quit?')
                thread = threading.Thread(target=confirm_exit)
                thread.start()
                
            if event.type == KEYUP and event.key == K_F1 and self.started:
                music_playing = not music_playing
                if music_playing:
                    p.mixer.music.pause()
                else:
                    p.mixer.music.play(-1, 0.0)
            if event.type == KEYUP and event.key == K_F2:
                num = len(os.listdir('../run/screenshots')) + 1
                name = f'screenshot{num}'
                p.image.save(self.screen, '../run/screenshots/%s.png' % (name))
                alert('Screenshot saved as %s.png' % (name))
            if event.type == KEYUP and event.key == K_F6:
                self.Send({'action':'F6'})
            if event.type == KEYUP and event.key == K_F10:
                hack(self)
            if event.type == KEYUP and event.key == K_F3:
                self.F3 = not self.F3
            if event.type == KEYUP and event.key == K_F8:
                self.Send({'action':'startgame'})  # Cheaty way to start the server before everyone's ready
            if event.type == MOUSEMOTION:
                self.mouseX = event.pos[0]
                self.mouseY = event.pos[1]
            if event.type == MOUSEBUTTONUP:
                if self.dropdown_rect.collidepoint(event.pos):
                    self.dropdown_open = not self.dropdown_open
                else:
                    self.dropdown_open = False
        _keys = p.key.get_pressed()
        keys = []
        for i in range(len(list(_keys))):
            keys.append(_keys[i])
        mouse = list(p.mouse.get_pos())
        mouse_click = p.mouse.get_pressed()
        mouse.append(mouse_click[0])
        mouse.append(mouse_click[1])
        mouse.append(mouse_click[2])

        self.Send({'action': 'keys', 'keys': keys, 'mouse':mouse})

        self.screen.blit(self.last_frame, (0, 0))
        pygame.display.flip()

        fps = self.clock.get_fps()
        self.Send({'action':'fps', 'fps':fps})
        self.clock.tick(self.fps_expected)
        pygame.display.set_caption("VillageWars " + self.version + " fps: " + str(fps))        
        
                
    #####################################
    ### Client-side Network functions ###
    #####################################
    """
    Each one of these "Network_" functions defines a command
    that the server will tell you (the client) to do.
    """
    def Network_hack_fail(self, data):
        print('Exception:', data['msg'])

    def Network_gamemode(self, data):
        self.gamemode = data['gamemode']
        
    def Network_receive(self, data):
        self.diconnected = 0
        self._connected = True
        self.fps_expected = 30
        for i in data['data']:
            exec('self.Network_' + i['action'] + '(i)')
        self.Network_flip(data)
    

    def Network_fall(self, data):
        self.Setting = self.no_walls_setting
        p.mixer.music.stop()
        p.mixer.music.load('../assets/sfx/villageLoop.mp3')
        global music_playing
        if music_playing:
            p.mixer.music.play(-1, 0.0)

    def Network_achievement(self, data):
        self.achievement = [120, data['type']]

    def Network_flip(self, data):
        self.toDraw.clear()
        self.toDraw.extend(self.toDrawNext)
        self.toDrawNext.clear()
        self.last_frame.fill((255,255,255))
        for image in self.toDraw:
            self.last_frame.blit(image[0], image[1])
        
    def Network_draw_setting(self, data):
        self.toDrawNext.append([self.Setting, data['coords']])

        
    def Network_draw_lobby_background(self, data):
        self.toDrawNext.append([self.Setting, data['coords']])
        image = self.crate
        for i in range(1000//50):
            rect = image.get_rect(center=(data['x'] + i*50, data['y']))
            self.toDrawNext.append([image, rect])
        for i in range(1000//50):
            rect = image.get_rect(center=(data['x'] + i*50, data['y'] + 650))
            self.toDrawNext.append([image, rect])
        for i in range(700//50):
            rect = image.get_rect(center=(data['x'], data['y'] + i*50))
            self.toDrawNext.append([image, rect])
        for i in range(700//50):
            rect = image.get_rect(center=(data['x'] + 1000, data['y'] + i*50))
            self.toDrawNext.append([image, rect])
        image = p.Surface((500, 100), SRCALPHA)
        
        rect = image.get_rect(center=(data['x']+500, data['y']+500))
        if rect.collidepoint((500,325)):
            image.fill((200,200,250,128))
            if not self.ready:
                self.ready = True
                self.Send({'action':'ready', 'ready':self.ready})
        else:
            image.fill((0,0,200,128))
            if self.ready:
                self.ready = False
                self.Send({'action':'ready', 'ready':self.ready})
        self.toDrawNext.append([image, rect])

    def Network_draw_background(self, data):
        self.toDrawNext.append([self.ocean_pics[self.ocean_frame], (0, 0)])
        self.ocean_frame += 1
        self.ocean_frame %= 40

    def Network_preview(self, data):

        if not data['ArcheryTower?']:
            image = self.house
            rect = image.get_rect(center=(500, 185))
            cage = self.preview

            cage = p.transform.scale(cage, data['dimensions'])
            cage_rect = cage.get_rect(midtop=rect.midtop)
            self.toDrawNext.append([cage, cage_rect])
        else:
            cage = p.transform.scale(self.preview, (360, 360))
            cage_rect = cage.get_rect(center=(500, 85))
            self.toDrawNext.append([cage, cage_rect])


    def Network_draw_avatar(self, data):
        avatar_pic = self.players[data['skin']][0]
        avatar_rect = avatar_pic.get_rect(center=data['coords'])
        avatar_pic, avatar_rect = t.rotate(avatar_pic, avatar_rect, data.get('angle', 0))
        self.toDrawNext.append([avatar_pic, avatar_rect])

        text = self.medium_font.render(data['username'], True, data['color'])
        text_rect = text.get_rect(midbottom = avatar_rect.midtop)
        text_rect.y -= 4
        self.toDrawNext.append([text, text_rect])        

    def Network_victory(self, data):
        p.mixer.music.stop()
        victory = p.mixer.Sound('../assets/sfx/victory.mp3')
        victory.play()

    def Network_animation(self, data):
        image = self.animations[data['name']][data['frame']]
        rect = image.get_rect(center=data['coords'])
        self.toDrawNext.append((image, rect))

    def Network_congrats(self, data):
        screen = p.Surface((1000, 650))
        screen.fill((255,255,0))
        self.toDrawNext.append([screen, (0, 0)])
        if data['color'] == (255,255,0): data['color'] = (0,0,0)
        name = self.large_font.render('You won the game!', True, data['color'])
        text_rect = name.get_rect(midtop=(500, 30))
        self.toDrawNext.append([name, text_rect])

        name = self.medium_font.render('Kills: ' + str(data['kills']), True, (0,0,0))
        text_rect = name.get_rect(topleft=(400, 200))
        self.toDrawNext.append([name, text_rect])
        name = self.medium_font.render('Eliminations: ' + str(data['eliminations']), True, (0,0,0))
        text_rect = name.get_rect(topleft=(400, 320))
        self.toDrawNext.append([name, text_rect])
        name = self.medium_font.render('Buildings Destroyed: ' + str(data['destroyed']), True, (0,0,0))
        text_rect = name.get_rect(topleft=(400, 440))
        self.toDrawNext.append([name, text_rect])
        name = self.medium_font.render('Deaths: ' + str(data['deaths']), True, (255,0,0))
        text_rect = name.get_rect(topleft=(400, 560))
        self.toDrawNext.append([name, text_rect])

        keys = p.key.get_pressed()
        if keys[K_ESCAPE]:
            global running
            running = False

    def Network_end(self, data):
        p.mixer.music.stop()
        screen = p.Surface((1000, 650))
        screen.fill((128, 128, 128))
        self.toDrawNext.append([screen, (0, 0)])
        name = self.large_font.render(data['winner'] + ' won the game.', True, (0,0,0))
        text_rect = name.get_rect(midtop=(500, 30))
        self.toDrawNext.append([name, text_rect])

        name = self.medium_font.render('Kills: ' + str(data['kills']), True, (0,0,0))
        text_rect = name.get_rect(topleft=(400, 200))
        self.toDrawNext.append([name, text_rect])
        name = self.medium_font.render('Eliminations: ' + str(data['eliminations']), True, (0,0,0))
        text_rect = name.get_rect(topleft=(400, 320))
        self.toDrawNext.append([name, text_rect])
        name = self.medium_font.render('Buildings Destroyed: ' + str(data['destroyed']), True, (0,0,0))
        text_rect = name.get_rect(topleft=(400, 440))
        self.toDrawNext.append([name, text_rect])
        name = self.medium_font.render('Deaths: ' + str(data['deaths']), True, (255,0,0))
        text_rect = name.get_rect(topleft=(400, 560))
        self.toDrawNext.append([name, text_rect])
        
    def Network_ingame(self, data):
        self.toDrawNext.append([self.Setting, data['coords']])

    def Network_music_change(self, data):
        p.mixer.music.stop()
        p.mixer.music.load(self.musics[data['music']])
        global music_playing
        if music_playing:
            p.mixer.music.play(-1, 0.0)


    def Network_draw_barbarian(self, data):
        if self.F3 and not data['type'] == 'leader':
            image = self.barbarian_range
            rect = image.get_rect(center=data['coords'])
            self.toDrawNext.insert(6, (image, rect))
        
        image = self.barbarians[data['type']][bool(data['hurt'])]
        rect = image.get_rect(center=data['coords'])
        image, rect = t.rotate(image, rect, data['angle'])

        if data['type'] == 'leader':
            banner = self.barbarian_banner
            banner_rect = banner.get_rect(bottomleft=rect.center)
            self.toDrawNext.append((banner, banner_rect))
        
        self.toDrawNext.append((image, rect))

        username_text = self.small_font.render('Barbarian ' + data['type'].title(), True, (0,0,0))
        text_rect = username_text.get_rect(midbottom = (rect.midtop[0], rect.midtop[1] - 15))
        self.toDrawNext.append([username_text, text_rect])


        if data['shield'] != None:
            image = self.shield
            rect = image.get_rect(center=data['coords'])
            image, rect = t.rotate(image, rect, data['shield'])
            self.toDrawNext.append((image, rect))
            
        

        
        health_bar = p.Surface((50, 10))
        health_bar.fill((255, 0, 0))
        health_rect = health_bar.get_rect(midbottom=rect.midtop)
        
        green_bar = p.Surface((int(data['health']/2), 10))
        green_bar.fill((0,255,0))
        health_bar.blit(green_bar, (0, 0))
        
        self.toDrawNext.append([health_bar, health_rect])

    def Network_hud(self, data):
        gold = self.medium_font.render('Gold: ' + str(data['gold']), True, (255,205,0))
        gold_rect = gold.get_rect(topright = (950,260))
        self.toDrawNext.append([gold, gold_rect])
            
        food = self.medium_font.render('Food: ' + str(data['food']), True, (5,255,5))
        food_rect = food.get_rect(topright = (950,300))
        self.toDrawNext.append([food, food_rect])

        if self.F3:
            x = round(data['x'])
            y = round(data['y'])
            coords = self.medium_font.render('x=' + str(x) + ', y=' + str(y), True, (0,0,0))
            coords_rect = coords.get_rect(topleft = (50,100))
            self.toDrawNext.append([coords, coords_rect])
            if x > 3000:
                if y > 1950:
                    q = 'Bottom-right'
                else:
                    q = 'Top-right'
            else:
                if y > 1950:
                    q = 'Bottom-left'
                else:
                    q = 'Top-left'
            coords = self.medium_font.render('Quadrant: ' + q, True, (0,0,0))
            coords_rect = coords.get_rect(topleft = (50,130))
            self.toDrawNext.append([coords, coords_rect])
            if -45 <= data['angle'] <= 45:
                d = 'East (towards positive x)'
            elif 45 <= data['angle'] <= 135:
                d = 'North (towards negative y)'
            elif -135 <= data['angle'] <= -45:
                d = 'South (towards positive y)'
            elif -135 >= data['angle'] or data['angle'] >= 135:
                d = 'West (towards negative x)'

            text = self.medium_font.render('Facing: ' + d, True, (0,0,0))
            text_rect = text.get_rect(topleft = (50,160))
            self.toDrawNext.append([text, text_rect])

            gametime = data.get('gametime')
            if gametime:
                gametime = round(gametime)
                seconds = gametime % 60 + 1
                minutes = gametime // 60
                if seconds == 60:
                    seconds = 0
                    minutes += 1
                if minutes > 0 and seconds > 9:
                    gametime = str(minutes) + ':' + str(seconds)
                elif seconds > 9:
                    gametime = str(seconds)
                else:
                    if minutes > 0:
                        gametime = str(minutes) + ':' + '0' + str(seconds)
                    else:
                        gametime = str(seconds)
                text = self.medium_font.render('Game Time: ' + gametime, True, (0,0,0))
                text_rect = text.get_rect(topleft = (50,190))
                self.toDrawNext.append([text, text_rect])

            fps = self.clock.get_fps()
            text = self.medium_font.render('FPS: ' + str(fps), True, (0,0,0))
            text_rect = text.get_rect(topleft = (50,220))
            self.toDrawNext.append([text, text_rect])

        if data['food?']:
            image = self.meals[data['type']]
        else:
            image = self.plate

        mouse = p.mouse.get_pos()

        rect = image.get_rect(center=(890, 130))
        if rect.collidepoint(mouse) and image != self.plate:
            image = p.transform.scale(image, (110, 110))
            rect = image.get_rect(center=(890, 130))
            pressed = p.mouse.get_pressed()
            if pressed[0]:
                self.Send({'action':'eat'})

        self.toDrawNext.append([image, rect])

        
        
        if data['crates'] > 0:
            text = self.medium_font.render('x ' + str(data['crates']), True, (0,0,0))
            text_rect = text.get_rect(midleft=(940, 20))
            self.toDrawNext.append([text, text_rect])
            self.toDrawNext.append([p.transform.scale(self.crate, (30, 30)), (900, 5)])

            
        
        if data['spiky_bushes'] > 0:
            text = self.medium_font.render('x ' + str(data['spiky_bushes']), True, (0,0,0))
            text_rect = text.get_rect(midleft=(940, 75))
            self.toDrawNext.append([text, text_rect])
            self.toDrawNext.append([p.transform.scale(self.spiky_bush, (30, 30)), (900, 60)])

    def Network_draw_player(self, data):
        global cursor
        cursor = p.cursors.Cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
        if data.get('in_barrel', (0,False))[1]:
            if data['in_barrel'][0] == True:
                
                image = self.players[data['skin']][data['hurt']]
                rect = image.get_rect(center=(data['coords']))
                image, rect = t.rotate(image, rect, data['angle'])
                self.toDrawNext.append([image, rect])
                image = self.barrel_broken
            elif data['in_barrel'][0] == False:
                image = self.barrel
            else:
                image = self.barrel_tnt
            rect = image.get_rect(center=(data['coords']))
        else:
            image = self.players[data['skin']][data['hurt']]
            rect = image.get_rect(center=(data['coords']))
            image, rect = t.rotate(image, rect, data['angle'])
        self.toDrawNext.append([image, rect])

        username_text = self.small_font.render(data['username'], True, data['color'])
        text_rect = username_text.get_rect(midbottom = (rect.midtop[0], rect.midtop[1] - 15))
        if not data.get('in_barrel', False)[1]:
            
            self.toDrawNext.append([username_text, text_rect])

            
            health_bar = p.Surface((int(data['max_health'] / 2), 10))
            health_bar.fill((255, 0, 0))
            health_rect = health_bar.get_rect(midbottom=rect.midtop)
            
            green_bar = p.Surface((int(data['health']/2), 10))
            green_bar.fill((0,255,0))
            health_bar.blit(green_bar, (0, 0))
            
            self.toDrawNext.append([health_bar, health_rect])
            
            if data['shield'] != None:
                image = self.shield
                rect = image.get_rect(center=data['coords'])
                image, rect = t.rotate(image, rect, data['shield'])
                self.toDrawNext.append((image, rect))

        if self.F3:
            health = self.small_font.render(str(data['health']) + '/' + str(data['max_health']), True, (240,240,240))
            text_rect = health.get_rect(midbottom = (text_rect.midtop[0], text_rect.midtop[1] - 4))
            self.toDrawNext.append([health, text_rect])

        

        


    def Network_draw_NPC(self, data):
        if data['image'] == 'farmer':
            image = self.farmer
            name = 'Farmer'
        elif data['image'] == 'miner':
            image = self.miner
            name = 'Miner'
        rect = image.get_rect(center=(data['coords']))
        image, rect = t.rotate(image, rect, data['angle'])
        self.toDrawNext.append([image, rect])


        
        username_text = self.small_font.render(name, True, data['color'])
        text_rect = username_text.get_rect(midbottom = (rect.midtop[0], rect.midtop[1] - 15))
        self.toDrawNext.append([username_text, text_rect])

        status_text = self.small_font.render(data['status'], True, (0,0,0))
        text_rect = status_text.get_rect(midbottom = (rect.midtop[0], rect.midtop[1] + 5))
        self.toDrawNext.append([status_text, text_rect])

    def Network_draw_InnPC(self, data):
        
        image = self.players[0][0]
        rect = image.get_rect(center=(data['coords']))
        image, rect = t.rotate(image, rect, data['angle'])
        self.toDrawNext.append([image, rect])
        
        username_text = self.small_font.render(data['type'], True, data['color'])
        text_rect = username_text.get_rect(midbottom = (rect.midtop[0], rect.midtop[1] - 15))
        self.toDrawNext.append([username_text, text_rect])

        health_bar = p.Surface((50, 10))
        health_bar.fill((255,0,0))
        health_rect = health_bar.get_rect(midbottom=rect.midtop)
        
        green_bar = p.Surface((round(data['health'] / 2), 10))
        green_bar.fill((0,255,0))
        health_bar.blit(green_bar, (0, 0))
        
        self.toDrawNext.append([health_bar, health_rect])
    def Network_draw_robot(self, data):
        if data['image'] == 'regular':
            image = self.robot
        elif data['image'] == 'hurt':
            image = self.robot_hurt
        
        rect = image.get_rect(center=(data['coords']))
        image, rect = t.rotate(image, rect, data['angle'])
        self.toDrawNext.append([image, rect])


        
        username_text = self.small_font.render(data['name'], True, data['color'])
        text_rect = username_text.get_rect(midbottom = (rect.midtop[0], rect.midtop[1] - 15))
        self.toDrawNext.append([username_text, text_rect])


        health_bar = p.Surface((50, 10))
        health_bar.fill((255,0,0))
        health_rect = health_bar.get_rect(midbottom=rect.midtop)
        
        green_bar = p.Surface((round(data['health'] / 2), 10))
        green_bar.fill((0,255,0))
        health_bar.blit(green_bar, (0, 0))
        
        self.toDrawNext.append([health_bar, health_rect])


    def Network_draw_farm(self, data):
        if data['state'] == 'good':
            image = self.food_image
        elif data['state'] == 'mine':
            image = self.food_mine
        else:
            image = self.food_used
        self.toDrawNext.append([image, data['coords']])

    def Network_draw_gold(self, data):
        image = None
        if data['state'] == 'good':
            image = self.gold_image
        elif data['state'] == 'mine':
            image = self.gold_mine
        if image != None:
            self.toDrawNext.append([image, data['coords']])

    def Network_draw_mine(self, data):
        image = self.mine
        if data['right'] == True:
            image = p.transform.flip(image, True, False)
        self.toDrawNext.append([image, data['coords']])
    

    def Network_draw_balloon(self, data):
        image_id = data.get('id', 'default')
        if image_id == 0:
            image = self.balloon
        if image_id == 1:
            image = self.op_balloon
        if image_id == 2:
            image = self.speedy_balloon
        if image_id == 3:
            image = self.speedy_plus_op
        if image_id == 4:
            image = self.bolt
        rect = image.get_rect(center=(data['coords']))
        image, rect = t.rotate(image, rect, data['angle'])
        self.toDrawNext.append([image, rect])

        
    def Network_draw_building(self, data):
        
        if data['image'] == 'house':
            if data['state'] == 'alive':
                image = self.house
            else:
                image = self.house_burnt
        rect = image.get_rect(center=data['coords'])
        

        color = tuple(data['color'])
        if color == (255,0,0):
            cage = self.red
        elif color == (0,255,0):
            cage = self.green
        elif color == (0,0,255):
            cage = self.blue
        elif color == (255,255,0):
            cage = self.yellow
        elif color == (0,0,0):
            cage = self.black
        

        cage = p.transform.scale(cage, data['dimensions'])
        cage_rect = cage.get_rect(midtop=rect.midtop)
        self.toDrawNext.append([cage, cage_rect])

        self.toDrawNext.append([image, rect])

        if data['state'] == 'alive':
            person = self.building_person
            person_rect = image.get_rect(midtop=(rect.midbottom[0], rect.midbottom[1] + 50))
            person, person_rect = t.rotate(person, person_rect, data['angle'])

            self.toDrawNext.append([person, person_rect])

            name = self.small_font.render(data['type'], True, data['color'])
            text_rect = name.get_rect(midbottom = (person_rect.midtop[0], person_rect.midtop[1] - 30))
            self.toDrawNext.append([name, text_rect])

            name = self.small_font.render('(Level ' + str(data['level']) + ')', True, data['color'])
            text_rect = name.get_rect(midbottom = (person_rect.midtop[0], person_rect.midtop[1] - 15))
            self.toDrawNext.append([name, text_rect])

            health_bar = p.Surface((int(data['max_health'] / 2), 10))
            health_bar.fill((255, 0, 0))
            health_rect = health_bar.get_rect(midbottom=person_rect.midtop)
            
            green_bar = p.Surface((int(data['health'] / 2), 10))
            green_bar.fill((0,255,0))
            health_bar.blit(green_bar, (0, 0))
            
            self.toDrawNext.append([health_bar, health_rect])

    def Network_archery_tower(self, data):
        

        color = tuple(data['color'])
        if color == (255,0,0):
            cage = self.red
        elif color == (0,255,0):
            cage = self.green
        elif color == (0,0,255):
            cage = self.blue
        elif color == (255,255,0):
            cage = self.yellow
        elif color == (0,0,0):
            cage = self.black

        cage = p.transform.scale(cage, (360, 360))
        cage_rect = cage.get_rect(center=data['coords'])
        self.toDrawNext.append([cage, cage_rect])

        
        
        person = self.archer
        person_rect = person.get_rect(midtop=(data['coords']))
        person, person_rect = t.rotate(person, person_rect, data['angle'])
        if data['state'] == 'alive':
            self.toDrawNext.append([person, person_rect])

        if data['state'] == 'alive':
            name = self.small_font.render('Archery Tower', True, data['color'])
        else:
            name = self.small_font.render('Archery Tower (Broken)', True, data['color'])
        text_rect = name.get_rect(midbottom = (person_rect.midtop[0], person_rect.midtop[1] - 15))
        self.toDrawNext.append([name, text_rect])

        if data['state'] == 'alive':
            health_bar = p.Surface((150, 10))
            health_rect = health_bar.get_rect(midbottom=person_rect.midtop)
            health_bar.fill((255,0,0))
            
            green_bar = p.Surface((int(data['health']/2), 10))
            green_bar.fill((0,255,0))
            health_bar.blit(green_bar, (0, 0))
            
            self.toDrawNext.append([health_bar, health_rect])

    def Network_sound(self, data):
        if data['sound'] == 'TNT':
            self.sound_be.play()
        if data['sound'] == 'shot':
            self.sound_shot.play()
        if data['sound'] == 'die':
            self.sound_se.play()
        if data['sound'] == 'splash':
            self.sound_sp.play()
        if data['sound'] == 'opsplash':
            self.sound_sh.play()
        if data['sound'] == 'bump':
            self.sound_bump.play()
        if data['sound'] == 'building':
            self.sound_bb.play()
        if data['sound'] == 'ow':
            self.sound_ow.play()
        if data['sound'] == 'cw':
            self.sound_cw.play()
        if data['sound'] == 'barrel':
            self.sound_ba.play()


    def Network_num_buildings(self, data):
        y = 500
        x = 990
        for user in data['users']:
            username = self.small_font.render(user['name'] + ' has ' + str(user['bs']) + ' buildings.', True, user['color'])
            text_rect = username.get_rect(topright=(x, y+user['num']*30))
            self.toDrawNext.append([username, text_rect])
    

    def Network_chat(self, data):
        y = 20
        for message in reversed(data['messages']):
            color = list(message['color'])
            m = self.medium_font.render(message['message'], True, color)
            m.set_alpha(message['fade'])
            text_rect = m.get_rect(topleft=(20, y))
            self.toDrawNext.append([m, text_rect])
            y += 30

    def Network_startgame(self, data):
        p.mixer.music.stop()
        p.mixer.music.load('../assets/sfx/stepPebblesLoop.mp3')
        self.started = True
        global music_playing
        if music_playing:
            p.mixer.music.play(-1, 0.00)

    def Network_text(self, data):

        if data['text']:
            name = self.medium_font.render(data['text'], True, (0,0,255))
        else:
            if self.tips[self.tip].startswith('+'):
                name = self.medium_font.render('TIP: ' + self.tips[self.tip][1:], True, (255,0,128))
            else:
                name = self.medium_font.render('TIP: ' + self.tips[self.tip], True, (255,205,0))            
        text_rect = name.get_rect(midbottom=(500, 500))
        self.toDrawNext.append([name, text_rect])
    
    

    def Network_time(self, data):
        text = self.medium_font.render(data['time'], True, (0,0,0))
        text_rect = text.get_rect(midbottom=(500, 640))
        self.toDrawNext.append([text, text_rect])

    def Network_draw_obstacle(self, data):
        if data['image'] == 'tree':
            image = self.tree
        if data['image'] == 'sappling':
            image = self.sappling
        if data['image'] == 'crate':
            image = self.crate
        if data['image'] == 'vine':
            image = self.vine
        if data['image'] == 'gate':
            if data['rotated?']:
                image = p.transform.rotate(self.gate, 90)
            else:
                image = self.gate
        if data['image'] == 'spiky bush':
            image = self.spiky_bush
        if data['image'] == 'TNT':
            image = self.tnt
        if data['image'] == 'barrel':
            image = self.barrel_broken if data['max_health'] / (1+data['health']) > 2 else self.barrel
            if data.get('explosive', False):
                image = self.barrel_tnt
            

        rect = image.get_rect(center=data['coords'])
        image, rect = t.rotate(image, rect, data.get('angle', 0))
        self.toDrawNext.append([image, rect])

        if data['image'] not in ('barrel', 'crate', 'gate', 'TNT', 'spiky bush', 'sappling'):
            health_bar = p.Surface((int(data['max_health']/2), 12))
            health_bar.fill((255, 0, 0))
            health_rect = health_bar.get_rect(midbottom=rect.midtop)
        
            green_bar = p.Surface((int(data['health']/2), 12))
        
            green_bar.fill((0,255,0))
            health_bar.blit(green_bar, (0, 0))
        
            self.toDrawNext.append([health_bar, health_rect])

    def Network_draw_window(self, data):
        grey = p.Surface((610, 618))
        large_rect = grey.get_rect(topleft=(195, 4))
        grey.fill((128,128,128))
        self.toDrawNext.append([grey, large_rect])

        if large_rect.collidepoint(p.mouse.get_pos()):
            global cursor
            cursor = p.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW)

        dark_grey = p.Surface((600, 606))
        rect = dark_grey.get_rect(topleft=(200, 10))
        dark_grey.fill((95,95,95))
        self.toDrawNext.append([dark_grey, rect])

        x = 200
        y = 200

        info = self.small_fantasy_font.render(data['window']['info'][0], True, (0,0,0))
        text_rect = info.get_rect(topleft=(210,30))
        self.toDrawNext.append([info, text_rect])
        info = self.small_fantasy_font.render(data['window']['info'][1], True, (0,0,0))
        text_rect = info.get_rect(topleft=(210,55))
        self.toDrawNext.append([info, text_rect])

        info = self.small_font.render('Owner:', True, (255,0,255))
        text_rect = info.get_rect(topleft=(210,90))
        self.toDrawNext.append([info, text_rect])
        info = self.small_font.render('Health:', True, (255,0,255))
        text_rect = info.get_rect(topleft=(210,110))
        self.toDrawNext.append([info, text_rect])
        info = self.small_font.render('Level:', True, (255,0,255))
        text_rect = info.get_rect(topleft=(210,130))
        self.toDrawNext.append([info, text_rect])
        info = self.small_font.render(data['window']['4th_info'][0] + ':', True, (255,0,255))
        big_text_rect = info.get_rect(topleft=(210,150))
        self.toDrawNext.append([info, big_text_rect])
        right = big_text_rect.topright[0] + 30

        info = self.small_font.render(data['window']['owner'], True, data['window']['color'])
        text_rect = info.get_rect(topleft=(right,90))
        self.toDrawNext.append([info, text_rect])

        info = self.small_font.render(str(data['window']['health'][0]) + '/' + str(data['window']['health'][1]), True, (0,0,0))
        text_rect = info.get_rect(topleft=(right,110))
        self.toDrawNext.append([info, text_rect])

        info = self.small_font.render(str(data['window']['level']), True, (0,0,0))
        text_rect = info.get_rect(topleft=(right,130))
        self.toDrawNext.append([info, text_rect])

        info = self.small_font.render(data['window']['4th_info'][1], True, (0,0,0))
        text_rect = info.get_rect(topleft=(right,150))
        self.toDrawNext.append([info, text_rect])

        for Y in range(len(data['window']['options'])):
            black = p.Surface((600, 2))
            black_rect = black.get_rect(topleft=(200,y+Y*40))
            grey = p.Surface((600, 44))
            rect = grey.get_rect(topleft=(200, y+Y*40))
            grey.fill((155,155,155))
            mouse = p.mouse.get_pos()
            if rect.collidepoint(mouse):
                grey.fill((250, 250, 255))
            self.toDrawNext.append([grey, rect])
            self.toDrawNext.append([black, black_rect])

            name = self.medium_font.render(data['window']['options'][Y], True, (0,0,0))
            text_rect = name.get_rect(midtop=(500, y+Y*40+5))
            self.toDrawNext.append([name, text_rect])


    def Network_draw_innpc_window(self, data):
        grey = p.Surface((610, 618))
        large_rect = grey.get_rect(topleft=(195, 4))
        grey.fill((128,128,128))
        self.toDrawNext.append([grey, large_rect])

        dark_grey = p.Surface((600, 606))
        rect = dark_grey.get_rect(topleft=(200, 10))
        dark_grey.fill((95,95,95))
        self.toDrawNext.append([dark_grey, rect])

        x = 210
        y = 30

        for Y, thing in enumerate(data['window']['info']):
            info = self.small_fantasy_font.render(thing, True, (0,0,0))
            text_rect = info.get_rect(topleft=(x, y + Y*25))
            self.toDrawNext.append([info, text_rect])

        x = 200
        y = 200
        for Y in range(len(data['window']['options'])):
            black = p.Surface((600, 2))
            black_rect = black.get_rect(topleft=(200,y+Y*40))
            grey = p.Surface((600, 44))
            rect = grey.get_rect(topleft=(200, y+Y*40))
            grey.fill((155,155,155))
            mouse = p.mouse.get_pos()
            if rect.collidepoint(mouse):
                grey.fill((250, 250, 255))
            self.toDrawNext.append([grey, rect])
            self.toDrawNext.append([black, black_rect])

            name = self.medium_font.render(data['window']['options'][Y], True, (0,0,0))
            text_rect = name.get_rect(midtop=(500, y+Y*40+5))
            self.toDrawNext.append([name, text_rect])

    def Network_WARNING_outdated_client(self, data):
        info = self.medium_font.render('WARNING: Outdated Client', True, (255,0,0))
        text_rect = info.get_rect(midbottom=(400,600))

        box = p.Surface((text_rect.width + 10, 85))
        box.fill((255,255,255))
        rect = box.get_rect(midbottom=(400, 650))
        self.toDrawNext.append([box, rect])

        self.toDrawNext.append([info, text_rect])
        info = self.medium_font.render('Server: %s - Client: %s' % (data['version'], self.version), True, (255,0,0))
        text_rect = info.get_rect(midbottom=(400,635))
        self.toDrawNext.append([info, text_rect])

    


    def Network_WARNING_outdated_server(self, data):
        info = self.medium_font.render('WARNING: Outdated Server', True, (255,0,0))
        text_rect = info.get_rect(midbottom=(400,600))

        box = p.Surface((text_rect.width + 10, 85))
        box.fill((255,255,255))
        rect = box.get_rect(midbottom=(400, 650))
        self.toDrawNext.append([box, rect])

        self.toDrawNext.append([info, text_rect])
        info = self.medium_font.render('Server: %s - Client: %s' % (data['version'], self.version), True, (255,0,0))
        text_rect = info.get_rect(midbottom=(400,635))
        self.toDrawNext.append([info, text_rect])

        
        

    def Network_display_host(self, data):
        x, y, width, height = 700, 0, 300, 50
        # Check if the dropdown is clicked
        mouse_pos = p.mouse.get_pos()
        mouse = p.mouse.get_pressed()
                
        if self.dropdown_open:
            # Display the dropdown options
            for i, option in enumerate(self.gamemodes):
                option_rect = pygame.Rect(x, y + (height * (i+1)), width, height)
                text_surface = self.medium_font.render(option, True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=option_rect.center)

                surf = p.Surface((width, height), p.SRCALPHA)
                if option_rect.collidepoint(mouse_pos):
                    surf.fill((200,200,200,200))
                else:
                    surf.fill((128,128,128,200))
                self.toDrawNext.append((surf, option_rect))
                self.toDrawNext.append((text_surface, text_rect))

                if option_rect.collidepoint(mouse_pos) and mouse[0]:
                    # Change the selected option
                    self.gamemode = option
                    self.Send({"action": "change_gamemode", "gamemode": self.gamemode})
        
        text_surface = self.medium_font.render(('Gamemode' if self.dropdown_open else self.gamemode), True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.dropdown_rect.center)
        surf = p.Surface((width, height), p.SRCALPHA)
        if self.dropdown_rect.collidepoint(mouse_pos):
            if self.dropdown_open:
                surf.fill((200,200,200))
            else:
                surf.fill((200,200,200,200))
        else:
            if self.dropdown_open:
                surf.fill((128,128,128))
            else:
                surf.fill((128,128,128,200))
            
        self.toDrawNext.append((surf, self.dropdown_rect))
        self.toDrawNext.append((text_surface, text_rect))

        

    def Network_connected(self, data):
        """
        Network_connected runs when you successfully connect to the server
        """
        self.Send({'action':'version', 'version':self.version})
        self.Send({'action':'init', 'username':self.username, 'status':'JG', 'color':self.color, 'skin':self.skin, 'xp':0})
        __main__.stop_loading_circle = True
        print("Joined game")

        p.mixer.music.stop()
    
    def Network_disconnected(self, data):
        """
        Network_disconnected runs when you disconnect from the server
        """
        shut_down()

    def Network_kicked(self, data):
        """
        Network_kicked runs when you are kicked from the server
        """
        shut_down()


def main(screen, username, userInfo, ip, port=5555, musicPlaying=True):
    global running, cursor, music_playing
    running = True
    cursor = p.cursors.Cursor(p.SYSTEM_CURSOR_ARROW)
    music_playing = musicPlaying
    cursor = p.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW)
    if ip.lower() != ip.upper():
        uri = f'wss://{ip}'
    else:
        uri = f'ws://{ip}:{port}'
    client = Client(uri=uri, screen=screen, username=username, color=userInfo['color'], skin=userInfo['skin'])
    while running:
        client.update()
    shut_down()

if __name__ == '__main__':
    print('This program is open in debug mode.')
    conf.init_assets()
    p.init()
    screen = p.display.set_mode((1000, 650))
    username = 'f'
    userInfo = {'color': (0,0,255), 'username': 'f', 'skin': 0}
    ip = '127.0.0.1'
    musicPlaying = True
    main(screen, username, userInfo, ip, musicPlaying=musicPlaying)

















