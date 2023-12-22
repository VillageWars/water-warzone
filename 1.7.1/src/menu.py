import pygame as p
import shelve
import math as m
import random
import webbrowser
from time import monotonic, sleep
import os
import sys
import pygame
import threading
import os
import re
import json
import zipfile2
import toolbox as t
from typer import Typing
from pygame.locals import *
from pymsgbox import *
import __main__
import requests, bs4

def version_update(screen, clock, active):
    global FINISHED, download_size, downloaded_bytes

    grey_bar = p.Surface((800, 50))
    grey_bar.fill((95, 95, 95))
    grey_bar_rect = grey_bar.get_rect(center=(500, 300))
    blue_bar_pos = grey_bar_rect.topleft
    title = p.transform.scale(p.image.load('../assets/title page/attempt 1.png'), (500, 100))

    fo = open('tips.json', 'r')
    all_tips = json.loads(fo.read())
    fo.close()
    tips = []
    for tip in all_tips['basic_tips']:
        tip = font40.render(tip, True, (255,205,0))
        tip_rect = tip.get_rect(midbottom=(500, 620))
        tips.append((tip, tip_rect))
    for tip in all_tips['rare_tips']:
        tip = font40.render(tip, True, (255,0,128))
        tip_rect = tip.get_rect(midbottom=(500, 620))
        tips.append((tip, tip_rect))
    random.shuffle(tips)
    
    
    while True:        
        try:
            perc = downloaded_bytes/download_size*100
        except NameError:
            perc = 0
            
        title_rect = title.get_rect(midtop=(500, (10 * (m.sin(monotonic() * 2))) + 30)) # Update title location

        for e in p.event.get():
            if e.type == QUIT and confirm('Are you sure you want to cancel this update?', buttons=['Yes', 'No']) == 'Yes':
                p.quit()
                sys.exit()
        screen.fill((255,255,255))

            
        try:
            blue_bar = p.Surface((perc/100*800, 50))
        except:
            blue_bar = p.Surface((0, 50))
        blue_bar.fill((10, 10, 250))

        try:
            out_of = '%s / %s' % (downloaded_bytes, download_size)
        except:
            out_of = '%s / %s' % (0, '?')

            
        screen.blit(title, title_rect)
        screen.blit(grey_bar, blue_bar_pos)
        screen.blit(blue_bar, blue_bar_pos)
        
        perctext = p.font.SysFont('default', 40).render(str(round(perc, 1)) + ' %', True, (255,128,0))
        perctextrect = perctext.get_rect(midtop=(500, 330))
        screen.blit(perctext, perctextrect)
        
        #perctext = p.font.SysFont('default', 30).render(out_of, True, (255,66,66))
        #perctextrect = perctext.get_rect(midtop=(500, 400))
        #screen.blit(perctext, perctextrect)
        
        tip = tips[int((monotonic()/6)%len(tips))]
        screen.blit(tip[0], tip[1])
            
        p.display.set_caption('VillageWars %s --> %s Update:  %s' % (__main__.__version__, active, out_of))

        p.display.update()
        clock.tick(60)

        try:
            if FINISHED:
                alert('Version %s has been installed\nsuccessfuly!' % active, title='VillageWars')
                p.quit()
                import os
                os.chdir('../../%s' % active)
                while not 'main.pyw' in os.listdir():
                    pass
                os.startfile('main.pyw')
                sys.exit()
        except NameError:
            pass
    

def download_active_version(active):
    global zipfile2
    global FINISHED, download_size, downloaded_bytes
    FINISHED = False
    print('Sent files request')
    res = requests.get('http://villagewars.pythonanywhere.com/download_active_version', stream=True)
    res.raise_for_status()
    download_size = int(res.headers['Content-length'])
    downloaded_bytes = 0
    fo = open('../run/downloads/new_version.zip', 'wb')
    for chunk in res.iter_content(chunk_size=2048):
        if chunk: # filter out keep-alive new chunks
            len_chunk = len(chunk)
            fo.write(chunk)
            downloaded_bytes += len_chunk

    fo.close()  # Found commented out, i hope it wasn't important because it crashes the update
    fo = zipfile2.ZipFile('../run/downloads/new_version.zip', 'r')
    
    os.makedirs('../../%s' % active, exist_ok=True)
    fo.extractall('../../%s' % active)
    fo.close()
    FINISHED = True

def load(result):
    href = result['href']
    name = result['name']
    res = requests.get(href)
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    elem = soup.select('.mw-parser-output')[0]
    return name + '\n' + elem.text

def load_results(search):
    results = []
    try:
        res = requests.get('https://villagewars.fandom.com/wiki/Special:Search?query=%s&scope=internal&navigationSearch=true&so=trending' % search)
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        elements = soup.select('.unified-search__result__title')  # All search responses
        results = []
        for elem in elements:
             results.append({'href':elem.get('href'), 'name':elem.get('data-title')})
        global guide_results, scroll
        scroll = 0
        guide_results = True
    except:
        alert('You need to be connected\nto the Internet.', title='VillageWars')
    return results
    
def runMenu(screen, clock):
    global mouse, click, keys, open_menu_surf, open_menu_hover_surf, options, tab, menu_space, font40, creds, font30, scroll, guide_results, carry_to
    active = '0.0.1'

    mouse = p.mouse.get_pos()
    click = p.mouse.get_pressed()
    keys = p.key.get_pressed()
    width, height = screen.get_width(), screen.get_height()
    
    font40 = p.font.SysFont('default', 40)
    font200 = p.font.SysFont('default', 200)
    font30 = p.font.SysFont('default', 30)
    font100 = p.font.SysFont('default', 100)
    title = p.transform.scale(p.image.load('../assets/title page/attempt 1.png'), (500, 100))
    menu_space = 30

    open_menu_surf = p.transform.scale(p.image.load('../assets/title page/open menu.png'), (22, 22))
    open_menu_hover_surf = p.transform.scale(p.image.load('../assets/title page/open menu_hover.png'), (22, 22))

    background = p.image.load('../assets/optional/{}.png'.format(random.randrange(3)))
    background.set_alpha(180)
    background_rect = background.get_rect(topright=(1000,0))

    logIn_button = t.Button(screen, 'title page/log in to play.png', 'title page/log in to play_hover.png', 'title page/log in to play_down.png', midtop=(((width-menu_space)/2) + menu_space, 400))
    #logInToPlay = p.image.load('../assets/title page/log in to play.png')
    #logInToPlay_hover = p.image.load('../assets/title page/log in to play_hover.png')

    #darker_surf = p.image.load('../assets/paused.png')
    #credits_fade = p.image.load('../assets/title page/credits fade.png')

    font80 = p.font.SysFont('default', 80)

    tab = 'Home'
    guide_results = True

    fo = open('splash.txt')
    splash = [s[:-1] for s in fo.readlines()]
    fo.close()
    splash = splash[random.randrange(len(splash))]
    #splash = 'Ha!'
    #print(len(splash))
    splashFont = p.font.SysFont('default', 80-len(splash))
    splash = splashFont.render(splash, True, (250,250,100))

    creds = []
    results = []
    searcher = Typing(block=[])

    scroll = 0

    with open('../../version screenshots/version_info.json', 'r') as data_file:
        version_data = json.loads(data_file.read())
        active = version_data['active']
        version_data = version_data['versions']
    
    mag_glass = p.transform.scale(p.image.load('../assets/title page/search.png'), (30, 30))
    search_activated = False

    release_screenshots = {file[:-4]: p.transform.scale(p.image.load('../../version screenshots/' + file), (250, 162)) for file in os.listdir('../../version screenshots') if file != 'version_info.json'}
    lovable_versions = [folder for folder in os.listdir('../../') if (not folder.endswith('.txt') and '.' in folder and folder in version_data)]
    play_version_buttons = {}
    for version in lovable_versions:
        play_version_buttons[version] = t.Button(screen, 'play version.png', 'play version_hov.png', 'play version_down.png')
    install_version_button = t.Button(screen, 'install_version.png', 'install_version_hov.png', 'install_version_down.png', topleft=(-1000, -650))
    release_screenshots['default'] = p.transform.scale(p.image.load('../run/pre-downloaded/default.png'), (250, 162))

    
    while True:
        options = ['Home', 'Language', 'Statistics', 'Releases', 'Guide', 'Credits', 'Feedback']
        options.remove(tab)
        
        for event in pygame.event.get():
            if event.type == QUIT:
                p.quit()
                sys.exit()
            if tab == 'Guide' and event.type == KEYUP and event.key == K_RETURN and search_activated:
                search = searcher.result
                search_activated = False
                results = load_results(search)
                
            if event.type == KEYUP and event.key == K_F1:
                p.mixer.music.load('../assets/sfx/menu.mp3')
                p.mixer.music.play(-1, 0.0)
            if tab == 'Guide' and event.type in (KEYDOWN, KEYUP) and event.key in (K_RSHIFT, K_LSHIFT):
                searcher.shift()
            if tab == 'Guide' and event.type in (KEYDOWN, KEYUP) and event.key in (K_RCTRL, K_LCTRL):
                searcher.shift()
            if tab == 'Guide' and event.type == KEYUP:
                searcher.type(event)
            if event.type == MOUSEBUTTONDOWN:
                if tab in ('Guide', 'Releases'):
                    if event.button == 5:
                        scroll -= 20
                    elif event.button == 4:
                        if scroll < 0:
                            scroll += 20
            if tab == 'Home' and logIn_button.handle_event(event):
                do_tabs(screen, menu_space)
                result = runLogIn(screen, clock)
                if type(result) == dict:
                    return result
            if tab == 'Releases':# and menu_space == 30:
                for version in play_version_buttons:
                    button = play_version_buttons[version]
                    if button.x != 0 and button.handle_event(event):
                        print(button.rect)
                        os.chdir('../../%s/' % version)
                        print('Hun.', tab, version)
                        try:
                            os.startfile('main.pyw')
                        except:
                            try:
                                os.chdir('src')
                                os.startfile('VillageWarsClient.py')
                            
                            except:
                                if 'src' in os.listdir():
                                    os.chdir('src')
                                
                                os.startfile('SuperShooterWar_startgame.py')
                        p.quit()
                        sys.exit()
                        #alert('Not Implemented.', title='VillageWars')
                if active != __main__.__version__ and install_version_button.handle_event(event):
                    if confirm('A version installation is about to begin. Click OK to start it. This may take several minutes.', title='VillageWars') == 'OK':
                        thread = threading.Thread(target=download_active_version, args=[active])
                        thread.start()
                        version_update(screen, clock, active)
                        lovable_versions = [folder for folder in os.listdir('../../') if (not folder.endswith('.txt') and '.' in folder)]
                        play_version_buttons = {}
                        for version in lovable_versions:
                            play_version_buttons[version] = t.Button(screen, 'play version.png', 'play version_hov.png', 'play version_down.png')
                    
        mouse = p.mouse.get_pos()
        click = p.mouse.get_pressed()
        keys = p.key.get_pressed()
        width, height = screen.get_width(), screen.get_height()

        title_rect = title.get_rect(midtop=(((width-menu_space)/2) + menu_space, (10 * (m.sin(monotonic() * 2))) + 30 + scroll)) # Update title location
        splash_rect = splash.get_rect(midtop=((100 * (m.sin((monotonic()+1) * 2.5))) + ((width-menu_space)/2) + menu_space, 180))
        

        
        if tab == 'Home':
            scroll = 0
            screen.fill((255,255,255))
            screen.blit(background, background_rect)
            screen.blit(title, title_rect)
            screen.blit(splash, splash_rect)
            logIn_button.draw()
            
            #if logIn_rect.collidepoint(mouse):
            #    screen.blit(logInToPlay_hover, logIn_rect)
            #    if click[0]:
                    
            #else:
            #    screen.blit(logInToPlay, logIn_rect)

            
        if tab == 'Language':
            screen.fill((255,255,255))
            text_surf = font40.render('Not Implemented yet.', True, (0,0,0))
            rect = text_surf.get_rect(midtop=((width-menu_space)//2+menu_space, 300 + scroll))
            screen.blit(text_surf, rect)
            
        if tab == 'Statistics':
            screen.fill((255,255,255))
            text_surf = font40.render('Not Implemented yet.', True, (0,0,0))
            rect = text_surf.get_rect(midtop=((width-menu_space)//2+menu_space, 300 + scroll))
            screen.blit(text_surf, rect)
            
        if tab == 'Releases':
            
            screen.fill((20,20,20))
            #screen.blit(title, title_rect)
            y = 100
            
                
            for version in version_data:
                if version == __main__.__version__:
                    text_surf = font40.render('Current version - %s - %s' % (version, version_data[version]['description']), True, (255,0,0))
                    rect = text_surf.get_rect(midtop=((width-menu_space)//2+menu_space, y + scroll))
                    screen.blit(text_surf, rect)
                    y += 50
                    if 'date' in version_data[version]:
                        text_surf = font40.render(version_data[version]['date'], True, (128,128,255))
                        rect = text_surf.get_rect(midtop=((width-menu_space)//2+menu_space, y + scroll))
                        screen.blit(text_surf, rect)
                        y += 40
                    screenshot = release_screenshots.get(version, release_screenshots['default'])
                    rect = screenshot.get_rect(midtop=((width-menu_space)//2+menu_space, y + scroll))
                    screen.blit(screenshot, rect)
                    y += rect.height + 50
                    if carry_to:
                        scroll = (-y) + height // 2 + 200
                        carry_to = False
                    if t.getVersionInt(active) > t.getVersionInt(__main__.__version__):
                        text_surf = font40.render('New updates available below!', True, (255,128,255))
                        rect = text_surf.get_rect(midtop=((width-menu_space)//2+menu_space, y + scroll))
                        screen.blit(text_surf, rect)
                        y += 80
                    
                elif t.getVersionInt(version) > t.getVersionInt(active): #__main__.__version__):
                    text_surf = font40.render('Version %s - %s' % (version, version_data[version]['description']), True, (255,200,200))
                    rect = text_surf.get_rect(midtop=((width-menu_space)//2+menu_space, y + scroll))
                    screen.blit(text_surf, rect)
                    y += 50
                elif t.getVersionInt(version) > t.getVersionInt(__main__.__version__):
                    text_surf = font40.render('Version %s - %s' % (version, version_data[version]['description']), True, (255,255,255))
                    rect = text_surf.get_rect(midtop=((width-menu_space)//2+menu_space, y + scroll))
                    screen.blit(text_surf, rect)
                    y += 50
                    if 'date' in version_data[version]:
                        text_surf = font40.render(version_data[version]['date'], True, (255,128,128))
                        rect = text_surf.get_rect(midtop=((width-menu_space)//2+menu_space, y + scroll))
                        screen.blit(text_surf, rect)
                        y += 40
                    screenshot = release_screenshots.get(version, release_screenshots['default'])
                    rect = screenshot.get_rect(midtop=((width-menu_space)//2+menu_space, y + scroll))
                    screen.blit(screenshot, rect)
                    if version in play_version_buttons:
                        play_version_buttons[version].x = 700
                        play_version_buttons[version].y = y + 50 + scroll
                        play_version_buttons[version].draw()
                    if version == active:
                        install_version_button.x = 700
                        install_version_button.y = y + 50 + scroll
                        install_version_button.draw()
                        
                    
                    y += rect.height + 50
                else:
                    text_surf = font40.render('Version %s - %s' % (version, version_data[version]['description']), True, (255,255,255))
                    rect = text_surf.get_rect(midtop=((width-menu_space)//2+menu_space, y + scroll))
                    screen.blit(text_surf, rect)
                    y += 50
                    if 'date' in version_data[version]:
                        text_surf = font40.render(version_data[version]['date'], True, (128,128,255))
                        rect = text_surf.get_rect(midtop=((width-menu_space)//2+menu_space, y + scroll))
                        screen.blit(text_surf, rect)
                        y += 40
                    screenshot = release_screenshots.get(version, release_screenshots['default'])
                    rect = screenshot.get_rect(midtop=((width-menu_space)//2+menu_space, y + scroll))
                    screen.blit(screenshot, rect)
                    if version in play_version_buttons:
                        play_version_buttons[version].x = 700
                        play_version_buttons[version].y = y + 50 + scroll
                        play_version_buttons[version].draw()
                    y += rect.height + 50
                if version == active:
                    text_surf = font40.render('See below for upcoming releases!', True, (255,128,255))
                    rect = text_surf.get_rect(midtop=((width-menu_space)//2+menu_space, y + scroll))
                    screen.blit(text_surf, rect)
                    y += 80
                    
                #p.draw.rect(install_version_button.rect, (0,255,0))
            
        if tab == 'Guide':
            screen.fill((255,255,255))
            #screen.blit(title, title_rect)

            text_surf = font40.render('This is a work in progress.', True, (0,0,0))
            rect = text_surf.get_rect(midtop=((width-menu_space)//2+menu_space, 100 + scroll))
            screen.blit(text_surf, rect)
            text_surf = font40.render('To view the output better, see villagewars.fandom.com', True, (0,0,0))
            rect = text_surf.get_rect(midtop=((width-menu_space)//2+menu_space, 150 + scroll))
            screen.blit(text_surf, rect)

            if guide_results:
                
                y = 250
                for result in results:
                    text = font40.render(result['name'], True, (60,0,62))
                    rect = text.get_rect(topleft=(250, y + scroll))
                    if rect.collidepoint(mouse):
                        text = font40.render(result['name'], True, (120,0,124))
                        if click[0]:
                            guide_results = False
                            result_text = load(result)
                            results = []

                    screen.blit(text, rect)
                    y += 50
            else:
                y = 300
                for i in result_text.split('\n'):
                    text_surf = font40.render(i, True, (0,0,0))
                    rect = text_surf.get_rect(topleft=(200, y + scroll))
                    screen.blit(text_surf, rect)
                    y += 50

            surf = p.Surface((width, 50))
            surf.fill((200,0,0))
            screen.blit(surf, (0,0))

            surf = p.Surface((width-menu_space-50, 40))
            white_rect = surf.get_rect(topleft=(menu_space + 25, 5))
            if white_rect.collidepoint(mouse):
                if not search_activated:
                    surf.fill((240,240,240))
                else:
                    surf.fill((255,255,255))
                if click[0]:
                    search_activated = True
            else:
                surf.fill((255,255,255))
                if click[0]:
                    search_activated = False
            screen.blit(surf, white_rect)

            mag_rect = mag_glass.get_rect(topleft=(width-65, 10))
            if mag_rect.collidepoint(mouse):
                scaled = p.transform.scale(mag_glass, (35, 35))
                scaled_rect = scaled.get_rect(center=mag_rect.center)
                screen.blit(scaled, scaled_rect)
                if click[0]:
                    search = searcher.result
                    results = load_results(search)
            else:
                screen.blit(mag_glass, mag_rect)

            if search_activated:
                text = font40.render(searcher.text(), True, (0,0,0))
            else:
                if searcher.result:
                    text = font40.render(searcher.result, True, (0,0,0))
                else:
                    text = font40.render('Click here to search', True, (188,188,188))
            rect = text.get_rect(midleft=(white_rect.midleft[0] + 5, white_rect.midleft[1]))
            screen.blit(text, rect)
            
            
            
            
            
        if tab == 'Credits':
            screen.fill((0,0,0))

            
            
            if creds == []:
                Credit.space = 650
                
                creds.append(Credit('- Credits -', creds, font=font200, y=250))
                
                creds.append(Credit('VillageWars', creds, font=font100, y=200))
                
                creds.append(Credit('Creator: Aaron McCormick', creds, font=font40, y=100))
                
                creds.append(Credit('Programming:', creds, font=font40, y=80))

                creds.append(Credit('Surpervisor: Aaron McCormick', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('Game Mechanics (Client + Server): Aaron McCormick', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('Graphical Representation: pygame (module)', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('Windows Messages: pymsgbox (module)', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('Client-Server pumping: PodSixNet (module)', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('Copy and paste with Windows clipboard: pyperclip (module)', creds, font=font40, y=80, rjust=True))

                creds.append(Credit('Graphics:', creds, font=font40, y=80))

                creds.append(Credit('Player Skins, Balloons(+ Water Droplets), Crates, TNT,', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('                            Robots: Codakid Game Dev 2', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('Map, Gates, Buildings, Building Borders: Aaron McCormick', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('Walls, Trees, Spiky Bushes: opengameart.org', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('Barbarians: Aaron McCormick, inspired by skin number 2', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('                                   (Codakid Game Dev 2)', creds, font=font40, y=80, rjust=True))
                creds.append(Credit('Music and Sound Effects:', creds, font=font40, y=80))

                creds.append(Credit('All Sound Effects (splashes, bump, explosions, shots):', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('                                    Codakid Game Dev 2', creds, font=font40, y=50, rjust=True))
                
                creds.append(Credit('Stepping Pebbles (Before the Walls fall): Matthew Pablo', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('                                      (opengameart.org)', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('After the Walls fall: opengameart.org', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('During the Barbarian Raid: opengameart.org', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('Menu Music: opengameart.org', creds, font=font40, y=80, rjust=True))

                creds.append(Credit('Exteral Server Management:', creds, font=font40, y=80))
                
                creds.append(Credit('Programming: Aaron McCormick', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('Support: Colin McCormick', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('Module: Flask', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('Application: Pythonanywhere.com', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('Website: villagewars.pythonanywhere.com', creds, font=font40, y=80, rjust=True))

                creds.append(Credit('Co-designers (Idea givers):', creds, font=font40, y=80))

                creds.append(Credit('Caden McCormick, Lucas McComick, David McCormick,', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('Angela McCormick, Charlie Garland, Owen Garland,', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('Samuel Mawson, John Mawson, Colin McCormick,', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('Nathan Dauner, Vincent Santoni, Jonathan Hostteter,', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('Gavin McCormick', creds, font=font40, y=50, rjust=True))
                creds.append(Credit('If you would like to see your name here, send me an email', creds, font=font30, y=30, color=(255,100,255)))
                creds.append(Credit('at aamcc@cluemail.com giving me ideas! Your idea won\'t', creds, font=font30, y=30, color=(255,100,255)))
                creds.append(Credit('necessarily be added, but your name will be added here!', creds, font=font30, y=80, color=(255,100,255)))

                #fo = shelve.open('database/data')
                #users = dict(fo)
                #fo.close()
                print(1)
                if __main__.INTERNET:
                    print(2)
                    try:
                        res = requests.get(__main__.flask_application + 'all_users')
                        res.raise_for_status()
                        print(3)
                    except:
                        __main__.INTERNET = False
                else:
                    alert('You need to be connected\nto the Internet.', title='VillageWars')
                    tab = 'Home'
                if __main__.INTERNET:
                    print(4)
                    users = res.text[4:]
                    users = eval(users)
                        
                    creds.append(Credit('First %s Accounts:' % len(users), creds, font=font40, y=80))
                        
                    for i, user in enumerate(list(users)):
                        if i+1 == len(users):
                            creds.append(Credit('%s) %s (%s)' % (i+1, user, users[user].get('name', 'No Name')), creds, font=font40, y=60, rjust=False))
                        else:
                            name = users[user].get('name', 'No Name')
                            if user in ('f', 'ModestNoob', 'ff'):
                                name = 'Aaron McCormick, test account'
                            if user == 'ProHacker':
                                name = 'Aaron McCormick, fake games account'
                            if user == 'Warpedillager':
                                name = 'Aaron McCormick, stunts account'
                            creds.append(Credit('%s) %s (%s)' % (i+1, user, name), creds, font=font40, y=50, rjust=False))
                        
                        

                    creds.append(Credit('...and new accounts are created every month!', creds, font=font40, y=200, rjust=True, color=(128,128,255)))                               

                    creds.append(Credit('Thank you everyone!', creds, font=font100, y=0, color=(255,255,5)))
                        
            for credit in creds: 
                credit.update(screen, keys=keys)
            
            
        if tab == 'Feedback':
            screen.fill((255,255,255))
            text_surf = font40.render('To send feedback, email me at aamcc@cluemail.com.', True, (0,0,0))
            rect = text_surf.get_rect(midtop=((width-menu_space)//2+menu_space, 100 + scroll))
            screen.blit(text_surf, rect)
            text_surf = font40.render('I appreciate ideas, feedback, and support!', True, (0,0,0))
            rect = text_surf.get_rect(midtop=((width-menu_space)//2+menu_space, 150 + scroll))
            screen.blit(text_surf, rect)


        do_tabs(screen, menu_space)

        
        
            

        p.display.update()
        if keys[K_F9]:
            p.display.set_caption('VillageWars ' + __main__.__version__ + ' - FPS: ' + str(round(clock.get_fps(), 1)))
        else:
            p.display.set_caption('VillageWars ' + __main__.__version__)
        clock.tick(60)
    
    return t.getMyIP(), 5555, 'sign in'

class Credit():
    space = 0
    def __init__(self, text, creds, y=0, font=None, rjust=False, color=(255,255,255)):
        self.y = type(self).space
        type(self).space += y
        self.surf = font.render(text, True, color)
        self.credits = creds
        self.rjust = rjust
    def update(self, screen, keys=0):
        global menu_space
        if not (keys[K_PAGEDOWN] or keys[K_DOWN]):
            self.y -= 0.6
        else:
            self.y -= 3
        if self.rjust:
            self.rect = self.surf.get_rect(topleft=((1000-menu_space)/2+menu_space-360, self.y))
        else:
            self.rect = self.surf.get_rect(midtop=((1000-menu_space)/2+menu_space, self.y))
        self.surf.set_alpha(min([((650-self.rect.y)/650*255), 255]))
        screen.blit(self.surf, self.rect)
        if self.y < -200:
            self.credits.remove(self)

def do_tabs(screen, width=1000, height=650):
    global mouse, click, keys, open_menu_surf, open_menu_hover_surf, options, tab, menu_space, font40, creds, scroll, carry_to
    menu_surf = p.Surface((menu_space, height))
    menu_surf.fill((50,0,50))
    screen.blit(menu_surf, (0,0))   
    if menu_space == 30:
        rect = open_menu_surf.get_rect(topleft=(4,4))
    else:
        rect = open_menu_surf.get_rect(midtop=(100,4))
    if rect.collidepoint(mouse):
        screen.blit(open_menu_hover_surf, rect)
        if click[0]:
            if menu_space == 30:
                menu_space = 200
            else:
                menu_space = 30
    else:
        screen.blit(open_menu_surf, rect)

    if menu_space == 200:
        x = 10
        y = 85
        for option in options:
            rect_surf = p.Surface((200, 100))  # rectangle around text in menu
            rect = rect_surf.get_rect(topleft=(0, y-35))
            if rect.collidepoint(mouse):
                rect_surf.fill((200,50,200))
                screen.blit(rect_surf, rect)
                surf = font40.render(option, True, (255,255,255))  # text surf
                if click[0]:
                    tab = option
                    menu_space = 30
                    scroll = 0
                    
                    carry_to = True
                    if tab == 'Credits':
                        creds = []
            else:
                surf = font40.render(option, True, (255,255,180))  # text surf
            rect = surf.get_rect(midtop=(100, y))
            screen.blit(surf, rect)
            y += 100
            

def submitLogIn(username, password):
    u = []
    if len(username) == 0:
        u.append('username')
    if len(password) == 0:
        u.append('password')
    if len(u) == 0:
        return {'create':False, 'username':username, 'password':password}
    return u
        

def runLogIn(screen, clock):
    global font40, font30

    logInPopup = p.image.load('../assets/title page/log in popup.png')

    darker = p.image.load('../assets/paused.png')
    for i in range(2):
        screen.blit(darker, (0,0))

    username_typer = Typing(block=['@', '/', '.'])
    password_typer = Typing(block=[])

    typingOn = None
    fontUnderline = p.font.SysFont('default', 35, italic=True)

    logIn_surf = p.Surface((240, 50))
    logIn_surf.fill((0,141,15))
    logIn_surf_hov = p.Surface((240, 50))
    logIn_surf_hov.fill((10,10,255))
    logIn_surf_down = p.Surface((240, 50))
    logIn_surf_down.fill((60,60,255))
    rect = logIn_surf.get_rect(topleft=(0,0))
    
    text_surf = font40.render('Log In!', True, (255,150,150))
    rect = text_surf.get_rect(center=rect.center)
    logIn_surf_hov.blit(text_surf, rect)
    logIn_surf_down.blit(text_surf, rect)
    text_surf = font40.render('Log In!', True, (0,0,0))
    rect = text_surf.get_rect(center=rect.center)
    logIn_surf.blit(text_surf, rect)
    
    logIn_button = t.Button.from_surf(screen, logIn_surf, logIn_surf_hov, logIn_surf_down, midtop=((1000-menu_space)//2+menu_space, 400))

    u_prob = False
    p_prob = False
    
    while True:


        

        
        for event in pygame.event.get():
            if event.type == QUIT:
                p.quit()
                sys.exit()
            if event.type == KEYUP and event.key == K_ESCAPE:
                return 'Cancel'
            elif event.type == KEYUP:
                if typingOn:
                    typingOn.type(event)
            if event.type in (KEYUP, KEYDOWN) and event.key in (K_RSHIFT, K_LSHIFT):
                username_typer.shift()
                password_typer.shift()
            if event.type in (KEYUP, KEYDOWN) and event.key in (K_RCTRL, K_LCTRL):
                username_typer.ctrl()
                password_typer.ctrl()
            if event.type == KEYUP and event.key == (K_TAB):
                if typingOn is None:
                    typingOn = username_typer
                if typingOn == username_typer:
                    typingOn = password_typer
                else:
                    typingOn = username_typer
            if event.type == KEYUP and event.key == K_RETURN:
                if typingOn == username_typer:
                    typingOn = password_typer
                elif typingOn == password_typer:
                    result = submitLogIn(username_typer.result, password_typer.result)
                    if type(result) == dict:
                        return result
                    if 'username' in result:
                        u_prob = True
                    if 'password' in result:
                        p_prob = True
            if logIn_button.handle_event(event):
                result = submitLogIn(username_typer.result, password_typer.result)
                if type(result) == dict:
                    return result
                elif 'username' in result:
                    u_prob = True
                if 'password' in result:
                    p_prob = True
                
        mouse = p.mouse.get_pos()
        click = p.mouse.get_pressed()
        keys = p.key.get_pressed()
        width, height = screen.get_width(), screen.get_height()

        logInRect = logInPopup.get_rect(center=((1000-menu_space)//2+menu_space, height // 2))

        screen.blit(logInPopup, logInRect)

        username_rect = p.Surface((320, 50)).get_rect(topleft=((1000-menu_space)//2+menu_space-160, 150))
        if username_rect.collidepoint(mouse) and typingOn != username_typer:
            surf = p.Surface((320, 50))
            surf.fill((100,100,255))
            surf.set_alpha(50)
            screen.blit(surf, username_rect)
            if click[0]:
                typingOn = username_typer
        password_rect = p.Surface((320, 50)).get_rect(topleft=((1000-menu_space)//2+menu_space-160, 300))
        if password_rect.collidepoint(mouse) and typingOn != password_typer:
            surf = p.Surface((320, 50))
            surf.fill((100,100,255))
            surf.set_alpha(50)
            screen.blit(surf, password_rect)
            if click[0]:
                typingOn = password_typer

        if typingOn == username_typer:
            username_surf = font40.render(username_typer.text(), True, (0,0,0))
            rect = username_surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 160))
        elif typingOn != username_typer:
            if username_typer.text() in ('|','') and u_prob:
                username_surf = font40.render('Fill this out first.', True, (250,0,0))
            else:
                username_surf = font40.render(username_typer.result, True, (0,0,0))
            rect = username_surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 160))
            if rect.right > (1000-menu_space)//2+menu_space+160:
                username_typer.typing = username_typer.typing[:-2] + username_typer.character
        try:
            screen.blit(username_surf, rect)
        except:
            pass

        surf = font40.render('Enter your username:', True, (255,255,255))
        rect = surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 110))
        screen.blit(surf, rect)
        surf = font40.render('Enter your password:', True, (255,255,255))
        rect = surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 260))
        screen.blit(surf, rect)
        
        if typingOn == password_typer:
            if password_typer.text().endswith('|'):
                password_surf = font40.render(len(password_typer.result) * '*' + '|', True, (0,0,0))
            else:
                password_surf = font40.render(len(password_typer.result) * '*', True, (0,0,0))
            rect = password_surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 310))
        elif typingOn != password_typer:
            if password_typer.result in ('|', '') and p_prob:
                password_surf = font40.render('Fill this out first.', True, (250,0,0))
            else:
                password_surf = font40.render(len(password_typer.result) * '|', True, (0,0,0))
            rect = password_surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 310))
            if rect.right > (1000-menu_space)//2+menu_space+160:
                password_typer.typing = password_typer.typing[:-2] + password_typer.character
        try:
            screen.blit(password_surf, rect)
        except:
            pass

        logIn_button.draw()
        #rect = p.Surface((240, 50)).get_rect(midtop=((1000-menu_space)//2+menu_space, 400))
        #if rect.collidepoint(mouse):
        #    surf = p.Surface((240,50))
        #    surf.fill((10,10,255))
        #    screen.blit(surf, rect)
        #    text_surf = font40.render('Log In!', True, (255,150,150))
        #    rect = text_surf.get_rect(center=rect.center)
        #    screen.blit(text_surf, rect)
        #    if click[0]:
        #        result = submitLogIn(username_typer.result, password_typer.result)
        #        if type(result) == dict:
        #            return result
        #        elif 'username' in result:
        #            u_prob = True
        #        if 'password' in result:
        #            p_prob = True
        #else:
        #    text_surf = font40.render('Log In!', True, (0,0,0))
        #    rect = text_surf.get_rect(center=rect.center)
        #    screen.blit(text_surf, rect)


        slump_rect = p.Surface((300, 80)).get_rect(midbottom=((1000-menu_space)//2+menu_space, 580))
        if slump_rect.collidepoint(mouse):
            text_surf = fontUnderline.render("Don't have an account?", True, (128,128,255))
            rect = text_surf.get_rect(midbottom=((1000-menu_space)//2+menu_space, 540))
            screen.blit(text_surf, rect)
            text_surf = fontUnderline.render("Create one here!", True, (128,128,255))
            rect = text_surf.get_rect(midbottom=((1000-menu_space)//2+menu_space, 580))
            screen.blit(text_surf, rect)
            if click[0]:
                return runCreateAccount(screen, clock)
        else:
            text_surf = fontUnderline.render("Don't have an account?", True, (0,0,255))
            rect = text_surf.get_rect(midbottom=((1000-menu_space)//2+menu_space, 540))
            screen.blit(text_surf, rect)
            text_surf = fontUnderline.render("Create one here!", True, (0,0,255))
            rect = text_surf.get_rect(midbottom=((1000-menu_space)//2+menu_space, 580))
            screen.blit(text_surf, rect)

        p.display.update()
        if keys[K_F9]:
            p.display.set_caption('VillageWars ' + __main__.__version__ + ' - FPS: ' + str(round(clock.get_fps(), 1)))
        else:
            p.display.set_caption('VillageWars ' + __main__.__version__)
        clock.tick(60)

def runCreateAccount(screen, clock):
    global font40, font30

    logInPopup = p.image.load('../assets/title page/create account popup.png')

    #darker = p.image.load('../assets/paused.png')
    #for i in range(2):
    #    screen.blit(darker, (0,0))

    username_typer = Typing(block=['@', '/', '.', ' '])
    password_typer = Typing(block=[])
    cpassword_typer = Typing(block=[])
    name_typer = Typing(block=['@', '/'])
    email_typer = Typing(block=['/', ' '])

    u_prob = False
    p_prob = False
    c_prob = False
    n_prob = False
    match_prob = False

    typingOn = None
    fontUnderline = p.font.SysFont('default', 35, italic=True)

    surf = p.Surface((242, 57))
    surf.fill((10,10,255))
    surf_hov = p.Surface((242, 57))
    surf_hov.fill((50,50,255))
    surf_down = p.Surface((242, 57))
    surf_down.fill((80,80,255))
    rect = surf.get_rect(topleft=(0,0))
    
    text_surf = font40.render('Create Account!', True, (255,150,150))
    rect = text_surf.get_rect(center=rect.center)
    surf_hov.blit(text_surf, rect)
    surf_down.blit(text_surf, rect)
    text_surf = font40.render('Create Account!', True, (0,0,0))
    rect = text_surf.get_rect(center=rect.center)
    surf.blit(text_surf, rect)
    
    create_button = t.Button.from_surf(screen, surf, surf_hov, surf_down, midtop=((1000-menu_space)//2+menu_space, 543))
    
    while True:


        

        
        for event in pygame.event.get():
            if event.type == QUIT:
                p.quit()
                sys.exit()
            if event.type == KEYUP and event.key == K_ESCAPE:
                return 'Cancel'
            elif event.type == KEYUP:
                if typingOn:
                    typingOn.type(event)
            if event.type in (KEYUP, KEYDOWN) and event.key in (K_RSHIFT, K_LSHIFT):
                username_typer.shift()
                password_typer.shift()
                cpassword_typer.shift()
                name_typer.shift()
                email_typer.shift()
            if event.type in (KEYUP, KEYDOWN) and event.key in (K_RCTRL, K_LCTRL):
                username_typer.ctrl()
                password_typer.ctrl()
                cpassword_typer.ctrl()
                name_typer.ctrl()
                email_typer.ctrl()
            if event.type == KEYUP and event.key == (K_TAB):
                if typingOn is None:
                    typingOn = username_typer
                if typingOn == username_typer:
                    typingOn = password_typer
                elif typingOn == password_typer:
                    typingOn = cpassword_typer
                elif typingOn == cpassword_typer:
                    typingOn = name_typer
                elif typingOn == name_typer:
                    typingOn = email_typer
                elif typingOn == email_typer:
                    typingOn = username_typer
            if event.type == KEYUP and event.key == K_RETURN:
                if typingOn == username_typer:
                    typingOn = password_typer
                elif typingOn == password_typer:
                    typingOn = cpassword_typer
                elif typingOn == cpassword_typer:
                    typingOn = name_typer
                elif typingOn == name_typer:
                    typingOn = email_typer
                else:
                    result = submitCreate(username_typer.result, password_typer.result, cpassword_typer.result, name_typer.result, email=email_typer.result)
                    if type(result) == dict:
                        return result
                    elif 'username' in result:
                        u_prob = True
                    if 'password' in result:
                        p_prob = True
                    if 'cpassword' in result:
                        c_prob = True
                    if 'name' in result:
                        n_prob = True
                    match_prob = 'match' in result
                    if match_prob:
                        password_typer = Typing(block=[])
                        cpassword_typer = Typing(block=[])
                        p_prob = False
                        c_prob = False
            if create_button.handle_event(event):
                result = submitCreate(username_typer.result, password_typer.result, cpassword_typer.result, name_typer.result, email=email_typer.result)
                if type(result) == dict:
                    return result
                elif 'username' in result:
                    u_prob = True
                if 'password' in result:
                    p_prob = True
                if 'cpassword' in result:
                    c_prob = True
                if 'name' in result:
                    n_prob = True
                match_prob = 'match' in result
                if match_prob:
                    password_typer = Typing(block=[])
                    cpassword_typer = Typing(block=[])
                    p_prob = False
                    c_prob = False
                
        mouse = p.mouse.get_pos()
        click = p.mouse.get_pressed()
        keys = p.key.get_pressed()
        width, height = screen.get_width(), screen.get_height()

        logInRect = logInPopup.get_rect(center=((1000-menu_space)//2+menu_space, height // 2))

        screen.blit(logInPopup, logInRect)


        
        
        # Show the box for the inputs, and change active input if needed

        username_rect = p.Surface((320, 50)).get_rect(topleft=((1000-menu_space)//2+menu_space-160, 60))
        surf = p.Surface((320, 50))
        surf.fill((255,255,255))
        screen.blit(surf, username_rect)
        if username_rect.collidepoint(mouse) and typingOn != username_typer:            
            surf = p.Surface((320, 50))
            surf.fill((100,100,255))
            surf.set_alpha(50)
            screen.blit(surf, username_rect)
            if click[0]:
                typingOn = username_typer
                
        password_rect = p.Surface((320, 50)).get_rect(topleft=((1000-menu_space)//2+menu_space-160, 160))
        surf = p.Surface((320, 50))
        surf.fill((255,255,255))
        screen.blit(surf, password_rect)
        if password_rect.collidepoint(mouse) and typingOn != password_typer:
            surf = p.Surface((320, 50))
            surf.fill((100,100,255))
            surf.set_alpha(50)
            screen.blit(surf, password_rect)
            if click[0]:
                typingOn = password_typer
                
        cpassword_rect = p.Surface((320, 50)).get_rect(topleft=((1000-menu_space)//2+menu_space-160, 260))
        surf = p.Surface((320, 50))
        surf.fill((255,255,255))
        screen.blit(surf, cpassword_rect)
        if cpassword_rect.collidepoint(mouse) and typingOn != cpassword_typer:          
            surf = p.Surface((320, 50))
            surf.fill((100,100,255))
            surf.set_alpha(50)
            screen.blit(surf, cpassword_rect)
            if click[0]:
                typingOn = cpassword_typer

        name_rect = p.Surface((320, 50)).get_rect(topleft=((1000-menu_space)//2+menu_space-160, 360))
        surf = p.Surface((320, 50))
        surf.fill((255,255,255))
        screen.blit(surf, name_rect)
        if name_rect.collidepoint(mouse) and typingOn != name_typer:
            surf = p.Surface((320, 50))
            surf.fill((100,100,255))
            surf.set_alpha(50)
            screen.blit(surf, name_rect)
            if click[0]:
                typingOn = name_typer
                
        email_rect = p.Surface((320, 50)).get_rect(topleft=((1000-menu_space)//2+menu_space-160, 460))
        surf = p.Surface((320, 50))
        surf.fill((255,255,255))
        screen.blit(surf, email_rect)
        if email_rect.collidepoint(mouse) and typingOn != email_typer:
            
            surf = p.Surface((320, 50))
            surf.fill((100,100,255))
            surf.set_alpha(50)
            screen.blit(surf, email_rect)
            if click[0]:
                typingOn = email_typer

        # Write username input on the screen
        if typingOn == username_typer:
            username_surf = font40.render(username_typer.text(), True, (0,0,0))
            rect = username_surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 70))
        elif typingOn != username_typer:
            if username_typer.text() in ('|','') and u_prob:
                username_surf = font40.render('Fill this out first.', True, (250,0,0))
            else:
                username_surf = font40.render(username_typer.result, True, (0,0,0))
            rect = username_surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 70))
        if rect.right > (1000-menu_space)//2+menu_space+160:
            username_typer.typing = username_typer.typing[:-2] + username_typer.character
        try:
            screen.blit(username_surf, rect)
        except:
            pass

        # Write password input on the screen
        if typingOn == password_typer:
            if password_typer.text().endswith('|'):
                password_surf = font40.render(len(password_typer.result) * '*' + '|', True, (0,0,0))
            else:
                password_surf = font40.render(len(password_typer.result) * '*', True, (0,0,0))
            rect = password_surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 170))
        elif typingOn != password_typer:
            if password_typer.text() in ('|','') and p_prob:
                password_surf = font40.render('Fill this out first.', True, (250,0,0))
            else:
                password_surf = font40.render(len(password_typer.result) * '*', True, (0,0,0))
        rect = password_surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 170))
        if rect.right > (1000-menu_space)//2+menu_space+160:
            password_typer.typing = password_typer.typing[:-2] + password_typer.character
        try:
            screen.blit(password_surf, rect)
        except:
            pass

        # Write cpassword input on the screen
        if typingOn == cpassword_typer:
            if password_typer.text().endswith('|'):
                cpassword_surf = font40.render(len(cpassword_typer.result) * '*' + '|', True, (0,0,0))
            else:
                cpassword_surf = font40.render(len(cpassword_typer.result) * '*', True, (0,0,0))
            rect = cpassword_surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 270))
        elif typingOn != cpassword_typer:
            if cpassword_typer.text() in ('|','') and c_prob:
                cpassword_surf = font40.render('Fill this out first.', True, (250,0,0))
            elif cpassword_typer.text() in ('|','') and match_prob:
                cpassword_surf = font30.render('Passwords must match.', True, (250,0,0))
            else:
                cpassword_surf = font40.render(len(cpassword_typer.result) * '*', True, (0,0,0))
        rect = cpassword_surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 270))
        if rect.right > (1000-menu_space)//2+menu_space+160:
            cpassword_typer.typing = cpassword_typer.typing[:-2] + cpassword_typer.character
        try:
            screen.blit(cpassword_surf, rect)
        except:
            pass

        # Write name input on the screen
        if typingOn == name_typer:
            name_surf = font40.render(name_typer.text(), True, (0,0,0))
            rect = cpassword_surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 370))
        elif typingOn != name_typer:
            if name_typer.text() in ('|','') and n_prob:
                name_surf = font40.render('Fill this out first.', True, (250,0,0))
            else:
                name_surf = font40.render(name_typer.result, True, (0,0,0))
        rect = name_surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 370))
        if rect.right > (1000-menu_space)//2+menu_space+160:
            name_typer.typing = name_typer.typing[:-2] + name_typer.character
        try:
            screen.blit(name_surf, rect)
        except:
            pass

        # Write email input on the screen
        if typingOn == email_typer:
            email_surf = font40.render(email_typer.text(), True, (0,0,0))
            rect = email_surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 470))
        elif typingOn != email_typer:
            if email_typer.result != '':
                email_surf = font40.render(email_typer.result, True, (0,0,0))
            else:
                email_surf = font40.render('Optional', True, (160,160,160))
        rect = email_surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 470))
        if rect.right > (1000-menu_space)//2+menu_space+160:
            email_typer.typing = email_typer.typing[:-2] + email_typer.character
        try:
            screen.blit(email_surf, rect)
        except:
            pass

        

        surf = font40.render('Create your username:', True, (255,255,255))
        rect = surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 25))
        screen.blit(surf, rect)
        surf = font40.render('Enter your password:', True, (255,255,255))
        rect = surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 125))
        screen.blit(surf, rect)
        surf = font40.render('Confirm your password:', True, (255,255,255))
        rect = surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 225))
        screen.blit(surf, rect)
        surf = font40.render('Enter your name:', True, (255,255,255))
        rect = surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 325))
        screen.blit(surf, rect)
        surf = font40.render('Enter your email address:', True, (255,255,255))
        rect = surf.get_rect(topleft=((1000-menu_space)//2+menu_space-160, 425))
        screen.blit(surf, rect)

        create_button.draw()
        #rect = p.Surface((242, 57)).get_rect(midtop=((1000-menu_space)//2+menu_space, 543))
        #if rect.collidepoint(mouse):
        #    surf = p.Surface((242, 57))
        #    surf.fill((50,50,255))
        #    screen.blit(surf, rect)
        #    text_surf = font40.render('Create Account!', True, (255,150,150))
        #    rect = text_surf.get_rect(center=rect.center)
        #    screen.blit(text_surf, rect)
        #    if click[0]:
        #        result = submitCreate(username_typer.result, password_typer.result, cpassword_typer.result, name_typer.result, email=email_typer.result)
        #        if type(result) == dict:
        #            return result
        #        elif 'username' in result:
        #            u_prob = True
        #        if 'password' in result:
        #            p_prob = True
        #        if 'cpassword' in result:
        #            c_prob = True
        #        if 'name' in result:
        #            n_prob = True
        #        match_prob = 'match' in result
        #        if match_prob:
        #            password_typer = Typing(block=[])
        #            cpassword_typer = Typing(block=[])
        #            p_prob = False
        #            c_prob = False
        #        p.mouse.set_pos(mouse[0], 540)
        #else:
        #    surf = p.Surface((242, 57))
        #    surf.fill((10,10,255))
        #    screen.blit(surf, rect)
        #    text_surf = font40.render('Create Account!', True, (0,0,0))
        #    rect = text_surf.get_rect(center=rect.center)
        #    screen.blit(text_surf, rect)


        p.display.update()
        if keys[K_F9]:
            p.display.set_caption('VillageWars ' + __main__.__version__ + ' - FPS: ' + str(round(clock.get_fps(), 1)))
        else:
            p.display.set_caption('VillageWars ' + __main__.__version__)
        clock.tick(60)

def submitCreate(username, password, cpassword, name, email=None):
    u = []
    if len(username) == 0:
        u.append('username')
    if len(password) == 0:
        u.append('password')
    if len(cpassword) == 0:
        u.append('cpassword')
    if password != cpassword:
        u.append('match')
    if len(name) == 0:
        u.append('name')
    if len(u) == 0:
        if not email:
            email = None
        return {'create':True, 'username':username, 'password':password, 'name':name, 'email':email}
    return u
