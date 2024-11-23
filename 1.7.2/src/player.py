import pygame
import time
import random
import toolbox
from balloon import Balloon, Bolt
from obstacle import Crate, SpikyBush, Gate, TNT, Sappling, Barrel
from building import test_build
from animations import Explosion
from NPC import ArcheryTower
from elements import Sprite, Dummy, SCREEN, playsound

VOWELS = ('a', 'e', 'i', 'o', 'u', 'y')

class Character(Sprite):
    type = 'Character'
    max_health = 100
    dimensions = (50, 50)
    speed = 8
    def __init__(self, channel, x, y):
        # Administration
        Sprite.__init__(self, *self.groups)
        self.channel = channel
        self.server = channel.server
        self.color = channel.color
        self.name = channel.username

        # Game Attributes
        self.x = x
        self.y = y
        self.angle = 0
        self.health = self.max_health
        self.dead = False

        self.shot_speed = 15
        self.resistance = 0
        self.balloon_damage = 10
        self.damage_cost = 30
        self.balloon_speed = 16
        self.speed_cost = 10

        # Cooldowns

        self.hurt_count = 1
        self.shoot_cooldown = 0
        self.barbshoot_cooldown = -1  # -1 because not owned
        self.respawn_count = 0
        self.crate_hold = False
        self.spiky_bush_hold = False

        # Resources
        if self.name in ('f', 'ModestNoob'):
            self.gold = self.food = 1000000
        elif channel.server.gamemode == 'OP':
            self.gold = self.food = 1600
        elif channel.server.gamemode in ('Immediate' , 'Express'):
            self.gold = self.food = 100
        elif channel.server.gamemode == 'Mutated':
            self.gold = self.food = 45
        else:
            self.gold = self.food = 0

        # Extra

        self.has_explosive_barrel = True
        
        self.meal = False
        self.meal_type = 0

        self.crates = 0
        self.spiky_bushes = 0
        self.spence = 'gold'  # What to give back if they deleted the building
        self.garden_xp = 0  # No in-game effect, but displayed at Botanist's Lab
        self.shield_count = 0
        self.shield_angle = 0
        self.has_shield = False
        self.barrel_health = 0
        self.in_barrel = False
        self.barrel_max_health = 0

        # For Alchemist and Rancher
        self.farm = None
        self.mine = None

        # Non-Vanilla VillageWars
        self.invincible = False

        # Statistics
        self.kills = 0
        self.destroyed = 0
        self.deaths = 0
        self.eliminations = 0

    def statistics(self):
        return [self.channel.username, 'kills', self.kills]

    @property
    def rect(self):
        rect = pygame.Rect(0, 0, 50, 50); rect.center = self.x, self.y; return rect
    @property
    def has_builder(self):
        for building in self.channel.get_buildings():
            if building.type == 'Inn' and building.NPC and building.NPC.type == 'Builder':
                return True
            if building.type == 'Builder\'s':
                return True
        return False

    def get_x(self, item):
        return getattr(item, 'x', item) + 500 - self.x
    def get_y(self, item):
        return getattr(item, 'y', item) + 325 - self.y
    def get_coords(self, item):
        return self.get_x(item), self.get_y(item)
    def get_rect(self, rect):
        return pygame.Rect(self.get_coords(rect), rect.size)

    def move_on_axis(self, axis, amount, **kwargs):
        if amount == 0:
            return
        original_value = getattr(self, axis)
        setattr(self, axis, original_value + amount)
        if not self.dead:  # No obstacles when flying
            obstacle = self.server.obstacles.collide(self, self.rect, ignore_friend=['Gate'])
            if obstacle:
                if obstacle.type == 'Spiky bush' and not kwargs.get('hurt'):
                    self.getHurt(1, name='a spiky bush', angle=self.angle + 180, msg='<Victim> fell in <Attacker>.')
                else:
                    setattr(self, axis, original_value)
    def move(self, **kwargs):
        x, y = toolbox.getDir(kwargs.get('angle', self.angle), kwargs.get('speed', self.get_speed()))
        self.x, self.y = round(self.x), round(self.y)
        self.move_on_axis('x', round(x), **kwargs)
        self.move_on_axis('y', round(y), **kwargs)

    def update(self):
        ### Game Logic Side ###

        # Suffocation
        if not self.dead:
            obstacle = self.server.obstacles.collide(self, self.rect, ignore_friend=['Barrel', 'Gate'], ignore=['Spiky bush'])
            if obstacle:
                if obstacle.type == 'Crate':
                    x, y = toolbox.getDir(self.angle + 180, 40)
                    self.x += round(x)
                    self.y += round(y)
                else:
                    self.die(Dummy, msg=self.name + ' suffocated.')

        # Cooldowns
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.hurt_count > 1:
            self.hurt_count -= 1
        if self.shield_count:
            self.shield_count -= 1  # Barbarian Shield
        if self.barbshoot_cooldown:
            self.barbshoot_cooldown -= 1
        if not self.barbshoot_cooldown and not self.dead:
            self.barbshoot()  # Barbarian Crossbow
        if self.respawn_count > 0:
            self.respawn_count -= 1
            if self.respawn_count == 0:
                self.respawn()

        ### Visual Display Side ###

        if self.dead:
            return
        if self.channel.build_to_place:  # Show Building Preview
            self.channel.to_send.append({'action':'preview', 'dimensions':
                            ((self.channel.build_to_place.dimensions[0]*0.8, self.channel.build_to_place.dimensions[1]*0.8) 
                            if self.has_builder else self.channel.build_to_place.dimensions),
                            'ArcheryTower?':self.channel.build_to_place == ArcheryTower})
        barrel_image = ('TNT' if self.has_explosive_barrel else (self.barrel_max_health / (self.barrel_health+1) > 2))
        for p in self.channel.server.users:
            visible_rect = p.character.get_rect(self.rect)
            if SCREEN.colliderect(visible_rect):
                p.to_send.append({'action': 'draw_player',
                        'hurt': int(bool(self.hurt_count - 1)),
                        'coords': visible_rect.center,
                        'angle': self.angle,
                        'color': self.channel.color,
                        'username': self.channel.username,
                        'health': self.health,
                        'max_health': self.max_health,
                        'skin': self.channel.skin,
                        'shield': (self.shield_angle if self.shield_count else None),
                        'in_barrel': (barrel_image, self.in_barrel)})
    def hud(self):
        return {'action':'hud',
                'x':self.x,
                'y':self.y,
                'angle':self.angle,
                'color':self.color,
                'username':self.name,
                'health':self.health,
                'gold':self.gold,
                'food':self.food,
                'max_health':self.max_health,
                'food?':self.meal,
                'type':self.meal_type,
                'crates':self.crates,
                'spiky_bushes':self.spiky_bushes,
                'gametime':time.time() - self.channel.server.starttime}

    def barbshoot(self):
        distance = 650
        angle = None
        for character in self.server.characters:
            if toolbox.getDist(self.x, self.y, character.x, character.y) < distance and character != self:
                angle = toolbox.getAngle(self.x, self.y, character.x, character.y)
                distance = toolbox.getDist(self.x, self.y, character.x, character.y)
        if target_character:
            Bolt(self, angle=angle, msg='<Attacker> shot <Victim> with a barbarian crossbow.')
            self.barbshoot_cooldown = 50

    def left_click(self, mouse):
        if self.in_barrel:
            Barrel(self, self.x, self.y, self.angle, self.barrel_health, self.barrel_max_health, self.has_explosive_barrel)
            self.in_barrel = False
            self.barrel_health = 0
            self.shoot_cooldown = self.shot_speed * 2
            playsound(self, 'shot', self.rect)
            return
        for yard in self.channel.server.resources:
            if yard.HandleInput(mouse, self):
                self.shoot_cooldown = self.shot_speed * 2
                return
        self.shoot()
    def right_click(self, mouse):
        if self.channel.build_to_place:
            if test_build(self):  # Test for whether the building can fit
                building = self.channel.build_to_place(self)  # Create Building object
                self.channel.text = ''
                self.channel.build_to_place = None
                if building.type[0].lower() in VOWELS:
                    self.channel.add_message('You have placed an ' + building.type + '.')
                else:
                    self.channel.add_message('You have placed a ' + building.type + '.')
            else:
                if self.channel.build_to_place.type == 'ArcheryTower':
                    self.channel.add_message('You cannot place an Archery Tower here.', color=(255,0,0))
                else:
                    self.channel.add_message('You cannot place this building here.', color=(255,0,0))
        # Open Building Window
        elif not self.channel.in_window:
            for building in self.server.buildings:
                keeper_rect = self.get_rect(building.keeper_rect)
                building_rect = self.get_rect(building.obstacle_rect)
                if keeper_rect.collidepoint((mouse[0], mouse[1])) or building_rect.collidepoint((mouse[0], mouse[1])):
                    building.gen_window(self.channel)
                    return
                if building.type == 'Inn' and building.NPC and building.character is self:
                    rect = self.get_rect(building.NPC.rect)
                    if rect.collidepoint((mouse[0], mouse[1])):
                        building.NPC.gen_window(self.channel)

    def handle_window(self, keys, mouse):
        self.in_barrel = False
        if not mouse[2]:
            return
        for i, option in enumerate(self.channel.window['options']):
            x = 200
            y = 200 + i * 40
            rect = pygame.Rect(x, y, 600, 50)
            if rect.collidepoint((mouse[0], mouse[1])):
                self.channel.window['object'].do_action(self, option['action'], gold_cost=option['gold-cost'], food_cost=option['food-cost'], condition=option.get('condition', 'True'), no=option['no'])
                return
    def handle_nowindow(self, keys, mouse):
        self.crate_hold = keys[pygame.K_x] and self.crate_hold
        self.spiky_bush_hold = keys[pygame.K_c] and self.spiky_bush_hold

        if self.barrel_health:  # Test Z key for barrel
            before = self.in_barrel
            self.in_barrel = keys[pygame.K_z]
            if self.in_barrel != before:
                playsound(self, 'barrel', self.rect)
        else:
            self.in_barrel = False

        if keys[pygame.K_c]:  # Test C key for spiky bushes or sapplings
            if self.channel.text == 'Press c to place sappling':
                Sappling(self.server, self.x, self.y)
                self.channel.text = ''
            elif self.spiky_bushes and not self.spiky_bush_hold:
                move = toolbox.getDir(self.angle, 80)
                SpikyBush(self, self.x + move[0], self.y + move[1])
                self.spiky_bushes -= 1
            self.spiky_bush_hold = True

        if keys[pygame.K_x]:  # Test X key for crates, gates, and TNT
            if self.channel.text == 'Press x to place gate':
                self.channel.text = ''
                move = toolbox.getDir(self.angle, 100)
                Gate(self, self.x + move[0], self.y + move[1], (45 < self.angle < 135 or -45 > self.angle > -135))  # Gates have 2 orientations
            elif self.channel.text == 'Press x to place TNT':
                self.channel.text = ''
                move = toolbox.getDir(self.angle, 80)
                TNT(self, self.x + move[0], self.y + move[1])
            elif self.crates and not self.crate_hold:
                move = toolbox.getDir(self.angle, 80)
                Crate(self, self.x + move[0], self.y + move[1])
                self.crates -= 1
            self.crate_hold = True

        if keys[pygame.K_DELETE] and self.channel.build_to_place:  # Test DEL key for building deletion
            self.channel.build_to_place = None
            self.channel.text = ''
            if self.spence == 'gold':
                self.channel.add_message('You deleted the building and gained 10 gold.', color=(255,100,0))
                self.gold += 10
            else:
                self.channel.add_message('You deleted the building and gained 10 food.', color=(255,100,0))
                self.food += 10

        if mouse[2]:
            self.left_click(mouse)
        if mouse[4]:
            self.right_click(mouse)

    def HandleInput(self, keys, mouse):
        self.angle = toolbox.getAngle(500, 325, mouse[0], mouse[1])  # Look towards mouse pointer
        if keys[pygame.K_SPACE] and not (self.in_barrel or self.channel.in_window):  # Move forwards
            self.move(angle=self.angle)
        if self.dead:
            return
        # Handle in window and not in window input
        self.handle_window(keys, mouse) if self.channel.in_window else self.handle_nowindow(keys, mouse)

    def eat(self):
        self.meal = False
        self.health = self.max_health
        self.channel.add_message('You ate your meal, your health bar is now full again.')
        
    def getHurt(self, damage, attacker=Dummy, name='Undefined', angle=0, knockback=0, msg='<Attacker> splashed <Victim> too hard.'):
        if self.in_barrel:
            if self.has_explosive_barrel:  # If explosive barrel equipped, it explodes
                self.in_barrel = False
                self.barrel_health = 0
                barrel = Barrel(self, self.x, self.y, self.angle, health=15, max_health=15, explosive=True)
                barrel.explode()
            else:
                self.barrel_health -= damage
                if self.barrel_health <= 0 or 'blown up' in msg:
                    self.barrel_health = 0
                    self.in_barrel = False
                    playsound(self, 'barrel', self.rect)
            return
        if (self.has_shield and random.randint(0, 2) == 0) or self.invincible:
            self.shield_angle = angle + 180
            self.shield_count = 20
            playsound(self, 'bump', self.rect)
            return self.shield_angle + random.randint(-20, 20)
        self.channel.in_window = False
        self.channel.window = None
        self.health -= max(0, damage - self.resistance)
        self.move(angle=angle, speed=knockback, hurt=True)
        self.hurt_count = 8
        if self.health <= 0:
            self.die(attacker, name=name, msg=msg)

    def die(self, attacker, name='Undefined', msg='<Attacker> splashed <Victim> too hard.'):
        Explosion(self)
        playsound(self, 'die', self.rect)
        self.kill()
        self.channel.text = ''
        self.channel.build_to_place = None
        self.dead = True
        self.deaths += 1
        self.barrel_health = 0
        self.crates = 0
        self.spiky_bushes = 0
        self.meal = False
        if attacker.type == 'Character': attacker.kills += 1
        msg = msg.replace('<Attacker>', name).replace('<Victim>', self.name)
        for channel in self.channel.server.users:
            channel.add_message(msg, color=((255,205,0) if channel != self.channel else (255,0,0)))
        if len(self.channel.get_buildings()) > 0:
            self.respawn_count = 200
        else:
            self.elimination()

    def elimination(self, attacker):
        # Elimination
        if attacker.type == 'Character':
            attacker.eliminations += 1
        still_alive = []
        self.channel.add_message(username + ' has eliminated you from the game!', color=(255,0,0))
        for channel in self.channel.server.users:
            if channel != self.channel:
                channel.add_message(username + ' has eliminated ' + self.channel.username + ' from the game.')
            if not channel.character.dead or channel.character.respawn_count > 0:
                still_alive.append(channel)
        if len(still_alive) == 1:
            self.channel.server.terminate(still_alive[0])

    def shoot(self):
        if self.shoot_cooldown == 0:
            balloon = Balloon(self)
            self.shoot_cooldown = self.shot_speed
            playsound(self, 'shot', self.rect)

    def respawn(self):
        self.dead = False
        self.add(self.server.dynamics)  # Sprite.add
        self.x, self.y = self.server.STARTING_COORDS[self.channel.quadrant]
        self.channel.add_message('You respawned. You respawn as long as you have buildings alive.', color=(128,255,5))
        self.health = self.max_health


    def get_speed(self):
        '''
        Compensates for differences in connectino speeds.
        This function ensures no one player moves faster than another simply because they have a faster connection.
        '''
        return ((max(self.speed, 16) if self.dead else self.speed) * 30) / max(self.channel.fps, 5)
