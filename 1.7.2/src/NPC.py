import pygame
import random
import toolbox
from balloon import ArcheryBalloon
from animations import *

from elements import Sprite, Obstacle, SCREEN, Dummy, playsound

class Collector(Sprite):
    type = 'Collector'
    def __init__(self, building):
        Sprite.__init__(self, *self.groups)
        self.building = building
        if building.type == 'Miner\'s Guild':
            self.type = 'Miner'
            self.yard_type = 'Mine'
            self.collect_status = 'Mining Gold'
        elif building.type == 'Farmer\'s Guild':
            self.type = 'Farmer'
            self.yard_type = 'Farm'
            self.collect_status = 'Gathering Food'
        self.character = building.character
        self.server = building.server
        self.x = building.keeper_rect.centerx
        self.y = building.keeper_rect.centery
        self.speed = 2
        self.gold = 0
        self.food = 0
        self.dest_x = 0
        self.dest_y = 0
        sm_dist = 8000
        for yard in self.building.server.resources:
            if type(yard).__name__ == self.yard_type:
                dist = toolbox.getDist(self.x, self.y, yard.x, yard.y)
                if dist < sm_dist:
                    sm_dist = dist
                    self.yard = yard
        self.setout()
    @property
    def channel(self):
        return self.character.channel
    @property
    def rect(self):
        rect = pygame.Rect(0, 0, 50, 50); rect.center = self.x, self.y; return rect
    @property
    def angle(self):
        return toolbox.getAngle(self.x, self.y, self.dest_x, self.dest_y)
    @property
    def resources(self):
        return self.gold + self.food
    def at_dest(self):
        return toolbox.getDist(self.x, self.y, self.dest_x, self.dest_y) < 10
    def setout(self):
        self.status = 'Heading to ' + self.yard_type
        if self.type == 'Farmer':
            self.dest_x = random.randint(self.yard.x + 75, self.yard.x + 285)
            self.dest_y = self.yard.y + 25
        elif self.type == 'Miner':
            self.dest_x = self.yard.x + 75
            self.dest_y = random.randint(self.yard.y + 25, self.yard.y + 375)
    def locate_resource(self):
        self.status = self.collect_status
        smallest_dist = 1000
        for resource in (self.yard.foods if self.yard_type == 'Farm' else self.yard.golds):
            if resource.image == 'good':
                dist = toolbox.getDist(self.x, self.y, resource.x, resource.y)
                if dist < smallest_dist:
                    smallest_dist = dist
                    self.resource = resource
                    self.dest_x = resource.x
                    self.dest_y = resource.y
    def collect_resource(self):
        self.resource.collect(self)
        if self.resource.image == 'used':
            self.locate_resource()
    def return_to_guild(self):
        self.status = 'Returning to Guild'
        self.dest_x, self.dest_y = self.building.keeper_rect.center
    def move(self):
        x, y = toolbox.getDir(self.angle, self.speed)
        x_start, y_start = self.x, self.y
        self.x += x
        if self.server.obstacles.collide(self, self.rect, ignore_friend=['Gate'], ignore=['Spiky bush']):
            self.x -= x
        self.y += y
        if self.server.obstacles.collide(self, self.rect, ignore_friend=['Gate'], ignore=['Spiky bush']):
            self.y -= y
        if round(x_start) == round(self.x) and round(y_start) == round(self.y):  # Move even though the obstacle is blocking
            self.x += x
            self.y += y
    def update(self):
        if self.status == self.collect_status:
            if self.resources < 20:
                self.collect_resource()
            else:
                self.return_to_guild()
        else:
            self.move()
        if self.at_dest():
            if self.status == 'Heading to ' + self.yard_type:
                self.locate_resource()
            elif self.status == 'Returning to Guild':
                if self.type == 'Farmer':
                    self.building.character.food += self.resources
                    self.channel.add_message(f'Received {self.resources} food.')
                elif self.type == 'Miner':
                    self.building.character.gold += self.resources
                    self.channel.add_message(f'Received {self.resources} gold.')
                self.gold = 0
                self.food = 0
                self.setout()
        for p in self.server.users:
            rect = p.character.get_rect(self.rect)
            status = self.status
            if status == self.collect_status:
                status += f': {self.resources}/20'
            if SCREEN.colliderect(rect):
                p.to_send.append({'action':'draw_NPC',
                        'coords':rect.center,
                        'image':self.type.lower(),
                        'status':status,
                        'color':self.channel.color,
                        'angle':self.angle})
    def getHurt(self, damage, angle=None, knockback=None, **kwargs):
        x, y = toolbox.getDir(angle, knockback)
        self.x += x
        if self.server.obstacles.collide(self, self.rect, ignore_friend=['Gate']):
            self.x -= x
        self.y += y
        if self.server.obstacles.collide(self, self.rect, ignore_friend=['Gate']):
            self.y -= y


class ArcheryTower(Obstacle):
    type = 'Archery Tower'
    dimensions = (360, 360)
    max_health = 300
    shot_speed = 60
    balloon_damage = 24
    balloon_speed = 45
    knockback = 32
    building = None
    def __init__(self, character):
        Obstacle.__init__(self, character.server, character.x, character.y - 240)
        self.character = character
        self.shoot_cooldown = self.shot_speed
        self.state = 'alive'
        self.attacking = False
        self.name = self.type
    @property
    def channel(self):
        return self.character.channel
    def update(self):
        self.look_x = self.character.x
        self.look_y = self.character.y
        self.attacking = False
        closest_dist = float('inf')
        for enemy in self.server.dynamics:
            dist = toolbox.getDist(self.x, self.y, enemy.x, enemy.y)
            if enemy.channel != self.channel and dist < min(800, closest_dist):
                self.look_x = enemy.rect.centerx
                self.look_y = enemy.rect.centery
                self.attacking = True
                closest_dist = dist
        self.angle = toolbox.getAngle(self.x, self.y, self.look_x, self.look_y)
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.shoot_cooldown < 1 and self.attacking and self.state == 'alive':
            ArcheryBalloon(self, knockback=self.knockback)  # knockback isn't usually specified
            self.shoot_cooldown = self.shot_speed

        for p in self.server.users:
            rect = p.character.get_rect(self.obstacle_rect)
            if SCREEN.colliderect(rect):
                p.to_send.append({'action':'archery_tower',
                              'coords':rect.center,
                              'angle':self.angle,
                              'color':self.channel.color,
                              'health':self.health,
                              'state':self.state})
    
    def getHurt(self, damage, **kwargs):
        if self.state == 'broken' or kwargs.get('attacker') == self.character:
            return
        self.health -= damage
        if self.health <= 0:
            self.state = 'broken'
            attacker = kwargs.get('name', getattr(kwargs.get('attacker'), 'type', 'Anonymous'))
            self.channel.add_message(f'{attacker} has broken one of your Archery Towers.')
            self.zone_rect = self.obstacle_rect
            self.remove(self.server.obstacles)
            self.add(self.server.zones)

    def explode(self):
        self.getHurt(80, name='An explosion')
        if self.state == 'broken':
            self.kill()

class Robot(Sprite):
    type = 'Robot'
    max_health = 100
    dimensions = (50, 50)
    def __init__(self, building):
        Sprite.__init__(self, self.groups)
        self.building = building
        self.server = building.server
        self.character = building.character
        self.angle = random.randint(0, 360)
        self.x, self.y = self.building.keeper_rect.center
        self.fav_dir = random.choice([5, -5])
        self.angry_test = 20
        self.regular_test = 2
        self.angry = False
        self.speed = 4
        self.health = self.max_health
        self.hurt = 0
        self.dead = 0
        self.state = 'Peaceful'
        self.safety_zone = pygame.Rect(0, 0, 3400, 2190)
        self.safety_zone.center = self.x, self.y
        self.range = pygame.Rect(0, 0, 3000, 2000)
        self.range.center = self.x, self.y
    @property
    def channel(self):
        return self.character.channel
    @property
    def rect(self):
        rect = pygame.Rect(0, 0, *self.dimensions); rect.center= self.x, self.y; return rect
    def update(self):
        obstacle = self.server.obstacles.collide(self, self.rect, ignore_friend=['Gate'], ignore=['Spiky bush'])
        if obstacle:
            if obstacle.type == 'Crate':
                x, y = toolbox.getDir(self.angle + 180, 40)
                self.x += round(x)
                self.y += round(y)
            else:
                self.getHurt(self.health)  # Suffocate
        if self.hurt:
            self.hurt -= 1
        if self.dead:
            self.dead -= 1
            if not self.dead:
                self.add(self.server.dynamics)  # Sprite.add()
        if not self.dead:
            self.AI()
            for p in self.server.users:
                rect = p.character.get_rect(self.rect)
                if SCREEN.colliderect(rect):
                    p.to_send.append({'action':'draw_robot',
                                'coords':rect.center,
                                'name':'Robot',
                                'health':self.health,
                                'image':('hurt' if self.hurt else 'regular'),
                                'color':self.channel.color,
                                'angle':self.angle})

            for character in self.server.characters:
                if self.rect.colliderect(character.rect) and character != self.character and not p.character.dead:
                    character.getHurt(10, name=self.channel.username + "'s Robots", angle=self.angle, knockback=52)

    def AI(self):
        if self.state == 'Attacking':
            dist = toolbox.getDist(self.x, self.y, *self.building.keeper_rect.center)
            speed = self.speed * min(1, 2600/dist)
        else:
            speed = 2
        if self.state == 'Peaceful' and not self.rect.colliderect(self.safety_zone):
            self.angle = toolbox.getAngle(self.x, self.y, self.building.keeper_rect.centerx, self.building.keeper_rect.centery)
        x, y = toolbox.getDir(self.angle, speed)
        self.x += x
        obstacle = self.server.obstacles.collide(self, self.rect, ignore_friend=['Gate'], ignore=['Spiky bush'])
        if obstacle:
            self.x -= x
        self.y += y
        obstacle = self.server.obstacles.collide(self, self.rect, ignore_friend=['Gate'], ignore=['Spiky bush'])
        if obstacle:
            self.y -= y
        suspect = None
        closest_dist = float('inf')
        for character in self.server.characters:
            dist = toolbox.getDist(self.x, self.y, character.x, character.y)
            if character.rect.colliderect(self.range) and not character.dead and not character == self.character and dist < closest_dist:
                closest_dist = dist
                suspect = character
        if suspect is None:
            closest_dist = float('inf')
            for character in self.server.characters:
                dist = toolbox.getDist(self.x, self.y, character.x, character.y)
                if SCREEN.colliderect(character.get_rect(self.rect)) and not character.dead and not character == self.character and dist < closest_dist:
                    closest_dist = dist
                    suspect = character
        if suspect is not None:
            self.state = 'Attacking'
            self.attacking = suspect
            self.angle = toolbox.getAngle(self.x, self.y, self.attacking.x, self.attacking.y)  # + random.randint(-2,2)
        else:
            self.state = 'Peaceful'

    def die(self):
        Explosion(self)
        self.remove(self.server.dynamics)  # Sprite.remove
        self.dead = 200
        playsound(self, 'die', self.rect)
        self.x, self.y = self.building.keeper_rect.center
        self.health = self.max_health
        self.state = 'Peaceful'
        self.angle = random.randint(0, 360)

    def getHurt(self, damage, **kwargs):
        if kwargs.get('attacker', Dummy).channel == self.channel:
            damage = 0
        self.health -= damage
        if self.health <= 0:
            return self.die()
        elif damage != 0:
            self.hurt = 8
        if self.state == 'Peaceful':
            self.angle = kwargs.get('angle', self.angle)
        x, y = toolbox.getDir(kwargs.get('angle', 0), kwargs.get('knockback', 0))
        self.x += x
        obstacle = self.server.obstacles.collide(self, self.rect, ignore_friend=['Gate'])
        if obstacle:
            self.x -= x
        self.y += y
        obstacle = self.server.obstacles.collide(self, self.rect, ignore_friend=['Gate'])
        if obstacle:
            self.y -= y
