import pygame
import toolbox
from animations import *
import random as r
import random

from elements import Obstacle, OldObstacle, Sprite, SCREEN

def explosion_damage(self, radius=400, name='an explosion', damage=80, knockback=120):
    BAM(self)
    for p in self.server.users:
        screen = pygame.Rect(0, 0, 1000, 650)
        screen.center = p.character.rect.center
        if screen.colliderect(self.obstacle_rect):
            p.Send({'action':'sound', 'sound':'TNT'})
    ray = pygame.Rect(0, 0, radius, radius)
    ray.center = self.x, self.y
    for item in self.server.obstacles.collide_all(self, ray, ignore=['Barrel', 'TNT', 'Building']):
        item.explode()
    for item in self.server.dynamics.collide_all(self, ray):
        angle = toolbox.getAngle(self.x, self.y, item.rect.centerx, item.rect.centery)
        item.getHurt(damage, attacker=self, name=name, angle=angle, knockback=knockback, msg='<Victim> was blown up by <Attacker>.')

class Tree(Obstacle):
    type = 'Tree'
    dimensions = (50, 120)
    max_health = 300
    def __init__(self, server, x, y):
        Obstacle.__init__(self, server, x, y)
        self.display_rect = pygame.Rect(0, 0, 200, 280)
        self.display_rect.center = self.x, self.y
        self.obstacle_rect = pygame.Rect(0, 0, 50, 120)
        self.obstacle_rect.midtop = self.display_rect.center
    def update(self):
        for p in self.server.players:
            if not p.pending:
                screen = pygame.Rect(0, 0, 1000, 650)
                visible_rect = p.character.get_rect(self.display_rect)
                if screen.colliderect(visible_rect):
                    p.to_send.append({'action':'draw_obstacle',
                            'image':'tree',
                            'coords':visible_rect.center,
                            'health':self.health,
                            'max_health':self.max_health})
    def explode(self):
        self.getHurt(240)


class Sappling(Sprite):
    type = 'Sappling'
    dimensions = (60, 90)
    def __init__(self, server, x, y):
        Sprite.__init__(self, self.groups)
        self.server = server
        self.x = x
        self.y = y
        self.count = 100
        self.zone_rect = pygame.Rect(0, 0, 60, 90)
        self.zone_rect.center = self.x, self.y
    def update(self):
        self.count -= 1
        if not self.count:
            Tree(self.server, self.x, self.y)
            self.kill()
            return
        for p in self.server.users:
            visible_rect = p.character.get_rect(self.zone_rect)
            if SCREEN.colliderect(visible_rect):
                p.to_send.append({'action':'draw_obstacle',
                        'image':'sappling',
                        'coords':visible_rect.center})

class Boulder(OldObstacle):
    type = 'Boulder'
    dimensions = (200, 200)
    def __init__(self, server, x, y):
        super().__init__(server, x, y)
        self.image_id = 'boulder'
        self.max_health = self.health = random.randint(18, 32) * 10

class Crate(OldObstacle):
    type = 'Crate'
    max_health = 800
    dimensions = (50, 50)
    def __init__(self, character, x, y):
        super().__init__(character.channel.server, x, y)
        self.image_id = 'crate'
        self.character = character
    def explode(self):
        self.kill()

class Barrel(OldObstacle):
    type = 'Barrel'
    dimensions = (50, 50)
    knockback = 160
    speed = 16
    def __init__(self, character, x, y, angle, health=15, max_health=15, explosive=False):
        super().__init__(character.channel.server, x, y)
        self.image_id = 'barrel'
        self.explosive = explosive
        self.max_health = max_health
        self.health = health
        self.character = character
        self.angle = angle
        self.sedentary = False
        self.roll_angle = angle
        self.damage = self.health
        self.kill_msg = '<Victim> got rolled over by a barrel.'
        if -90 <= angle <= 90:
            self.roll_direction = -10
        else:
            self.roll_direction = 10
    @property
    def obstacle_rect(self):
        rect = pygame.Rect(0, 0, *self.dimensions)
        rect.center = self.x, self.y
        return rect
    @obstacle_rect.setter
    def obstacle_rect(self, *args, **kwargs):
        pass
    def explode(self):
        if not self.sedentary:
            explosion_damage(self, radius=350, name=self.channel.username, damage=80, knockback=120)
        self.kill()
    def update(self):
        if not self.sedentary:
            self.roll_angle += self.roll_direction
            self.move()
        for p in self.server.users:
            visible_rect = p.character.get_rect(self.obstacle_rect)
            if SCREEN.colliderect(visible_rect):  # TODO: Continue from here
                p.to_send.append({'action':'draw_obstacle',
                        'image':self.image_id,
                        'coords':visible_rect.center,
                        'health':self.health,
                        'max_health':self.max_health,
                        'angle':self.roll_angle,
                        'explosive':self.explosive})
    def sedent(self):
        if self.explosive:
            self.explode()
            return
        self.sedentary = True
        self.character = None  # This way they can explode
        self.getHurt(10)
        for p in self.server.players:
            if not p.pending:
                screen = pygame.Rect(0, 0, 1000, 650)
                rect = p.character.get_rect(self.obstacle_rect)
                if screen.colliderect(rect):
                    p.to_send.append({'action':'sound','sound':'barrel'})

    def move(self, amount=None):
        x, y = toolbox.getDir(self.angle, amount or self.speed)
        self.move_x(round(x))
        self.move_y(round(y))
        obstacle = self.server.obstacles.collide(self, self.obstacle_rect)
        enemy = self.server.dynamics.collide(self.character, self.obstacle_rect)
        if obstacle:
            obstacle.getHurt(self.damage, angle=self.angle, knockback=self.knockback, attacker=self.character, name=self.channel.username, msg=self.kill_msg)
            return self.sedent()
        elif enemy:
            result = enemy.getHurt(self.damage, angle=self.angle, knockback=self.knockback, attacker=self.character, name=self.channel.username, msg=self.kill_msg)
            if result:
                self.move(self.speed * -5)
                return self.sedent()
            else:
                return self.sedent()
    def move_x(self, amount):
        self.x += amount
    def move_y(self, amount):
        self.y += amount


class SpikyBush(Obstacle):
    type = 'Spiky bush'
    dimensions = (50, 50)
    max_health = 260
    image_id = 'spiky bush'
    def __init__(self, character, x, y):
        Obstacle.__init__(self, character.server, x, y)
        self.character = character
    def explode(self):
        self.kill()
    def update(self):
        for p in self.server.users:
            visible_rect = p.character.get_rect(self.obstacle_rect)
            if SCREEN.colliderect(visible_rect):
                p.to_send.append({'action':'draw_obstacle',
                            'image': self.image_id,
                            'coords':visible_rect.center,
                            'health':self.health,
                            'max_health':self.max_health})
    def getHurt(self, damage, **kwargs):
        if self.health > 0:
            self.health -= damage
            if self.health < 1:
                self.kill()


class Gate(Obstacle):
    type = 'Gate'
    image_id = 'gate'
    max_health = 1000
    def __init__(self, character, x, y, rot):
        self.dimensions = ((200, 100) if rot else (100, 200))
        Obstacle.__init__(self, character.server, x, y)
        self.character = character
        self.rotated = rot
    def explode(self):
        self.getHurt(900, None)
    def update(self):
        for p in self.server.users:
            visible_rect = p.character.get_rect(self.obstacle_rect)
            if SCREEN.colliderect(visible_rect):
                p.to_send.append({'action':'draw_obstacle',
                            'image':self.image_id,
                            'coords':visible_rect.center,
                            'health':self.health,
                            'max_health':self.max_health,
                            'rotated?':self.rotated})

class TNT(Obstacle):
    type = 'TNT'
    dimensions = (50, 50)
    max_health = 130
    def __init__(self, character, x, y):
        Obstacle.__init__(self, character.server, x, y)
        self.character = character
    def update(self):
        for p in self.server.users:
            p.to_send.append({'action':'draw_obstacle',
                            'image':'TNT',
                            'coords':(p.character.get_x(self), p.character.get_y(self))})
        self.health -= 1  # "Health" really just is a countdown to explosion
        if self.health == 0:
            self.explode()

    def getHurt(self, damage, **kwargs):
        self.explode()
    def explode(self):
        explosion_damage(self, radius=400, name=self.channel.username, damage=80, knockback=120)
        self.kill()


class Block(Obstacle):
    def __init__(self, topleft, size):
        rect = pygame.Rect(topleft, size)
        x, y = rect.center
        self.dimensions = size
        Obstacle.__init__(self, self.server, x, y)
    def isBuilding(self):
        return False
    def getHurt(self, damage, **kwargs):
        pass