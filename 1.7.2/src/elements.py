import random
import math
import logging
import pygame
import toolbox

SCREEN = pygame.Rect(0, 0, 1000, 650)

def pass_condition(sprite, other, ignore_friend, ignore):
    # `other` could be any dynamic object
    if sprite == other:
        return True
    if hasattr(sprite, 'type'):
        if (sprite.type in ignore_friend and sprite.channel == other.channel) or sprite.type in ignore:
            return True
        if issubclass(type(sprite), Building) and (('Building' in ignore_friend and sprite.channel == other.channel) or 'Building' in ignore):
            return True
    else:
        logging.warning(f'Object of type `{type(sprite)}` has no `type` attribute.')
    return False
class Group(pygame.sprite.Group):
    rect = 'rect'
    def collide(self, other, rect, ignore_friend=(), ignore=()):
        sprites = self.collide_all(other, rect, ignore_friend=ignore_friend, ignore=ignore)
        if sprites: return sprites[0]
    def collide_all(self, other, rect, ignore_friend=(), ignore=()):
        return [sprite for sprite in self if getattr(sprite, self.rect).colliderect(rect) and not pass_condition(sprite, other, ignore_friend=ignore_friend, ignore=ignore)]
class Obstacles(Group):
    rect = 'obstacle_rect'
class Dynamics(Group):
    rect = 'rect'
class Zones(Group):
    rect = 'zone_rect'

class Sprite(pygame.sprite.Sprite):
    groups = []

Dummy = type('Dummy', (object,), {'__bool__': (lambda self: False), '__getattr__': (lambda self, attr: None), 'gold': 0, 'food': 0})()

class Balloon(Sprite):
    def __init__(self, owner, **kwargs):
        Sprite.__init__(self, *self.groups)
        self.shooter = owner
        self.x = self.shooter.x
        self.y = self.shooter.y
        self.server = self.shooter.server
        self.shooter_name = kwargs.get('name', self.shooter.name)
        self.angle = kwargs.get('angle', self.shooter.angle)
        self.damage = kwargs.get('damage', self.shooter.balloon_damage)
        self.speed = kwargs.get('speed', self.shooter.balloon_speed)
        self.knockback = kwargs.get('knockback', (self.speed * 8 - 98) / 3)  # Only pass kwarg if necessary
        self.kill_msg = kwargs.get('msg', '<Attacker> splashed <Victim> too hard.')
        if kwargs.get('image_id'):
            self.image_id = kwargs['image_id']
        else:
            self.image_id = (0 if self.damage < 20 else 1)
            if self.shooter.shot_speed < 8:
                self.image_id = (2 if self.damage < 20 else 3)
    @property
    def channel(self):
        return getattr(self.shooter, 'channel', None)
    @property
    def rect(self):
        rect = pygame.Rect(0, 0, 16, 16); rect.center = self.x, self.y; return rect
    def update(self):
        for p in self.server.users:
            visible_rect = p.character.get_rect(self.rect)
            if SCREEN.colliderect(visible_rect):
                p.to_send.append({'action':'draw_balloon',
                                  'coords':visible_rect.center,
                                  'angle':self.angle,
                                  'id':self.image_id})
        self.move()
    def move(self):
        dist = self.speed
        while dist > 16:  # So that it never skips over objects in the middle
            x, y = toolbox.getDir(self.angle, 16)
            self.x += x
            self.y += y
            self.test_collide()
            if not self.alive():
                return
            dist -= 16
        x, y = toolbox.getDir(self.angle, dist)
        self.x += x
        self.y += y
        self.test_collide()
    def test_collide(self):
        obstacle = self.server.obstacles.collide(self.shooter, self.rect, ignore_friend=['Gate'])
        enemy = self.server.dynamics.collide(self.shooter, self.rect, ignore_friend=['Character'])

        if obstacle:
            obstacle.getHurt(self.damage, angle=self.angle, knockback=self.knockback, name=self.shooter_name, attacker=self.shooter, msg=self.kill_msg)
            self.pop()
        elif enemy:
            if 'Barbarian' in enemy.type and 'Barbarian' in self.shooter_name:
                return
            result = enemy.getHurt(self.damage, angle=self.angle, knockback=self.knockback, attacker=self.shooter, name=self.shooter_name, msg=self.kill_msg)
            if result:
                type(self)(enemy, angle=result, damage=self.damage, speed=self.speed, knockback=self.knockback, msg='<Attacker> blocked the attack, and it hit <Victim>!', image_id=self.image_id)
                self.kill()
            else:
                self.pop()
                if enemy.type == 'Character' and enemy.dead and 'Barbarian' in self.shooter_name:
                    self.shooter.gold += enemy.gold
                    self.shooter.food += enemy.food
                    enemy.gold = enemy.food = 0
    def pop(self):
        self.kill()

class Obstacle(Sprite):
    type = 'Erroneous Generic Obstacle'
    dimensions = (50, 50)
    max_health = 300
    def __init__(self, server, x, y):
        Sprite.__init__(self, *self.groups)
        self.server = server
        self.x = x
        self.y = y
        self.obstacle_rect = pygame.Rect(0, 0, *self.dimensions)
        self.obstacle_rect.center = (self.x, self.y)
        self.health = self.max_health
        self.character = None
    @property
    def channel(self):
        if self.character is None: return None
        return self.character.channel
    def update(self):
        pass
    def getHurt(self, damage, **kwargs):
        if self.health > 0:
            self.health -= damage
            if self.health < 1:
                self.kill()
    def explode(self):
        self.getHurt(80)

class OldObstacle(Obstacle):
    type = 'Erroneous Generic OldObstacle'
    image_id = None
    @property
    def channel(self):
        if self.character is None: return None
        return self.character.channel
    def update(self):
        for p in self.server.users:
            visible_rect = p.character.get_rect(self.obstacle_rect)
            if SCREEN.colliderect(visible_rect):
                p.to_send.append({'action': 'draw_obstacle',
                                            'image': self.image_id,
                                            'coords': visible_rect.center,
                                            'health': self.health,
                                            'max_health': self.max_health})


class Building(Sprite):
    type = 'Erroneous Generic Building'
    info = 'This is the generic information displayed on a building.', 'If you see this, let Aaron know so he can fix it.'
    dimensions = (600, 600)
    max_health = 50
    upgrade_cost = [0, 0]
    def __init__(self, character, coords=None):
        Sprite.__init__(self, *self.groups)
        self.character = character
        self.x, self.y = coords or (self.character.x, self.character.y - 140) 
        self.server = self.character.server
        self.health = self.max_health
        self.state = 'alive'
        self.level = 1
        if self.character.has_builder and self.type != 'Builder\'s':
            self.dimensions = self.dimensions[0] * 0.8, self.dimensions[1] * 0.8
        # pygame.Rects
        self.obstacle_rect = pygame.Rect(0, 0, 200, 200)  # The Building image's rect
        self.obstacle_rect.center = (self.x, self.y)
        self.keeper_rect = pygame.Rect(0, 0, 50, 50)  # The building keeper's rect
        self.keeper_rect.midtop = (self.x, self.obstacle_rect.bottom + 110)
        self.zone_rect = pygame.Rect(0, 0, *self.dimensions)
        self.zone_rect.midtop = (self.x, self.y - 100)  # 100 = half of building image height
        self.init()
    @property
    def channel(self):
        return self.character.channel

    def explode(self):
        self.getHurt(200, name='An explosion')
    
    def gen_options(self, channel):
        def option_complete(l, option):
            option = {'name': option.get('name', 'Unnamed Option'),
                      'food-cost': option.get('food-cost', 0),
                      'gold-cost': option.get('gold-cost', 0),
                      'action': option.get('action', self.Out),
                      'no': option.get('no', 'do this!')}
            option['display'] = option['name']
            if option['gold-cost'] or option['food-cost']:
                option['display'] += ' ('
                if option['gold-cost']:
                    option['display'] += str(option['gold-cost']) + ' gold'
                    if option['food-cost']:
                        option['display'] += ', '
                if option['food-cost']:
                    option['display'] += str(option['food-cost']) + ' food'
                option['display'] += ')'
            if option['name'] == 'Upgrade':
                l.insert(0, option)
            else:
                l.append(option)

        options = []
        if self.state == 'alive':
            heal_cost = math.ceil((self.max_health - self.health) / 2)
            if self.health < self.max_health:
                option_complete(options, {'name': 'Heal Building',
                                      'food-cost': heal_cost,
                                      'action': self.heal,
                                      'no': 'heal this building!'})
            if hasattr(self, 'options'):
                for option in self.options(channel.character):
                    if self.condition(channel.character, option['action']):
                        option_complete(options, option)
        else:
            option_complete(options, {'name': 'Clear',
                                      'gold-cost': 2,
                                      'action': self.clear,
                                      'no': 'clear this building!'})
        option_complete(options, {'name': 'Out', 'action': self.Out})
        return options

    def get_4th_info(self, channel):
        return 'Extra', 'Undefined'
    def init(self):
        pass

    def gen_window(self, channel):
        window = {'text': self.info,
                  '4th_info': self.get_4th_info(channel),
                  'health': (self.health, self.max_health),
                  'object': self,
                  'level': self.level,
                  }
        if self.state != 'alive':
            window['text'] = ('This building is broken.', '')
        window['options'] = self.gen_options(channel)
        channel.window = window
        channel.in_window = True
        channel.Send({'action':'sound', 'sound':'ow'})

    def update(self):
        for p in self.server.users:
            character = p.character
            angle = toolbox.getAngle(self.keeper_rect.centerx, self.keeper_rect.centery, character.rect.centerx, character.rect.centery)  # Look in the player's direction
            visible_rect = character.get_rect(self.zone_rect)
            visible_rect.width = max(self.dimensions[0], self.max_health/2)
            if SCREEN.colliderect(visible_rect):
                p.to_send.append({'action':'draw_building',
                                  'image':'house',
                                  'coords':character.get_coords(self),
                                  'health':self.health,
                                  'max_health':self.max_health,
                                  'angle':angle,
                                  'color':self.channel.color,
                                  'dimensions':self.dimensions,
                                  'type':self.type,
                                  'state':self.state,
                                  'level':self.level})

    def getHurt(self, damage, attacker=Dummy, name='Undefined', **kwargs):
        if self.health > 0 and attacker.channel != self.channel:
            self.health -= damage
            if self.health <= 0:
                self.health = 0
                self.state = 'broken'
                if type(attacker).__name__ == 'Character':
                    attacker.destroyed += 1
                self.channel.add_message(name + ' has broken one of your ' + self.type + 's.', color=(255,0,0))
                for character in self.server.characters:
                    screen = pygame.Rect(0, 0, 1000, 650)
                    screen.center = character.rect.center
                    if screen.colliderect(self.obstacle_rect):
                        character.channel.to_send.append({'action':'sound', 'sound':'building'})
                self.die()
    def die(self):
        pass

    def Out(self, character):
        character.shoot_cooldown = 20
        character.channel.in_window = character.channel.in_innpc_window = False
        character.channel.Send({'action':'sound', 'sound':'cw'})

    def if_is(self, action):
        def if_is(a):  # Bound methods are not equal to functions, even if it's the same method
            return action.__name__ == a
        return if_is
    def condition(self, player, action, **kwargs):
        if_is = self.if_is(action)
        if if_is('heal') and (self.health >= self.max_health or player != self.character):
            return False
        if if_is('buy_inn'):
            for b in player.channel.get_buildings():
                if b.type == 'Inn':
                    return False
        if if_is('buy_running_track'):
            for b in player.channel.get_buildings():
                if b.type == 'Running Track':
                    return False
        if if_is('buy_gym'):
            for b in player.channel.get_buildings():
                if b.type == 'Gym':
                    return False
        if if_is('buy_health_center'):
            for b in player.channel.get_buildings():
                if b.type == 'Health Center':
                    return False
        if if_is('buy_takeout') and player.meal:
            return False
        if (if_is('kick_npc') or if_is('build_house')) and player.channel != self.channel:
            return False
        if (if_is('buy_barrel') or if_is('buy_explosive_barrel')) and player.barrel_health > 0:
            return False
        if if_is('upgrade'):
            if self.type in ('Construction Site', 'Inn') and self.level >= 2:
                return False
            if self.type in ('Running Track', 'Gym', 'Health Center') and self.level >= 3:
                return False
        if self.level == 1 and (if_is('buy_archery_tower') or if_is('buy_robot_factory') or if_is('buy_barrel_maker')):
            return False
        return True

    def do_action(self, character, action, gold_cost=0, food_cost=0, no='do this!'):
        if not self.condition(character, action, pre_action=False):
            character.channel.add_message('It is no longer available to ' + no, color=(0,0,255))
            return self.Out(character)
        if character.food >= food_cost:
            if character.gold >= gold_cost:
                action(character)
                character.gold -= gold_cost
                character.food -= food_cost
                character.spence = ('gold' if gold_cost >= food_cost else 'food')
            else:
                character.channel.add_message('You don\'t have enough gold to ' + no, (255,0,0))
        else:
            if character.gold >= gold_cost:
                character.channel.add_message('You don\'t have enough food to ' + no, (255,0,0))
            else:
                character.channel.add_message('You don\'t have enough gold and food to ' + no, (255,0,0))
        self.Out(character)

    def options(self, player):
        return []        
    def heal(self, player):
        self.health = self.max_health
        player.channel.add_message('You just healed this building.')
    def clear(self, player):
        player.channel.add_message('Cleared building for 2 gold')
        self.kill()
    def upgrade(self, player):
        self.level += 1
        cost = toolbox.format_cost(self.upgrade_cost)
        player.channel.add_message('You upgraded this ' + self.type + ' to level ' + str(self.level) + ' for ' + cost + '.')
        self.level_up(player)
    def level_up(self, player):
        pass

def playsound(self, sound, rect):
    for channel in self.server.users:
        rect = channel.character.get_rect(rect)
        if SCREEN.colliderect(rect):
            channel.Send({'action': 'sound','sound': sound})