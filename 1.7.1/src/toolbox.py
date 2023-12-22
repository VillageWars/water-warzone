import pygame
from pygame.locals import *
import math
import socket, subprocess

def black_and_white(surface, change=0):
    width = surface.get_width()
    height = surface.get_height()
    surf = surface.__copy__()
    for x in range(width):
        for y in range(height):
            color = list(surface.get_at((x, y)))
            alpha = color.pop()
            color = [max(0, min(255, (sum(color)/3)+change)) for i in range(3)]
            color.append(alpha)
            #if alpha > 200:
            surf.set_at((x, y), tuple(color))
    return surf
    
    width = surface.get_width()
    height = surface.get_height()
    surf = pygame.Surface((width, height))
    surf.fill((100,100,100))
    for x in range(width):
        for y in range(height):
            color = list(surface.get_at((x, y)))
            alpha = color.pop()
            color = [sum(color)/3 for i in range(3)]
            color.append(alpha)
            #if alpha > 200:
            surf.set_at((x, y), tuple(color))
    
    return surf

class Button:
    def __init__(self, screen, image='', image_hover='', image_down='', image_off='', off=False, assets='../assets/', accepts=None, **kwargs): # give pygame.Rect kwargs
        if accepts is None:
            self.accepts = [1] # Left Click only
        else:
            self.accepts = accepts
        assert type(assets) == str
        self.screen = screen
        try:
            self.image = pygame.image.load(assets + image)
        except FileNotFoundError:
            self.image = pygame.Surface((0,0))
        try:
            self.image_hov = pygame.image.load(assets + image_hover)
        except FileNotFoundError:
            pass
        try:
            self.image_down = pygame.image.load(assets + image_down)
        except FileNotFoundError:
            pass
        try:
            self.image_no = pygame.image.load(assets + image_off)
        except FileNotFoundError:
            pass
        self.on = not off
        try:
            self.rect = self.image.get_rect(**kwargs)
        except Exception as exc:
            self.rect = self.image_off.get_rect(**kwargs)

        self.state = ('idle' if self.on else 'off')

    @property
    def x(self):
        return self.rect.x
    @x.setter
    def x(self, value):
        self.rect.x = value
    @property
    def y(self):
        return self.rect.y
    @y.setter
    def y(self, value):
        self.rect.y = value

    @classmethod
    def from_surf(cls, screen, image=None, image_hover=None, image_down=None, image_off=None, off=False, **kwargs):
        button = Button(screen, assets='filenotfounderror.png', off=off)
        if image:
            button.image = image
        if image_hover:
            button.image_hov = image_hover
        if image_down:
            button.image_down = image_down
        if image_off:
            button.image_no = image_off
        button.rect = button.image.get_rect(**kwargs)
        return button

    def handle_event(self, event):
        in_coords = self.rect.collidepoint(pygame.mouse.get_pos()[:2])
        
        if event.type not in (MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION):
            return
        
        if self.state == 'idle':
            if event.type == pygame.MOUSEBUTTONDOWN and in_coords and event.button in self.accepts:
                self.state = 'armed'
        elif self.state == 'armed':
            if event.type == MOUSEBUTTONUP and in_coords and event.button in self.accepts:
                self.state = 'idle'
                self.draw()
                return event.button
            if event.type == MOUSEMOTION and not in_coords:
                self.state = 'disarmed'
        elif self.state == 'disarmed':
            if event.type == MOUSEMOTION and in_coords:
                self.state = 'armed'
            elif event.type == MOUSEBUTTONUP and event.button in self.accepts:
                self.state = 'idle'
        return False

    def draw(self):
        in_coords = self.rect.collidepoint(pygame.mouse.get_pos()[:2])
        self.down = pygame.mouse.get_pressed()[0]
        if self.state == 'armed':
            self.screen.blit(self.image_down, self.rect)
        elif self.state == 'idle' or self.state == 'disarmed':
            if in_coords and (not self.down):
                self.screen.blit(self.image_hov, self.rect)
            else:
                self.screen.blit(self.image, self.rect)
        elif self.state == 'off':
            self.screen.blit(self.image_no, self.rect)

def rotate(image, rect, angle):
    """
    rotate returns the rotated version of image and the rotated image's rectangle.
    """
    # Get a new image that is the original image but rotated
    new_image = pygame.transform.rotate(image, angle)
    # Get a new rect with the center of the old rect
    new_rect = new_image.get_rect(center=rect.center)
    return new_image, new_rect

def getDist(x1, y1, x2, y2):
    """
    getDist returns the distance between (x1, y1) and (x2, y2).
    """
    
    x = abs(x1-x2)
    y = abs(y1-y2)
    return math.sqrt(x*x+y*y)


def getAngle(x1, y1, x2, y2):
    """
    getAnlge returns the angle (x1, y1) should be at if it is facing (x2, y2).
    """
    
    x_difference = x2-x1
    y_differnece = y2-y1
    return math.degrees(math.atan2(-y_differnece, x_difference))

def getDir(angle, total=1):
    """
    returns (x, y) where x and y are the distance moved if the unit is moving at the angle.
    """
    
    angle_rads = math.radians(angle)
    x_move = math.cos(angle_rads) * total
    y_move = -(math.sin(angle_rads) * total)
    return x_move, y_move


def centerXY(thing, screen):
    """
    centeringCoords returns the coords that will put thing in the center of the screen.
    """
    new_x = screen.get_width()/2 - thing.get_width()/2
    new_y = screen.get_height()/2 - thing.get_height()/2
    return new_x, new_y


class keyDownListener():
    """
    keyDownListener keeps track of one key and says when it gets pressed down.
    self.down will be True once every time the key is pressed and False otherwise.
    """
    def __init__(self):
        self.down = False
        self.is_up = False
        
    def update(self, key_pressed):
        if not key_pressed:
            self.is_up = True
            self.down = False
        else:
            if self.is_up:
                self.down = True
            else:
                self.down = False
            self.is_up = False


def getMyIP():
    """
    getMyIP returns the IP address on the computer you run it on.
    This may not work properly if you're not connected to the internet.
    (If this code seems super complicated, don't worry.. I don't understand it either  -Andy)
    """
    return str((([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")]
             or [[(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]])
            + ["no IP found"])[0])


def network():
    raw_wifi = subprocess.check_output(['netsh', 'WLAN', 'show', 'interfaces'])
    data_strings = raw_wifi.decode('utf-8').split()
    try:
        index = data_strings.index('Profile')
    except:
        return None
    return data_strings[index + 2]

def copy(theList):
    return theList[:]

def getVersionInt(version_str):
    parts = version_str.split('.')
    return int(parts[0]) * 10000 + int(parts[1]) * 100 + int(parts[2])


