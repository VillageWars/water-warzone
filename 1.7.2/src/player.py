import pygame
import time
import random
import toolbox
from balloon import Balloon, Bolt, TraitorBalloon
from obstacle import *
from building import *
from animations import *
from NPC import ArcheryTower

from elements import Sprite, Dummy

class Character(Sprite):
    type = 'Character'
    max_health = 100
    dimensions = (50, 50)
    speed = 8
    def __init__(self, channel, x, y):
        Sprite.__init__(self, *self.groups)
        self.channel = channel
        self.server = channel.server
        self.x = x
        self.y = y
        
        self.angle = 0
        self.moving = self.speed
        self.health = self.max_health
        self.hurt_count = 1
        self.dead = False
        self.explosive = True

        self.name = self.channel.username
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

        self.shoot_cooldown = 0
        self.barbshoot_cooldown = -1
        self.shot_speed = 15
        self.strength = 0
        self.balloon_damage = 10
        self.damage_cost = 30
        self.balloon_speed = 16
        self.speed_cost = 10
        self.crate_cooldown = 0
        self.crate_hold = False
        self.spiky_bush_hold = False
        self.invincible = False

        self.respawn_count = 0
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

        self.traitor = False

        ### Stat Side ###

        self._kills = 0
        self._destroyed = 0
        self._deaths = 0
        self._eliminations = 0

    ### Info Side - Statistics (Soon to be updated) ###

    @property
    def kills(self):
        return self._kills
    @kills.setter
    def kills(self, value):
        self._kills = value
    @property
    def destroyed(self):
        return self._destroyed
    @destroyed.setter
    def destroyed(self, value):
        self._destroyed = value
    @property
    def deaths(self):
        return self._deaths
    @deaths.setter
    def deaths(self, value):
        self._deaths = value
    @property
    def eliminations(self):
        return self._eliminations
    @eliminations.setter
    def eliminations(self, value):
        self._eliminations = value
    @property
    def statistics(self):
        return (self.channel.username, 'kills', self.kills)
    @property
    def x_flip(self):
        return 500 - self.x
    @property
    def y_flip(self):
        return 325 - self.y
    @property
    def rect(self):
        rect = pygame.Rect(0, 0, 50, 50); rect.center = self.x, self.y; return rect
    @property
    def has_builder(self):
        true = False
        for inn in self.channel.get_buildings():
            if type(inn).__name__ == 'Inn':
                if type(inn.NPC).__name__ == 'Builder':
                    true = True
                    break
            if inn.type == 'Builder\'s':
                true = True
                break
        return true

    def get_x(self, item):
        if hasattr(item, 'x'):
            return item.x + self.x_flip
        else:
            return item + self.x_flip
    def get_y(self, item):
        if hasattr(item, 'y'):
            return item.y + self.y_flip
        else:
            return item + self.y_flip
    def get_coords(self, item):
        return self.get_x(item), self.get_y(item)
    def get_rect(self, rect):
        return pygame.Rect(self.get_coords(rect), rect.size)

    def move_x(self, amount, **kwargs):
        self.x += amount
        if not self.dead:  # No obstacles when flying
            obstacle = self.server.obstacles.collide(self, self.rect, ignore=['Gate'])
            if obstacle:
                if obstacle.type == 'Spiky bush' and not kwargs.get('hurt'):
                    self.getHurt(1, 'a spiky bush', self.angle + 180, 4, msg='<Victim> fell in <Attacker>.')
                else:
                    self.x -= amount

    def move_y(self, amount, **kwargs):
        self.y += amount
        if not self.dead:  # No obstacles when flying
            obstacle = self.server.obstacles.collide(self, self.rect, ignore=['Gate'])
            if obstacle:
                if obstacle.type == 'Spiky bush' and not kwargs.get('hurt'):
                    self.getHurt(1, 'a spiky bush', self.angle + 180, 4, msg='<Victim> fell in <Attacker>.')
                else:
                    self.y -= amount
             
    def move(self, angle):
        x, y = toolbox.getDir(angle, self.get_speed())
        self.x, self.y = round(self.x), round(self.y)
        self.move_x(round(x))
        self.move_y(round(y))

    def update(self):
        if self.channel.build_to_place:
            self.channel.to_send.append({'action':'preview', 'dimensions':
                            ((self.channel.build_to_place.dimensions[0]*0.8, self.channel.build_to_place.dimensions[1]*0.8) 
                            if self.has_builder else self.channel.build_to_place.dimensions),
                            'ArcheryTower?':self.channel.build_to_place == ArcheryTower})
        if not self.dead:
            obstacle = self.server.obstacles.collide(self, self.rect, ignore=['Barrel', 'Gate'])
            if obstacle:
                if obstacle.type == 'Crate':
                    x, y = toolbox.getDir(self.angle + 180, 40)
                    self.x += round(x)
                    self.y += round(y)
                else:
                    self.suffocate()


        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.crate_cooldown > 0:
            self.crate_cooldown -= 1
        if self.hurt_count > 1:
            self.hurt_count -= 1
        if self.shield_count:
            self.shield_count -= 1
        if self.barbshoot_cooldown:
            self.barbshoot_cooldown -= 1

        

        if self.respawn_count > 0:
            self.respawn_count -= 1
            if self.respawn_count == 0:
                self.respawn()
                
        if not self.dead:

            if not self.barbshoot_cooldown:
                self.barbshoot()
            
            for p in self.channel.server.players:
                if not p.pending:
                        
                    barrel_image = self.barrel_max_health / (self.barrel_health+1)>2
                    if self.explosive:
                        barrel_image = 'TNT'
                    p.to_send.append({'action':'draw_player',
                                'hurt':int(bool(self.hurt_count - 1)),
                                'coords':(p.character.get_x(self), p.character.get_y(self)),
                                'angle':self.angle,
                                'color':self.channel.color,
                                'username':self.channel.username,
                                'health':self.health,
                                'max_health':self.max_health,
                                'skin':self.channel.skin,
                                'shield':(self.shield_angle if self.shield_count else None),
                                'in_barrel':(barrel_image, self.in_barrel)})
                    

    def hud(self):
        return {'action':'hud',
                'x':self.x,
                'y':self.y,
                'angle':self.angle,
                'color':self.channel.color,
                'username':self.channel.username,
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
        dire = 650
        player = None
        for p in self.channel.server.players:
            if p.pending:
                if toolbox.getDist(self.x, self.y, p.character.x, p.character.y) < dire and p != self.channel:
                    player = p.character
                    dire = toolbox.getDist(self.x, self.y, p.character.x, p.character.y)
        if player:
            self.angle = toolbox.getAngle(self.x, self.y, player.x, player.y)
            Bolt(archer=self)
            self.barbshoot_cooldown = 50
        

    def HandleInput(self, keys, mouse):
        if self.barrel_health and not self.dead and not self.channel.in_window and not self.channel.in_innpc_window:
            change = False
            if self.in_barrel:
                if not keys[pygame.K_z]:
                    change = True
            else:
                if keys[pygame.K_z]:
                    change = True
            if change:
                self.in_barrel = not self.in_barrel
                for p in self.channel.server.players:
                    if not p.pending:
                        screen = pygame.Rect(0, 0, 1000, 650)
                        rect = pygame.Rect(0, 0, 1, 1)
                        rect.size = self.rect.size
                        rect.topleft = (p.character.get_x(self), p.character.get_y(self))
                        if screen.colliderect(rect):
                            p.to_send.append({'action':'sound','sound':'barrel'})
        else:
            self.in_barrel = False

        # For mutated gamemode
        beg_building = self.channel.build_to_place
        beg_gold = self.gold
        beg_food = self.food

        if not self.channel.in_window:
            if not keys[pygame.K_x] and self.crate_hold:
                self.crate_hold = False
            if not keys[pygame.K_c] and self.spiky_bush_hold:
                self.spiky_bush_hold = False

            self.angle = toolbox.getAngle(500, 325, mouse[0], mouse[1])

            #if keys[pygame.K_a]:
            #    self.channel.achievement('You pressed the A button!')
            #if keys[pygame.K_8]:
            #    self.channel.achievement('You pressed the 8 button!')
                
            if keys[pygame.K_SPACE] and not self.in_barrel:
                self.move(self.angle)

            if keys[pygame.K_c] and not self.dead:  # C for spiky bushes or sapplings
                if self.channel.text == 'Press c to place sappling':
                    Sappling(self.channel.server, self.x, self.y)
                    self.channel.text = ''
                    self.spiky_bush_hold = True
                elif self.spiky_bush_hold == False and self.spiky_bushes > 0:
                    x, y = self.x, self.y
                    move = toolbox.getDir(self.angle, 80)
                    x += move[0]
                    y += move[1]
                        
                    SpikyBush(self, x, y)
                    self.spiky_bush_hold = True
                    self.spiky_bushes -= 1

            if keys[pygame.K_x]:
                if self.channel.text == 'Press x to place gate':
                    self.channel.text = ''
                    x, y = self.x, self.y
                    move = toolbox.getDir(self.angle, 100)
                    x += move[0]
                    y += move[1]
                    rotated = False
                    if 45 < self.angle < 135 or -45 > self.angle > -135:
                        rotated = True
                    
                    Gate(self, x, y, rotated)
                    self.crate_hold = True

                elif self.channel.text == 'Press x to place TNT':
                    self.channel.text = ''
                    x, y = self.x, self.y
                    move = toolbox.getDir(self.angle, 80)
                    x += move[0]
                    y += move[1]
                    
                    TNT(self, x, y)
                    self.crate_hold = True
                    
                elif not self.dead and self.crate_hold == False and self.crates > 0:
                    x, y = self.x, self.y
                    move = toolbox.getDir(self.angle, 80)
                    x += move[0]
                    y += move[1]
                    
                    Crate(self, x, y)
                    self.crate_hold = True
                    self.crates -= 1

            if keys[pygame.K_DELETE] and self.channel.build_to_place != None:
                self.channel.build_to_place = None
                self.channel.text = ''
                if self.spence == 'gold':
                    self.channel.message = 'You deleted the building, you gain 10 gold.'
                    self.gold += 10
                else:
                    self.channel.message = 'You deleted the building, you gain 10 food.'
                    self.food += 10
                self.channel.message_count = 150
                self.channel.message_color = (255,100,0)

            
            if mouse[2] and not self.dead:
                if self.in_barrel:
                    Barrel(self, self.x, self.y, self.angle, self.barrel_health, self.barrel_max_health, self.explosive)
                    self.in_barrel = False
                    self.barrel_health = 0
                    self.shoot_cooldown = self.shot_speed * 2
                    for p in self.channel.server.users:
                        screen = pygame.Rect(0, 0, 1000, 650)
                        rect = pygame.Rect(p.character.get_coords(self.rect), self.rect.size)
                        if screen.colliderect(rect):
                            p.to_send.append({'action':'sound','sound':'shot'})
                    return
                if self.dead == False:
                    for farm in self.channel.server.resources:
                        if farm.HandleInput(mouse, self):
                            self.shoot_cooldown = self.shot_speed * 2
                self.shoot()  # Automatically cancels if shoot cooldown isn't ready

        if self.channel.in_window and mouse[2] and not self.dead:  # Building or InnPC window
            for i, option in enumerate(self.channel.window['options']):
                x = 200
                y = 200 + i * 40
                rect = pygame.Rect(x, y, 600, 50)
                if rect.collidepoint((mouse[0], mouse[1])):
                    self.channel.window['object'].do_action(self, option['action'], option['gold-cost'], option['food-cost'], option['no'])
                    break
        if mouse[4] and not self.dead:  # Right click
            if self.channel.build_to_place != None:
                if test_build(self):  # Place Building
                    b = self.channel.build_to_place(self)  # Create Building object
                    self.channel.text = ''
                    self.channel.build_to_place = None
                    if b.type[0].lower() in ('a', 'e', 'i', 'o', 'u', 'y'):
                        self.channel.add_message('You have placed an ' + b.type + '.')
                    else:
                        self.channel.add_message('You have placed a ' + b.type + '.')
                else:
                    if self.channel.build_to_place.__name__ == 'ArcheryTower':
                        self.channel.add_message('You cannot place an Archery Tower here.', color=(255,0,0))
                    else:
                        self.channel.add_message('You cannot place this building here.', color=(255,0,0))

            elif not self.in_barrel and not self.channel.in_window and not self.channel.in_innpc_window:  # Open Building Window
                for building in self.channel.server.buildings:
                    keeper_rect = self.get_rect(building.keeper_rect)
                    building_rect = self.get_rect(building.obstacle_rect)
                    if keeper_rect.collidepoint((mouse[0], mouse[1])) or building_rect.collidepoint((mouse[0], mouse[1])):
                        building.gen_window(self.channel)
                    if type(building) == Inn and building.NPC is not None and building.character == self:
                        rect = self.get_rect(building.NPC.rect)
                        if rect.collidepoint((mouse[0], mouse[1])):
                            building.NPC.gen_window(self.channel)
        if self.channel.message == 'The Gold Discovery Rate is at its maximum!' and not [b for b in self.channel.get_buildings() if b.type == 'Miner\'s Guild']:
            self.channel.message = 'Get a Miner\'s Guild first.'
        if self.channel.message == 'The Food Production Rate is at its maximum!' and not [b for b in self.channel.get_buildings() if b.type == 'Farmer\'s Guild']:
            self.channel.message = 'Get a Farmer\'s Guild first.'

        if self.channel.server.gamemode == 'Mutated' and self.channel.build_to_place != beg_building and self.channel.build_to_place is not None:
            self.channel.message = 'No buying buildings in Mutated. Returned %s gold, %s food' % (beg_gold - self.gold, beg_food - self.food)
            self.channel.message_color = (255,128,0)
            self.channel.build_to_place = beg_building
            self.gold = beg_gold
            self.food = beg_food
            self.channel.text = ''



    def eat(self):
        if not self.dead:
            self.meal = False
            self.health = self.max_health
            self.channel.message = 'You ate your meal, your health bar is now full again.'
            self.channel.message_color = (255,205,0)
    def dine_in(self):
        self.health = self.max_health
        
    def getHurt(self, damage, attacker=Dummy, name='Undefined', angle=0, knockback=0, msg='<Attacker> splashed <Victim> too hard.'):
        if self.in_barrel:
            if self.explosive:
                self.in_barrel = False
                self.barrel_health = 0
                barrel = Barrel(self, self.x, self.y, self.angle, health=15, max_health=15, explosive=True)
                barrel.explode()
            else:
                self.barrel_health -= damage
                if self.barrel_health <= 0 or 'blown up' in msg:
                    self.barrel_health = 0
                    self.in_barrel = False
                    for p in self.channel.server.users:
                        screen = pygame.Rect(0, 0, 1000, 650)
                        rect = p.character.get_rect(self.rect)
                        if screen.colliderect(rect):
                            p.to_send.append({'action':'sound','sound':'barrel'})
            return
        if (self.has_shield and random.randint(0, 2)) or self.invincible:
            self.shield_angle = angle + 180
            self.shield_count = 20
            for p in self.channel.server.users:
                screen = pygame.Rect(0, 0, 1000, 650)
                rect = p.character.get_rect(self.rect)
                if screen.colliderect(rect):
                    p.to_send.append({'action':'sound','sound':'bump'})
            return self.shield_angle + random.randint(-20, 20)
        final_damage = (damage - self.strength)
        if final_damage < 0:
            final_damage = 0
        self.health -= final_damage
        x, y = toolbox.getDir(angle, knockback)
        self.move_x(x, hurt=True)
        self.move_y(y, hurt=True)
        self.hurt_count = 8
        if self.health <= 0:
            Explosion(self)
            for p in self.channel.server.players:
                screen = pygame.Rect(0, 0, 1000, 650)
                screen.center = p.character.rect.center
                if screen.colliderect(self.rect):
                    p.to_send.append({'action':'sound', 'sound':'die'})
            self.channel.text = ''
            self.channel.build_to_place = None
            self.dead = True
            self.kill()
            self.deaths += 1
            self.barrel_health = 0
            self.crates = 0
            self.spiky_bushes = 0
            self.meal = False
            self.moving = 16
            if isinstance(attacker, Character):
                attacker.kills += 1
            msg = msg.replace('<Attacker>', name).replace('<Victim>', self.channel.username)
            for channel in self.channel.server.players:
                channel.message = msg
                channel.message_count = 150
                channel.message_color = (255,205,0)
                if channel == self.channel:
                    channel.message_color = (255,0,0)
            if len(self.channel.get_buildings()) != 0:
                self.respawn_count = 200
            else:
                if not isinstance(attacker, str):
                    attacker.eliminations += 1
                guys = []
                for channel in self.channel.server.players:
                    channel.message = username + ' has eliminated ' + self.channel.username + ' from the game.'
                    channel.message_count = 150
                    channel.message_color = (255,205,0)
                    if channel == self.channel:
                        channel.message = username + ' has eliminated you from the game!'
                        channel.message_color = (255,0,0)
                    if channel.character.dead == False:
                        guys.append(channel)
                    elif channel.character.respawn_count > 0:
                        guys.append(channel)
                if len(guys) == 1:
                    self.channel.server.terminate(guys[0])

        self.channel.in_window = False
        self.channel.window = None

    def suffocate(self):
        Explosion(self)
        for p in self.channel.server.players:
            screen = pygame.Rect(0, 0, 1000, 650)
            screen.center = p.character.rect.center
            if screen.colliderect(self.rect):
                p.to_send.append({'action':'sound', 'sound':'die'})
        self.channel.text = ''
        self.channel.build_to_place = None
        self.dead = True
            
        self.deaths += 1
        self.crates = 0
        self.meal = False
        self.moving = 16

        for channel in self.channel.server.players:
            channel.message = self.channel.username + ' suffocated.'
            channel.message_count = 150
            channel.message_color = (255,205,0)
            if channel == self.channel:
                channel.message_color = (255,0,0)

        if len(self.channel.get_buildings()) != 0:
            self.respawn_count = 200
        else:
            guys = []
            for channel in self.channel.server.players:
                channel.message = self.channel.username + ' has been eliminated from the game by suffocation.'
                channel.message_count = 150
                channel.message_color = (255,205,0)
                if channel == self.channel:
                    channel.message = 'You suffocated and were eliminated from the game!'
                    channel.message_color = (255,0,0)
                if channel.character.dead == False:
                    guys.append(channel)
                elif channel.character.respawn_count > 0:
                    guys.append(channel)
            if len(guys) == 1:
                self.channel.server.terminate(guys[0])



    def shoot(self):
        if self.shoot_cooldown == 0:
            balloon = (Balloon(self) if not self.traitor else TraitorBalloon(self))
            self.shoot_cooldown = self.shot_speed
            for p in self.channel.server.players:
                if not p.pending:
                    screen = pygame.Rect(0, 0, 1000, 650)
                    screen.center = p.character.rect.center
                    if screen.colliderect(self.rect):
                        p.to_send.append({'action':'sound', 'sound':'shot'})

    def respawn(self):
        self.dead = False
        self.add(self.server.dynamics)
        self.x, self.y = self.server.ST_COORDS[self.channel.loc_number]
        self.moving = self.speed
        self.channel.message = 'You respawned. You respawn as long as you have buildings alive.'
        self.channel.message_count = 150
        self.channel.message_color = (128,255,5)
        self.health = self.max_health


    def get_speed(self):
        speed = self.moving
        speed /= self.channel.fps
        speed *= 30

        return speed