import shelve
import os
import sys

import requests
import json
import math as m
from time import monotonic, sleep
import random as ran
from progress_bar import InitBar as Bar

import pygame
import threading
import os
import re

import menu

import threading

   
import pygame as p
from pygame.locals import *
from pymsgbox import *
import GameClient

import toolbox
import toolbox as t
import typer
import pyperclip

import logging as log
log.basicConfig(level=log.INFO, format='%(levelname)s - %(message)s')

path = os.path.abspath('.')

if not path.endswith('src'):
    os.chdir('src/')


regex = re.compile(r'(\d)+\.(\d)+\.(\d)+')
__version__ = regex.search(path).group()
print('Running VillageWars version', __version__)


sys.path.append('../../')
from net2web import Client as ParentClient, getmyip


music_playing = True

p.mixer.pre_init(buffer=5)
p.mixer.init()

DOWNLOAD = False
p.font.init()

icon = p.image.load('../assets/Skins/0.png')
skins = [p.transform.scale(p.image.load('../assets/Skins/%s.png' % (i)), (280, 280)) for i in range(len(os.listdir('../assets/Skins')) // 2)]

click_sound = p.mixer.Sound('../assets/sfx/click.wav')

title = p.transform.scale(p.image.load('../assets/title page/attempt 1.png'), (500, 100))
title_rect = title.get_rect(midtop=(500, 30))

SigningIn = p.image.load('../assets/SigningIn.png')
CreatingAcount = p.image.load('../assets/CreatingAcount.png')
Connecting = SigningIn
cursor = p.cursors.Cursor(p.SYSTEM_CURSOR_ARROW)

def get_uns(username):
    font = p.font.SysFont('default', 90)
    return font.render(username, True, (255, 0, 0)), font.render(username, True, (0, 0, 255)), font.render(username, True, (255, 255, 0)), font.render(username, True, (0, 255, 0))




def getScreen(resizable=False):
    p.init()
    if resizable:
        screen = p.display.set_mode((1000, 650), p.RESIZABLE)
    else:
        screen = p.display.set_mode((1000, 650))
    p.display.set_icon(icon)
    clock = p.time.Clock()
    return screen, clock

def loading_circle(screen, clock):
    base_screen = screen.__copy__()
    dark = p.Surface((1000,650))
    dark.set_alpha(50)
    base_screen.blit(dark, (0,0))
    global stop_loading_circle
    stop_loading_circle = False

    circle = p.image.load('../assets/title page/loading.png')
    circle_angle = 0
    circle_speed = 5
    circle_rect = circle.get_rect(center=(500, 325))

    while not stop_loading_circle:
        for ev in pygame.event.get():
            if ev.type == QUIT:
                p.quit()
                sys.exit()
        screen.blit(base_screen, (0,0))

        circle_angle += circle_speed
        circled = p.transform.rotate(circle, circle_angle)
        circle_rect = circled.get_rect(center=circle_rect.center)
        screen.blit(circled, circle_rect)
                    
        p.display.update()
        clock.tick(60)

def logIn(screen, clock, logInType, username, password, name='', email='None'):
    base_screen = screen.__copy__()
    global response_data
    def CheckValidUser(username, password):
        global response_data
        res = requests.get(flask_application + 'get_user/%s/%s' % (username, password))
        res.raise_for_status()
        response_data = res.json()
    def CreateAccount(username, password, name, email):
        global response_data
        res = requests.post(flask_application + 'create', data={'username':username, 'password':password, 'name':name, 'email':str(email)})
        res.raise_for_status()
        response_data = res.json()

    if logInType == 'sign in':
        CheckValidUser(username, password)
    elif logInType == 'sign up':
        CreateAccount(username, password, name, email)
    return response_data



def rand_rgb(r,g,b,rd,gd,bd):
    
    rd += ran.randint(-16,16)/1000
    gd += ran.randint(-16,16)/1000
    bd += ran.randint(-16,16)/1000
    if abs(rd) > 20:
        rd = 0
    if abs(gd) > 20:
        gd = 0
    if abs(bd) > 20:
        bd = 0


    r += rd
    g += gd
    b += bd
    
    if r > 255 or r < 0:
        rd = -rd
        r += rd * 2
    if g > 255 or g < 0:
        gd = -gd
        g += gd * 2
    if b > 255 or b < 0:
        bd = -bd
        b += bd * 2

    return r, g, b, rd, gd, bd

def get_nametag_color(color, username):
    font40 = p.font.SysFont('default', 40)
    font120 = p.font.SysFont('default', 120)
    small = font40.render(username, True, color)
    big = font120.render(username, True, color)

    return small, big
    

def search_servers(screen, choose):
    global INTERNET
    
    
    if INTERNET:
    
        res = requests.post(flask_application + 'scan_for_servers')
        res.raise_for_status()
        
        servers = res.json()['IPs']
        
        
        global server_buttons
        server_buttons = server_surfs(servers, screen, choose)
    else:
        if check_internet(5):
            INTERNET = True
            return search_servers(screen, choose)
        else:
            INTERNET = False
        servers = []
        server_buttons = server_surfs(servers, screen, choose)
    global FOUND_SERVERS
    FOUND_SERVERS = True
    


def server_surfs(IPs, screen, choose_server_rect):
    server_buttons = []

    gray_rectangle = p.Surface((800, 60))
    gray_rectangle.fill((180,180,180))
    gray_rectangle2 = p.Surface((800, 60))
    gray_rectangle2.fill((180,180,240))
    gray_rectangle3 = p.Surface((800, 60))
    gray_rectangle3.fill((175,160,175))
    font_server = p.font.SysFont('default', 50)
    smfont = p.font.SysFont('default', 40)
    
    y = choose_server_rect.bottom + 50
    for server in IPs:
        name = server['name']
        

        ip = server['ip']

        ip_surf = font_server.render(ip, True, (0,0,90))
        ip_surf2 = font_server.render(ip, True, (50,50,50))
        ip_surf3 = font_server.render(ip, True, (0,0,0))
        ip_rect = ip_surf.get_rect(midright=(gray_rectangle.get_width() - 20, gray_rectangle.get_height() // 2))

        name_surf = font_server.render(name, True, (0,0,0))
        name_surf2 = font_server.render(name, True, (30,30,40))
        name_rect = name_surf.get_rect(midleft=(20, gray_rectangle.get_height() // 2))

        if server['started']:
            displayed = 'Game has started'
            gray_rectangle.fill((100,100,100))
            gray_rectangle2.fill((100,100,140))
            gray_rectangle3.fill((85,75,85))
        else:
            displayed = server['gamemode']
            gray_rectangle.fill((180,180,180))
            gray_rectangle2.fill((180,180,240))
            gray_rectangle3.fill((175,160,175))

        r = gray_rectangle.__copy__()
        r2 = gray_rectangle2.__copy__()
        r3 = gray_rectangle3.__copy__()
        
        gamemode_surf = smfont.render(displayed, True, (50,50,199))
        gamemode_rect = gamemode_surf.get_rect(midleft=(name_rect.right + 20, gray_rectangle.get_height() // 2))

        r.blit(ip_surf, ip_rect)
        r2.blit(ip_surf2, ip_rect)
        r3.blit(ip_surf3, ip_rect)

        r.blit(name_surf, name_rect)
        r2.blit(name_surf2, name_rect)
        r3.blit(name_surf, name_rect)

        r.blit(gamemode_surf, gamemode_rect)
        r2.blit(gamemode_surf, gamemode_rect)
        r3.blit(gamemode_surf, gamemode_rect)
        
        button = {
            'button':t.Button.from_surf(screen, r, r2, r3, midtop=(500, y)),
            'ip':ip
            }
        server_buttons.append(button)
        y += 60
    return server_buttons

def loggedIn(screen, clock, port, username, userInfo):
    global FOUND_SERVERS, server_buttons
    color = userInfo['color']
    username_surf_small, username_surf_big = get_nametag_color(color, username)
    skin_num = userInfo['skin']
    skin_original_size = skins[skin_num]
    skins_not = [t.black_and_white(p.transform.scale(skin, (200,200)), change=30) for skin in skins]
    skins_not_not = [t.black_and_white(p.transform.scale(skin, (120,120)), change=20) for skin in skins]
    
    coins = userInfo['coins']

    # State Constants (Local to avoid confusion)
    SPLASH = 'splash'
    PROFILE = 'profile'
    SINGLEPLAYER = 'singleplayer'
    MULTIPLAYER = 'multiplayer'
    CHANGE_COLOR = 'change_color'
    CHANGE_SKIN = 'change_skin'
    CHOOSE_SERVER = 'choose_server'

    state = SPLASH

    multiplayer_button = t.Button(screen, 'multiplayer.png', 'multiplayer_hov.png', 'multiplayer_down.png', 'multiplayer_no.png', midtop=(500, 300))
    singleplayer_button = t.Button(screen, 'singleplayer.png', 'singleplayer_hov.png', 'singleplayer_down.png', 'singleplayer_no.png', off=True, midtop=(500, 200))
    profile_button = t.Button(screen, 'profile.png', 'profile_hov.png', 'profile_down.png', 'profile_no.png', midtop=(500, 400))
    profile_back_button = t.Button(screen, 'back.png', 'back_hov.png', 'back_down.png', midtop=(500, 500))
    change_skin_button = t.Button(screen, 'change skin.png', 'change skin_hov.png', 'change skin_down.png', midtop=(500, 300))
    change_color_button = t.Button(screen, 'change color.png', 'change color_hov.png', 'change color_down.png', midtop=(500, 200))
    skin_back_button = t.Button(screen, 'back.png', 'back_hov.png', 'back_down.png', midbottom=(500, 610))
    color_back_button = t.Button(screen, 'back.png', 'back_hov.png', 'back_down.png', midbottom=(500, 610))
    server_back_button = t.Button(screen, 'back.png', 'back_hov.png', 'back_down.png', midbottom=(500, 620))
    server_refresh_button = t.Button(screen, 'refresh.png', 'refresh_hov.png', 'refresh_down.png', midbottom=(500, 480))
    server_direct_button = t.Button(screen, 'direct.png', 'direct_hov.png', 'direct_down.png', midbottom=(500, 550))

    red = p.Surface((60, 60))
    red.fill((255,0,0))  # Red
    red2 = red.__copy__()
    red2.fill((255,50,50))
    red3 = red.__copy__()
    red3.fill((200,10,10))
    
    blue = p.Surface((60, 60))
    blue.fill((0,0,255))  # Blue
    blue2 = blue.__copy__()
    blue2.fill((50,50,255))
    blue3 = blue.__copy__()
    blue3.fill((10,10,200))
    
    yellow = p.Surface((60, 60))
    yellow.fill((255,255,0))  # Yellow
    yellow2 = yellow.__copy__()
    yellow2.fill((255,255,100))
    yellow3 = yellow.__copy__()
    yellow3.fill((227,227,20))
    
    green = p.Surface((60, 60))
    green.fill((0,255,0))  # Green
    green2 = green.__copy__()
    green2.fill((100,255,100))
    green3 = green.__copy__()
    green3.fill((10,200,10))

    red_button = t.Button.from_surf(screen, red, red2, red3, midtop=(700, 250))
    blue_button = t.Button.from_surf(screen, blue, blue2, blue3, midtop=(760, 250))
    yellow_button = t.Button.from_surf(screen, yellow, yellow2, yellow3, midtop=(820, 250))
    green_button = t.Button.from_surf(screen, green, green2, green3, midtop=(880, 250))
    
    font100 = p.font.SysFont('default', 100)
    font40 = p.font.SysFont('default', 40)
    
    title = font100.render('VillageWars', True, (128,0,128))

    

    fo = open('tips.json', 'r')
    tips = json.loads(fo.read())
    fo.close()
    tip = ran.choice(tips['rare_tips'])
    tip = font40.render(tip, True, (255,205,0))
    tip_rect = tip.get_rect(midbottom=(500, 620))

    choose_server_surf = font100.render('Servers', True, (20,20,20))
    choose_server_rect = choose_server_surf.get_rect(midtop=(500, 50))

    
    

    

    scanning_surf = font40.render('Scanning for servers...', True, (20,20,20))
    scanning_rect = scanning_surf.get_rect(midtop=(500, choose_server_rect.bottom + 50))

    

    r = 10
    g = 10
    b = 20
    rd, gd, bd = 0.3, 0.1, 1

    global stop_loading_circle
    stop_loading_circle = True
    
    while True:
        width, height = screen.get_size()
        
        title_rect = title.get_rect(midtop=(width//2, (10 * (m.sin(monotonic() * 2))) + 30)) # Update title location
        
        mouse = p.mouse.get_pos()
        click = p.mouse.get_pressed()
        for event in pygame.event.get():
            if event.type == QUIT:
                p.quit()
                sys.exit()
                
            if state == SPLASH:
                if multiplayer_button.handle_event(event):
                    state = CHOOSE_SERVER
                    rd, gd, bd = 0.3, 0.1, 0.5
                    FOUND_SERVERS = False
                    thread = threading.Thread(target=search_servers, args=[screen, choose_server_rect])
                    thread.start()
                    
                if singleplayer_button.handle_event(event):
                    pass  # Doesn't do anything (for now)
                if profile_button.handle_event(event):
                    state = PROFILE
                    rd, gd, bd = 0.3, 0.1, 0.5
            if state == PROFILE:
                if profile_back_button.handle_event(event):
                    state = SPLASH
                    rd, gd, bd = 0, 0, 0
                if change_skin_button.handle_event(event):
                    state = CHANGE_SKIN
                    rd, gd, bd = 0.3, 0.1, 0.5
                if change_color_button.handle_event(event):
                    state = CHANGE_COLOR
                    rd, gd, bd = 0.3, 0.1, 0.5
            if state == CHANGE_SKIN:
                if skin_back_button.handle_event(event):
                    state = PROFILE
                    rd, gd, bd = 0.3, 0.1, 0.5
                if event.type == KEYUP and event.key == K_LEFT:
                    skin_num -= 1
                    if skin_num == -1:
                        skin_num = len(skins) - 1
                    skin_original_size = skins[skin_num]
                if event.type == KEYUP and event.key == K_RIGHT:
                    skin_num += 1
                    if skin_num == len(skins):
                        skin_num = 0
                    skin_original_size = skins[skin_num]
            if state == CHANGE_COLOR:
                if color_back_button.handle_event(event):
                    state = PROFILE
                    rd, gd, bd = 0.3, 0.1, 0.5
                if red_button.handle_event(event):
                    color = (255,0,0)
                    username_surf_small, username_surf_big = get_nametag_color(color, username)
                if blue_button.handle_event(event):
                    color = (0,0,255)
                    username_surf_small, username_surf_big = get_nametag_color(color, username)
                if yellow_button.handle_event(event):
                    color = (255,255,0)
                    username_surf_small, username_surf_big = get_nametag_color(color, username)
                if green_button.handle_event(event):
                    color = (0,255,0)
                    username_surf_small, username_surf_big = get_nametag_color(color, username)
            if state == CHOOSE_SERVER:
                if server_back_button.handle_event(event):
                    state = SPLASH
                    rd, gd, bd = 0.3, 0.1, 0.5
                if FOUND_SERVERS:

                    for button in server_buttons:
                        if button['button'].handle_event(event):
                            thread = threading.Thread(target=loading_circle, args=(screen, clock))
                            thread.start()
                            return {'color':color,
                                'skin':skin_num,
                                'coins':coins,
                                'xp':userInfo['xp'],
                                'ip':button['ip']}
                if server_refresh_button.handle_event(event):
                    FOUND_SERVERS = False
                    thread = threading.Thread(target=search_servers, args=[screen, choose_server_rect])
                    thread.start()
                if server_direct_button.handle_event(event):
                    ip = prompt('Enter the server\'s IP address:', title='VillageWars')
                    if ip and ip != 'Cancel':
                        thread = threading.Thread(target=loading_circle, args=(screen, clock))
                        thread.start()
                        return {'color':color,
                                    'skin':skin_num,
                                    'coins':coins,
                                    'xp':userInfo['xp'],
                                    'ip':ip}

        if state == SPLASH:
            r, g, b, rd, gd, bd = rand_rgb(r,g,b,rd,gd,bd)
            screen.fill((50,160,50))
            multiplayer_button.draw()
            singleplayer_button.draw()
            profile_button.draw()

            screen.blit(tip, tip_rect)

            # Skin Displayer
            skin = p.transform.scale(skin_original_size, (100, 100))
            skin_rect = skin.get_rect(center=(140, 325))
            angle = t.getAngle(140, 325, *(p.mouse.get_pos()[:2]))
            skin, skin_rect = t.rotate(skin, skin_rect, angle)
            
            screen.blit(skin, skin_rect)
            screen.blit(title, title_rect)

            username_rect = username_surf_small.get_rect(midbottom=skin_rect.midtop)
            screen.blit(username_surf_small, username_rect)

        if state == CHOOSE_SERVER:

            r, g, b, rd, gd, bd = rand_rgb(r,g,b,rd,gd,bd)
            screen.fill((90,100,255))
            server_back_button.draw()
            server_refresh_button.draw()
            server_direct_button.draw()

            if FOUND_SERVERS:
                for button in server_buttons:
                    button['button'].draw()
            else:
                screen.blit(scanning_surf, scanning_rect)
            

            screen.blit(choose_server_surf, choose_server_rect)
            

        if state == PROFILE:
            r, g, b, rd, gd, bd = rand_rgb(r,g,b,rd,gd,bd)
            screen.fill((r,g,b))
            profile_back_button.draw()
            change_skin_button.draw()
            change_color_button.draw()

            # Skin Displayer
            skin = p.transform.scale(skin_original_size, (100, 100))
            skin_rect = skin.get_rect(center=(140, 325))
            angle = t.getAngle(140, 325, *(p.mouse.get_pos()[:2]))
            skin, skin_rect = t.rotate(skin, skin_rect, angle)
            
            screen.blit(skin, skin_rect)

            username_rect = username_surf_small.get_rect(midbottom=skin_rect.midtop)
            screen.blit(username_surf_small, username_rect)

        if state == CHANGE_COLOR:
            r, g, b, rd, gd, bd = rand_rgb(r,g,b,rd,gd,bd)
            screen.fill((r,g,b))
            color_back_button.draw()

            skin = p.transform.scale(skin_original_size, (300, 300))
            skin_rect = skin.get_rect(center=(400, 325))
            
            screen.blit(skin, skin_rect)

            username_rect = username_surf_big.get_rect(midbottom=skin_rect.midtop)
            screen.blit(username_surf_big, username_rect)

            red_button.draw()
            blue_button.draw()
            yellow_button.draw()
            green_button.draw()

            
            
        if state == CHANGE_SKIN:
            r, g, b, rd, gd, bd = rand_rgb(r,g,b,rd,gd,bd)
            screen.fill((r,g,b))
            skin_back_button.draw()

            

            # Skin Displayer

            if skin_num == 0:
                skin = p.transform.scale(skin_original_size, (300, 300))
                rskin_rect = skin.get_rect(center=(500, 325))
            
                screen.blit(skin, rskin_rect)

                skin_rect = skins_not_not[3].get_rect(center=(40, 325))
                screen.blit(skins_not_not[3], skin_rect)

                skin_rect = skins_not[4].get_rect(center=(220, 325))
                screen.blit(skins_not[4], skin_rect)

                skin_rect = skins_not[1].get_rect(center=(780, 325))
                screen.blit(skins_not[1], skin_rect)

                skin_rect = skins_not_not[2].get_rect(center=(960, 325))
                screen.blit(skins_not_not[2], skin_rect)

            if skin_num == 1:
                skin = p.transform.scale(skin_original_size, (300, 300))
                rskin_rect = skin.get_rect(center=(500, 325))
            
                screen.blit(skin, rskin_rect)

                skin_rect = skins_not_not[4].get_rect(center=(40, 325))
                screen.blit(skins_not_not[4], skin_rect)

                skin_rect = skins_not[0].get_rect(center=(220, 325))
                screen.blit(skins_not[0], skin_rect)

                skin_rect = skins_not[2].get_rect(center=(780, 325))
                screen.blit(skins_not[2], skin_rect)

                skin_rect = skins_not_not[3].get_rect(center=(960, 325))
                screen.blit(skins_not_not[3], skin_rect)

            if skin_num == 2:
                skin = p.transform.scale(skin_original_size, (300, 300))
                rskin_rect = skin.get_rect(center=(500, 325))
            
                screen.blit(skin, rskin_rect)

                skin_rect = skins_not_not[0].get_rect(center=(40, 325))
                screen.blit(skins_not_not[0], skin_rect)

                skin_rect = skins_not[1].get_rect(center=(220, 325))
                screen.blit(skins_not[1], skin_rect)

                skin_rect = skins_not[3].get_rect(center=(780, 325))
                screen.blit(skins_not[3], skin_rect)

                skin_rect = skins_not_not[4].get_rect(center=(960, 325))
                screen.blit(skins_not_not[4], skin_rect)

            if skin_num == 3:
                skin = p.transform.scale(skin_original_size, (300, 300))
                rskin_rect = skin.get_rect(center=(500, 325))
            
                screen.blit(skin, rskin_rect)

                skin_rect = skins_not_not[1].get_rect(center=(40, 325))
                screen.blit(skins_not_not[1], skin_rect)

                skin_rect = skins_not[2].get_rect(center=(220, 325))
                screen.blit(skins_not[2], skin_rect)

                skin_rect = skins_not[4].get_rect(center=(780, 325))
                screen.blit(skins_not[4], skin_rect)

                skin_rect = skins_not_not[0].get_rect(center=(960, 325))
                screen.blit(skins_not_not[0], skin_rect)

            if skin_num == 4:
                skin = p.transform.scale(skin_original_size, (300, 300))
                rskin_rect = skin.get_rect(center=(500, 325))
            
                screen.blit(skin, rskin_rect)

                skin_rect = skins_not_not[2].get_rect(center=(40, 325))
                screen.blit(skins_not_not[2], skin_rect)

                skin_rect = skins_not[3].get_rect(center=(220, 325))
                screen.blit(skins_not[3], skin_rect)

                skin_rect = skins_not[0].get_rect(center=(780, 325))
                screen.blit(skins_not[0], skin_rect)

                skin_rect = skins_not_not[1].get_rect(center=(960, 325))
                screen.blit(skins_not_not[1], skin_rect)

            username_rect = username_surf_big.get_rect(midbottom=rskin_rect.midtop)
            screen.blit(username_surf_big, username_rect)
                
            


        p.display.update()
        clock.tick(60)
        p.display.set_caption('VillageWars ' + __version__)
    
    
    return {'color':color,
            'xp':userInfo['xp'],
            'skin':skin_num,
            'coins':userInfo['coins'],
            'ip':ip}
    

def joinGame(screen, clock, ip, port, username, newUserInfo):
    global music_playing
    music_playing = GameClient.main(screen, clock, username, __version__, newUserInfo, ip, port=port, musicPlaying=music_playing)
    if music_playing:
        p.mixer.music.load('../assets/sfx/menu.wav')
        p.mixer.music.play(-1, 0.0)
    


def check_internet(timeout=2):
    try:
        requests.head("http://villagewars.pythonanywhere.com/test_connection", timeout=timeout)
        this = True
    except:
        this = False
    try:
        with open('../../version screenshots/version_info.json', 'r') as data_file:
            version_data = json.loads(data_file.read())
            active = version_data['active']
    except:
        active = '0.0.1'
    if this == True:
        res = requests.get('http://villagewars.pythonanywhere.com/need_version_info/' + active)
        res.raise_for_status()
        if res.json()['need']:
            bar = Bar('Updating Launcher')
            bar(0)
            res = requests.get('http://villagewars.pythonanywhere.com/download_version_info', stream=True)
            res.raise_for_status()
            try:
                download_size = int(res.headers['Content-length'])
            except KeyError:
                download_size = 2048
            downloaded_bytes = 0
            os.makedirs('../../version screenshots', exist_ok=True)
            fo = open('../../version screenshots/version_info.json', 'wb')
            for chunk in res.iter_content(chunk_size=32):
                if chunk: # filter out keep-alive new chunks
                    len_chunk = len(chunk)
                    fo.write(chunk)
                    downloaded_bytes += len_chunk
                    bar(downloaded_bytes/download_size*100)
            fo.close()
            bar(100)
            del bar
            print('Successfully downloaded version information')
    return this

def main():
    screen, clock = getScreen(resizable=False)
    userInfo = {'valid':False}
    while not userInfo['valid']:
        result = menu.runMenu(screen, clock)
        username, password = result['username'], result['password']
        global stop_loading_circle
        stop_loading_circle = False
        circle = threading.Thread(target=loading_circle, args=[screen, clock])
        circle.start()
        if not INTERNET:
            username = 'Guest' + str(ran.randint(1,999)).rjust(3, '0')
            userInfo = {'valid':True,'username':username,'color':(255,0,0),'skin':0,'coins':0,'xp':0}
            alert('We were unable to sign you in. Play local!\n Name: ' + username)
        elif result['create']:
            name, email = result['name'], result['email']
            userInfo = logIn(screen, clock, 'sign up', username, password, name, email=email)
        else:
            userInfo = logIn(screen, clock, 'sign in', username, password)
        if not userInfo['valid']:
            alert(userInfo['message'], title='VillageWars')
            stop_loading_circle = True
    
    newUserInfo = loggedIn(screen, clock, 5555, username, userInfo)
    if not username.startswith('Guest'):
        res = requests.post(flask_application + 'updateUser', data={'username':username, 'color':json.dumps(newUserInfo['color']), 'skin':str(newUserInfo['skin'])})
        res.raise_for_status()
    joinGame(screen, clock, newUserInfo['ip'], 5555, username, newUserInfo)




if __name__ == '__main__':
    if check_internet(5):
        INTERNET = True
    else:
        INTERNET = False
    flask_application = 'http://villagewars.pythonanywhere.com/'
    main()
