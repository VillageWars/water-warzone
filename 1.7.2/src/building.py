import pygame
import toolbox as t
import math
import random as r
from NPC import *
import os
#from InnPC import *

try:
    DISHES = len(os.listdir('../assets/meals')) - 2
except:
    DISHES = 1

class Building(pygame.sprite.Sprite):
    dimensions = (600, 600)
    def __init__(self, server, x, y, owner):
        '''
        owner must be client channel, not character.

        '''
        try:
            pygame.sprite.Sprite.__init__(self, self.gp)
        except:
            pygame.sprite.Sprite.__init__(self, pygame.sprite.Group())
        self.x = x
        self.y = y
        self.type = self.__class__.__qualname__
        self.server = server
        self.level = 1
        self.owner = owner
        self.max_health = self.health = 50
        self.state = 'alive'
        self.dimensions = type(self).dimensions

        self.p = pygame.Surface((200, 200))
        self.innerrect = self.p.get_rect(center=(x,y))
        self.rect = pygame.Surface((50, 50)).get_rect(midtop=(self.innerrect.midbottom[0], self.innerrect.midbottom[1] + 110))

        

    def post_init(self, rect):
        self.dimensions = type(self).dimensions
        self.dimensions = rect.size
        self.dim_rect = rect
        self.server.building_blocks.append(self.dim_rect)
        self.server.obs.append(self)

    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            channel.window = {'text':self.info,
                              '4th_info':('Number of non-broken buildings', str(len(channel.get_buildings()))),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.heal), (1, self.Out)],
                              'simp':['Heal (5 food)', 'Out']}
        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              'upgradable':False,
                              '4th_info':('Number of non-broken buildings', str(len(channel.get_buildings()))),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 gold)', 'Out']}
        

    def update(self):
        

        for p in self.server.players:
            if not p.pending:
                player = p.character
                angle = t.getAngle(self.rect.x, self.rect.y, player.x, player.y)

                screen = pygame.Rect(0, 0, 1000, 650)
                rect = pygame.Rect(0, 0, 1, 1)
                rect.size = self.dim_rect.size
                rect.topleft = (p.character.get_x(self.dim_rect), p.character.get_y(self.dim_rect))
                if screen.colliderect(rect):
                    p.to_send.append({'action':'draw_building',
                        'image':'house',
                        'coords':(player.get_x(self), player.get_y(self)),
                        'health':self.health,
                        'max_health':self.max_health,
                        'angle':angle,
                        'color':self.owner.color,
                        'dimensions':self.dimensions,
                        'type':self.type,
                        'state':self.state,
                        'level':self.level})



    def getHurt(self, damage, attacker):
        
        if self.health > 0 and attacker != self.owner.character:
            self.health -= damage
            if self.health < 1:
                self.state = 'broken'
                if attacker.__class__.__name__ == 'Character':
                    self.owner.message = attacker.channel.username + ' has broken one of your ' + self.type + 's.'
                    attacker.destroyed += 1
                else:
                    self.owner.message = attacker + ' has broken one of your ' + self.type + 's.'
                self.owner.message_count = 150
                self.owner.message_color = (255,0,0)
                self.health = 0

                self.die()
                for p in self.server.players:
                    screen = pygame.Rect(0, 0, 1000, 650)
                    screen.center = p.character.rect.center
                    if screen.colliderect(self.rect):
                        p.to_send.append({'action':'sound', 'sound':'building'})

    def die(self):
        pass

    def isBuilding(self):
        return True


    def Out(self, character):
        
        character.channel.in_window = False
        character.shoot_cooldown = 20
        character.channel.to_send.append({'action':'sound', 'sound':'cw'})


    def heal(self, player):
        if player != self.owner.character:
            player.channel.message = "You can't heal someone else's building!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        
        elif player.food > 4:
            if self.health < self.max_health:
                self.health += 10
                if self.health > self.max_health:
                    self.health = self.max_health
                player.channel.message = 'You just healed this building 10 health for 5 food.'
                player.channel.message_count = 120
                player.channel.message_color = (255,205,0)
                player.food -= 5
            else:
                player.channel.message = 'This building is already at full health!'
                player.channel.message_count = 150
                player.channel.message_color = (50,50,255)
        else:
            player.channel.message = "You don't have enough food to heal this building!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)


    def clear(self, player):
        self.Out(player)
        if player.gold > 1:
            player.channel.message = 'Cleared building for 2 gold'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.gold -= 2
            if self.dim_rect in self.server.building_blocks:
                self.server.building_blocks.remove(self.dim_rect)
            if self in self.server.obs:
                self.server.obs.remove(self)
            self.kill()
            
        else:
            player.channel.message = "You don't have enough gold to clear this building!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        



class CentralBuilding(Building):
    dimensions = (675, 550)
    def __init__(self, server, x, y, owner, rect=None):
        Building.__init__(self, server, x, y, owner)
        self.type = 'Central Building'
        self.max_health = self.health = 420
        self.dimensions = type(self).dimensions
        self.info = ('The Central Building is for buying other buildings.', 'If all your buildings are destroyed, you will not respawn.')

        if rect is None:
            rect = pygame.Rect(0, 0, 675, 550)
            rect.midtop = (x, y-round(self.p.get_height()/2))
        self.post_init(rect)


    def update(self):
        Building.update(self)
        if False: # Makes building move, lol
            self.dim_rect.x += 3
            self.rect.x += 3
            self.x += 3
            self.innerrect.x += 3

    
        
        
    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            channel.window = {'text':self.info,
                              '4th_info':('Number of non-broken buildings', str(len(channel.get_buildings()))),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.heal), (1, self.buy_central_building), (2, self.buy_fitness_center), (3, self.buy_balloonist), (4, self.buy_farmers_guild), (5, self.buy_miners_guild), (6, self.buy_construction_site), (7, self.buy_restaurant), (8, self.buy_inn), (9, self.Out)],
                              'simp':['Heal (5 food)', 'Portable Central Building (10 gold, 10 food)', 'Fitness Center (50 food)', 'Balloonist (30 gold)', "Farmer's Guild (25 food)", "Miner's Guild (25 gold)", 'Construction Site (60 gold)', 'Restaurant (80 food)', 'Inn (100 food)', 'Out']}
        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              'upgradable':False,
                              'health':(self.health, self.max_health),
                              'building':self,
                              '4th_info':('Number of non-broken buildings', str(len(channel.get_buildings()))),
                              'level':self.level,
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 gold)', 'Out']}

    def buy_central_building(self, player):
        if player.food > 9:
            if player.gold > 9:

                player.channel.text = 'Right click to place building'
                player.channel.build_to_place = PortableCentralBuilding
                player.channel.message = 'You just bought a Portable Central Building for 10 gold and 10 food.'
                player.channel.message_count = 150
                player.channel.message_color = (255,205,0)
                player.gold -= 10
                player.food -= 10
            else:
                player.channel.message = "You don't have enough gold to buy this!"
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
        
        else:
            if player.gold > 9:
                player.channel.message = "You don't have enough food to buy this!"
            else:
                player.channel.message = "You can't afford this building!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'gold'

    def buy_fitness_center(self, player):
        if player.food > 49:

            player.channel.text = 'Right click to place building'
            player.channel.build_to_place = FitnessCenter
            player.channel.message = 'You just bought a Fitness Center for 50 food.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.food -= 50
        else:
            player.channel.message = "You don't have enough food to buy this!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'food'

    def buy_farmers_guild(self, player):
        if player.food > 24:

            player.channel.text = 'Right click to place building'
            player.channel.build_to_place = FarmersGuild
            player.channel.message = "You just bought a Farmer's Guild for 25 food."
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.food -= 25
        else:
            player.channel.message = "You don't have enough food to buy this!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'food'

    def buy_miners_guild(self, player):
        if player.gold > 24:

            player.channel.text = 'Right click to place building'
            player.channel.build_to_place = MinersGuild
            player.channel.message = "You just bought a Miner's Guild for 25 gold."
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.gold -= 25
        else:
            player.channel.message = "You don't have enough gold to buy this!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'gold'
        


    def buy_balloonist(self, player):
        if player.gold > 29:

            player.channel.text = 'Right click to place building'
            player.channel.build_to_place = Balloonist
            player.channel.message = 'You just bought a Balloonist for 30 gold.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.gold -= 30
        else:
            player.channel.message = "You don't have enough gold to buy this!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'gold'

    def buy_construction_site(self, player):
        if player.gold > 59:

            player.channel.text = 'Right click to place building'
            player.channel.build_to_place = ConstructionSite
            player.channel.message = 'You just bought a Construction Site for 60 gold.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.gold -= 60
        else:
            player.channel.message = "You don't have enough gold to buy this!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'gold'
    def buy_restaurant(self, player):
        if player.food > 79:

            player.channel.text = 'Right click to place building'
            player.channel.build_to_place = Restaurant
            player.channel.message = 'You just bought a Restaurant for 80 food.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.food -= 80
        else:
            player.channel.message = "You don't have enough food to buy this!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'food'

    def buy_inn(self, player):

        
        yes = True
        for b in player.channel.get_buildings():
            if b.type == 'Inn':
                yes = False
                player.channel.message = 'You already have an Inn! You can only have one at a time.'
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
        if yes:
            if player.food > 99:

                player.channel.text = 'Right click to place building'
                player.channel.build_to_place = Inn
                player.channel.message = 'You just bought an Inn for 100 food.'
                player.channel.message_count = 150
                player.channel.message_color = (255,205,0)
                player.food -= 100
            else:
                player.channel.message = "You don't have enough food to buy this!"
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'food'



    


class PortableCentralBuilding(Building):
    dimensions = (560, 560)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.type = 'Portable Central Building'
        self.max_health = self.health = 110
        self.dimensions = type(self).dimensions
        self.info = ('This building works the same way as the regular Central Building,', 'so you can use it as a portable central building.')

        self.post_init(rect)


    def update(self):
        Building.update(self)



    
        
        
    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            channel.window = {'text':self.info,
                              '4th_info':('Number of non-broken buildings', str(len(channel.get_buildings()))),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.heal), (1, self.buy_central_building), (2, self.buy_fitness_center), (3, self.buy_balloonist), (4, self.buy_farmers_guild), (5, self.buy_miners_guild), (6, self.buy_construction_site), (7, self.buy_restraunt), (8, self.buy_inn), (9, self.Out)],
                              'simp':['Heal (5 food)', 'Portable Central Building (10 gold, 10 food)', 'Fitness Center (50 food)', 'Balloonist (30 gold)', "Farmer's Guild (25 food)", "Miner's Guild (25 gold)", 'Construction Site (60 gold)', 'Restaurant (80 food)', 'Inn (100 food)', 'Out']}
        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              'upgradable':False,
                              'health':(self.health, self.max_health),
                              'building':self,
                              '4th_info':('Number of non-broken buildings', str(len(channel.get_buildings()))),
                              'level':self.level,
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 gold)', 'Out']}

    def buy_central_building(self, player):
        if player.food > 9:
            if player.gold > 9:
    
                player.channel.text = 'Right click to place building'
                player.channel.build_to_place = PortableCentralBuilding
                player.channel.message = 'You just bought a Portable Central Building for 10 gold and 10 food.'
                player.channel.message_count = 150
                player.channel.message_color = (255,205,0)
                player.gold -= 10
                player.food -= 10
            else:
                player.channel.message = "You don't have enough gold to buy this!"
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
        
        else:
            if player.gold > 9:
                player.channel.message = "You don't have enough food to buy this!"
            else:
                player.channel.message = "You can't afford this building!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'gold'
    

    def buy_fitness_center(self, player):
        if player.food > 49:

            player.channel.text = 'Right click to place building'
            player.channel.build_to_place = FitnessCenter
            player.channel.message = 'You just bought a Fitness Center for 50 food.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.food -= 50
        else:
            player.channel.message = "You don't have enough food to buy this!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'food'

    def buy_inn(self, player):

        
        yes = True
        for b in player.channel.get_buildings():
            if b.type == 'Inn':
                yes = False
                player.channel.message = 'You already have an Inn! You can only have one at a time.'
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
        if yes:
            if player.food > 99:

                player.channel.text = 'Right click to place building'
                player.channel.build_to_place = Inn
                player.channel.message = 'You just bought an Inn for 100 food.'
                player.channel.message_count = 150
                player.channel.message_color = (255,205,0)
                player.food -= 100
            else:
                player.channel.message = "You don't have enough food to buy this!"
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'food'

    def buy_farmers_guild(self, player):
        if player.food > 24:

            player.channel.text = 'Right click to place building'
            player.channel.build_to_place = FarmersGuild
            player.channel.message = "You just bought a Farmer's Guild for 25 food."
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.food -= 25
        else:
            player.channel.message = "You don't have enough food to buy this!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'food'

    def buy_miners_guild(self, player):
        if player.gold > 24:

            player.channel.text = 'Right click to place building'
            player.channel.build_to_place = MinersGuild
            player.channel.message = "You just bought a Miner's Guild for 25 gold."
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.gold -= 25
        else:
            player.channel.message = "You don't have enough gold to buy this!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'gold'
        


    def buy_balloonist(self, player):
        if player.gold > 29:

            player.channel.text = 'Right click to place building'
            player.channel.build_to_place = Balloonist
            player.channel.message = 'You just bought a Balloonist for 30 gold.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.gold -= 30
        else:
            player.channel.message = "You don't have enough gold to buy this!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'gold'

    def buy_construction_site(self, player):
        if player.gold > 59:

            player.channel.text = 'Right click to place building'
            player.channel.build_to_place = ConstructionSite
            player.channel.message = 'You just bought a Construction Site for 60 gold.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.gold -= 60
        else:
            player.channel.message = "You don't have enough gold to buy this!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'gold'
    def buy_restraunt(self, player):
        if player.food > 79:

            player.channel.text = 'Right click to place building'
            player.channel.build_to_place = Restaurant
            player.channel.message = 'You just bought a Restaurant for 80 food.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.food -= 80
        else:
            player.channel.message = "You don't have enough food to buy this!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'food'


class RunningTrack(Building):
    dimensions = (700, 620)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building increases your speed! Upgrade it to increase it', 'even more. (You can only have one Running Track at a time)')
        self.type = 'Running Track'
        self.health = self.max_health = 180
        self.dimensions = type(self).dimensions
        self.owner.character.speed += 3
        self.owner.character.moving += 3
        self.upgrade_cost = 90

        self.post_init(rect)

    def level_up(self, player):
        if self.level == 3:
            return
        if player.food > self.upgrade_cost - 1:
            self.level += 1
            self.owner.character.speed += 3
            self.owner.character.moving += 3
            player.channel.message = 'You upgraded this Running Track to level ' + str(self.level) + ' for ' + str(self.upgrade_cost) + ' food.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.food -= self.upgrade_cost
            self.upgrade_cost += 30
            self.health = self.max_health = self.max_health + 40
            
        else:
            player.channel.message = "You don't have enough food to upgrade this building!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)

        
        self.Out(player)

    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            if self.level < 3:
                channel.window = {'text':self.info,
                                  '4th_info':('Speed', str(self.owner.character.speed)),
                                  'health':(self.health, self.max_health),
                                  'building':self,
                                  'level':self.level,
                                  'options':[(0, self.level_up), (1, self.heal), (2, self.Out)],
                                  'simp':['Upgrade (' + str(self.upgrade_cost) + ' food)', 'Heal (5 food)', 'Out']}
            else:
                channel.window = {'text':self.info,
                                  '4th_info':('Speed', str(self.owner.character.speed)),
                                  'health':(self.health, self.max_health),
                                  'building':self,
                                  'level':self.level,
                                  'options':[(0, self.heal), (1, self.Out)],
                                  'simp':['Heal (5 food)', 'Out']}
        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              '4th_info':('Speed', str(self.owner.character.speed)),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.clear), (1, self.heal), (2, self.Out)],
                              'simp':['Clear (2 gold)', 'Out']}

        
    def getHurt(self, damage, attacker):
        
        if self.health > 0 and attacker != self.owner.character:
            self.health -= damage
            if self.health < 1:
                self.state = 'broken'
                if attacker.__class__.__name__ == 'Character':
                    self.owner.message = attacker.channel.username + ' has broken one of your ' + self.type + 's.'
                    attacker.destroyed += 1
                else:
                    self.owner.message = attacker + ' has broken one of your ' + self.type + 's.'
                self.owner.message_count = 150
                self.owner.message_color = (255,0,0)
                self.health = 0

                self.die()
                for p in self.server.players:
                    screen = pygame.Rect(0, 0, 1000, 650)
                    screen.center = p.character.rect.center
                    if screen.colliderect(self.rect):
                        p.Send({'action':'sound', 'sound':'building'})



                
                self.owner.character.speed = 8
                self.owner.character.moving = 8
                
class Gym(Building):
    dimensions = (700, 620)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building increases your resistance! Upgrade it to increase it', 'even more. (You can only have one Gym at a time)')
        self.type = 'Gym'
        self.health = self.max_health = 180
        self.dimensions = type(self).dimensions
        self.owner.character.strength += 2
        
        self.upgrade_cost = 90

        self.post_init(rect)

    def level_up(self, player):
        if self.level == 3:
            return
        if player.food > self.upgrade_cost - 1:
            self.level += 1
            self.owner.character.strength += 2
            
            player.channel.message = 'You upgraded this Gym to level ' + str(self.level) + ' for ' + str(self.upgrade_cost) + ' food.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.food -= self.upgrade_cost
            self.upgrade_cost += 30
            self.health = self.max_health = self.max_health + 40
            
        else:
            player.channel.message = "You don't have enough food to upgrade this building!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)

        
        self.Out(player)

    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            if self.level < 3:
                channel.window = {'text':self.info,
                                  '4th_info':('Resistance', str(self.owner.character.strength)),
                                  'health':(self.health, self.max_health),
                                  'building':self,
                                  'level':self.level,
                                  'options':[(0, self.level_up), (1, self.heal), (2, self.Out)],
                                  'simp':['Upgrade (' + str(self.upgrade_cost) + ' food)', 'Heal (5 food)', 'Out']}
            else:
                channel.window = {'text':self.info,
                                  '4th_info':('Resistance', str(self.owner.character.strength)),
                                  'health':(self.health, self.max_health),
                                  'building':self,
                                  'level':self.level,
                                  'options':[(0, self.heal), (1, self.Out)],
                                  'simp':['Heal (5 food)', 'Out']}
        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                                  '4th_info':('Resistance', str(self.owner.character.strength)),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 gold)', 'Out']}
            
    def getHurt(self, damage, attacker):
        
        if self.health > 0 and attacker != self.owner.character:
            self.health -= damage
            if self.health < 1:
                self.state = 'broken'
                if attacker.__class__.__name__ == 'Character':
                    self.owner.message = attacker.channel.username + ' has broken one of your ' + self.type + 's.'
                    attacker.destroyed += 1
                else:
                    self.owner.message = attacker + ' has broken one of your ' + self.type + 's.'
                self.owner.message_count = 150
                self.owner.message_color = (255,0,0)
                self.health = 0

                self.die()
                for p in self.server.players:
                    screen = pygame.Rect(0, 0, 1000, 650)
                    screen.center = p.character.rect.center
                    if screen.colliderect(self.rect):
                        p.Send({'action':'sound', 'sound':'building'})
                self.owner.character.strength = 0
                

class HealthCenter(Building):
    dimensions = (700, 620)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building increases your maximum health! Upgrade it to increase it', 'even more. (You can only have one Health Center at a time)')
        self.type = 'Health Center'
        self.health = self.max_health = 180
        self.dimensions = type(self).dimensions
        self.owner.character.max_health += 30
        self.owner.character.health += 30
        
        self.upgrade_cost = 90

        self.post_init(rect)

    def level_up(self, player):
        if self.level == 3:
            return
        if player.food > self.upgrade_cost - 1:
            self.level += 1
            self.owner.character.max_health += 30
            self.owner.character.health += 30
            
            player.channel.message = 'You upgraded this Health Center to level ' + str(self.level) + ' for ' + str(self.upgrade_cost) + ' food.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.food -= self.upgrade_cost
            self.upgrade_cost += 30
            self.health = self.max_health = self.max_health + 40
            
        else:
            player.channel.message = "You don't have enough food to upgrade this building!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)

        
        self.Out(player)

    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            if self.level < 3:
                channel.window = {'text':self.info,
                                  '4th_info':('Player health', ('%s/%s' % (self.owner.character.health, self.owner.character.max_health))),
                                  'health':(self.health, self.max_health),
                                  'building':self,
                                  'level':self.level,
                                  'options':[(0, self.level_up), (1, self.heal), (2, self.Out)],
                                  'simp':['Upgrade (' + str(self.upgrade_cost) + ' food)', 'Heal (5 food)', 'Out']}
            else:
                channel.window = {'text':self.info,
                                  '4th_info':('Player health', ('%s/%s' % (self.owner.character.health, self.owner.character.max_health))),
                                  'health':(self.health, self.max_health),
                                  'building':self,
                                  'level':self.level,
                                  'options':[(0, self.heal), (1, self.Out)],
                                  'simp':['Heal (5 food)', 'Out']}
        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                                  '4th_info':('Player health', ('%s/%s' % (self.owner.character.health, self.owner.character.max_health))),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 gold)', 'Out']}
            
    def getHurt(self, damage, attacker):
        
        if self.health > 0 and attacker != self.owner.character:
            self.health -= damage
            if self.health < 1:
                self.state = 'broken'
                if attacker.__class__.__name__ == 'Character':
                    self.owner.message = attacker.channel.username + ' has broken one of your ' + self.type + 's.'
                    attacker.destroyed += 1
                else:
                    self.owner.message = attacker + ' has broken one of your ' + self.type + 's.'
                self.owner.message_count = 150
                self.owner.message_color = (255,0,0)
                self.health = 0

                self.die()
                for p in self.server.players:
                    screen = pygame.Rect(0, 0, 1000, 650)
                    screen.center = p.character.rect.center
                    if screen.colliderect(self.rect):
                        p.Send({'action':'sound', 'sound':'building'})
                self.owner.character.max_health = 100
                if self.owner.character.health > 100:
                    self.owner.character.health = 100
                




class FitnessCenter(Building):
    dimensions = (585, 600)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building lets you buy the 3 fitness', 'buildings: Running Track, Gym and Health Center.')
        self.type = 'Fitness Center'
        self.health = self.max_health = 140
        self.dimensions = type(self).dimensions

        self.post_init(rect)

    def buy_running_track(self, player):
        yes = True
        for b in player.channel.get_buildings():
            if b.type == 'Running Track':
                yes = False
                player.channel.message = 'You already have a Running Track! You can only have one at a time.'
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
                

        if yes:
            if player.food > 74:

                player.channel.text = 'Right click to place building'
                player.channel.build_to_place = RunningTrack
                player.channel.message = 'You just bought a Running Track for 75 food.'
                player.channel.message_count = 150
                player.channel.message_color = (255,205,0)
                player.food -= 75
            else:
                player.channel.message = "You don't have enough food to buy this!"
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'food'

    def buy_gym(self, player):
        yes = True
        for b in player.channel.get_buildings():
            if b.type == 'Gym':
                yes = False
                player.channel.message = 'You already have a Gym! You can only have one at a time.'
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
                

        if yes:
            if player.food > 74:

                player.channel.text = 'Right click to place building'
                player.channel.build_to_place = Gym
                player.channel.message = 'You just bought a Gym for 75 food.'
                player.channel.message_count = 150
                player.channel.message_color = (255,205,0)
                player.food -= 75
            else:
                player.channel.message = "You don't have enough food to buy this!"
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'food'

    def buy_health_center(self, player):
        yes = True
        for b in player.channel.get_buildings():
            if b.type == 'Health Center':
                yes = False
                player.channel.message = 'You already have a Health Center! You can only have one at a time.'
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
                

        if yes:
            if player.food > 74:

                player.channel.text = 'Right click to place building'
                player.channel.build_to_place = HealthCenter
                player.channel.message = 'You just bought a Health Center for 75 food.'
                player.channel.message_count = 150
                player.channel.message_color = (255,205,0)
                player.food -= 75
            else:
                player.channel.message = "You don't have enough food to buy this!"
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
        self.Out(player)
        player.spence = 'food'


    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            channel.window = {'text':self.info,
                              '4th_info':('Number of fitness buildings', ('%s/3' % len([b for b in self.owner.get_buildings() if b.type in ('Health Center', 'Gym', 'Running Track')]))),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.heal), (1, self.buy_running_track), (2, self.buy_gym), (3, self.buy_health_center), (4, self.Out)],
                              'simp':['Heal (5 food)', 'Running Track (75 food)', 'Gym (75 food)', 'Health Center (75 food)', 'Out']}
        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              'upgradable':False,
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              '4th_info':('Number of fitness buildings', ('%s/3' % len([b for b in self.owner.get_buildings() if b.type in ('Health Center', 'Gym', 'Running Track')]))),
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 gold)', 'Out']}
                              


class Balloonist(Building):
    dimensions = (500, 495)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building lets you upgrade your attack stats.', '')
        self.type = 'Balloonist'
        self.health = self.max_health = 120
        self.dimensions = type(self).dimensions
        self.upgrade_cost = 50


        self.post_init(rect)

    def level_up(self, player):
        if player.gold > self.upgrade_cost - 1:
            self.level += 1
            
            
            player.channel.message = 'You upgraded this Balloonist to level ' + str(self.level) + ' for ' + str(self.upgrade_cost) + ' gold.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.gold -= self.upgrade_cost
            self.upgrade_cost += 20
            self.health = self.max_health = self.max_health + 50
            
        else:
            player.channel.message = "You don't have enough gold to upgrade this building!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)

    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            channel.window = {'text':self.info,
                              '4th_info':('Attack Damage', str(self.owner.character.attack)),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.level_up), (1, self.heal), (2, self.upgrade_balloon_damage), (3, self.upgrade_balloon_speed), (4, self.Out)],
                              'simp':['Upgrade (' + str(self.upgrade_cost) + ' gold)', 'Heal (5 food)', ' + Balloon Attack (' + str(channel.character.damage_cost) + ' gold)', ' + Balloon Speed (' + str(channel.character.speed_cost) + ' gold)', 'Out']}
        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              '4th_info':('Attack Damage', str(self.owner.character.attack)),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 gold)', 'Out']}

    def upgrade_balloon_speed(self, player):
        if player.gold > player.speed_cost - 1:
                
            player.balloon_speed += 3
            player.knockback += 8
            
            player.channel.message = "You upgraded your balloons' speed for " + str(self.owner.character.speed_cost) + " gold."
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.gold -= player.speed_cost

            player.speed_cost += 2

            
        else:
            player.channel.message = "You don't have enough gold to upgrade your balloons' speed!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)

    
    def upgrade_balloon_damage(self, player):
        if player.gold > player.damage_cost - 1:
            
            player.attack += 1
            
            player.channel.message = "You upgraded your attack for " + str(self.owner.character.damage_cost) + " gold."
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.gold -= player.damage_cost

            player.damage_cost += 10

            
        else:
            player.channel.message = "You don't have enough gold to upgrade your attack!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)




class FarmersGuild(Building):
    dimensions = (600, 500)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building sends farmers out to collect wheat for you.', '')
        self.type = "Farmer's Guild"
        self.health = self.max_health = 140
        self.dimensions = type(self).dimensions
        self.farmer = Farmer(self)

        self.post_init(rect)

    def getHurt(self, damage, attacker):
        
        if self.health > 0 and attacker != self.owner.character:
            self.health -= damage
            if self.health < 1:
                self.state = 'broken'
                if attacker.__class__.__name__ == 'Character':
                    self.owner.message = attacker.channel.username + ' has broken one of your ' + self.type + 's.'
                    attacker.destroyed += 1
                else:
                    self.owner.message = attacker + ' has broken one of your ' + self.type + 's.'
                self.owner.message_count = 150
                self.owner.message_color = (255,0,0)
                self.health = 0

                self.die()
                for p in self.server.players:
                    screen = pygame.Rect(0, 0, 1000, 650)
                    screen.center = p.character.rect.center
                    if screen.colliderect(self.rect):
                        p.Send({'action':'sound', 'sound':'building'})
                for farmer in self.server.NPCs:
                    if farmer.building == self:
                        farmer.kill()
                
    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            channel.window = {'text':self.info,
                              '4th_info':('Food Production Rate', str(1250 - self.farmer.farm.production)),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.heal), (1, self.Out)],
                              'simp':['Heal (5 food)', 'Out']}
        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              '4th_info':('Food Production Rate', str(1250 - self.farmer.farm.production)),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 gold)', 'Out']}

    




class MinersGuild(Building):
    dimensions = (500, 600)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building sends miners out to mine gold for you.', '')
        self.type = "Miner's Guild"
        self.health = self.max_health = 140
        self.dimensions = type(self).dimensions
        self.miner = Miner(self)
        

        self.post_init(rect)

    def getHurt(self, damage, attacker):
        
        if self.health > 0 and attacker != self.owner.character:
            self.health -= damage
            if self.health < 1:
                self.state = 'broken'
                if attacker.__class__.__name__ == 'Character':
                    self.owner.message = attacker.channel.username + ' has broken one of your ' + self.type + 's.'
                    attacker.destroyed += 1
                else:
                    self.owner.message = attacker + ' has broken one of your ' + self.type + 's.'
                self.owner.message_count = 150
                self.owner.message_color = (255,0,0)
                self.health = 0

                self.die()
                for p in self.server.players:
                    screen = pygame.Rect(0, 0, 1000, 650)
                    screen.center = p.character.rect.center
                    if screen.colliderect(self.rect):
                        p.Send({'action':'sound', 'sound':'building'})
                for miner in self.server.NPCs:
                    if miner.building == self:
                        miner.kill()
                

    


    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            channel.window = {'text':self.info,
                              '4th_info':('Gold Discovery Rate', str(1250 - self.miner.farm.production)),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.heal), (1, self.Out)],
                              'simp':['Heal (5 food)', 'Out']}
        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              '4th_info':('Gold Discovery Rate', str(1250 - self.miner.farm.production)),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 gold)', 'Out']}



        



def builder(b, p, has_builder):
    if b.isBuilding(object()):
        dimensions = b.dimensions
        if has_builder:
            dimensions = (b.dimensions[0]*0.8, b.dimensions[1]*0.8)
        x, y = p.x, p.y - 140
        image = pygame.Surface((200, 200))
        width, height = dimensions
        rect = pygame.Rect(0, 0, width, height)
        rect.midtop = (x, y-round(image.get_height()/2))

    else:
        x, y = p.x, p.y - 240
        surf = pygame.Surface((360, 360))
        rect = surf.get_rect(center=(x, y))

    if rect.left < 0 or rect.right > 6000 or rect.top < 0 or rect.bottom > 3900:
        return False, rect
    
    
    
    for obs in p.channel.server.building_blocks:
        if rect.colliderect(obs):
            return False, rect
    return True, rect



class ConstructionSite(Building):
    dimensions = (560, 560)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building lets you buy defences for your village. Crates, Gates, Archery Towers,', 'Robot Factories...')
        self.type = 'Construction Site'
        self.health = self.max_health = 160
        self.dimensions = type(self).dimensions
        self.upgradable = True

        self.post_init(rect)

    def buy_crate(self, player):
        if player.food > 1:
            player.channel.message = 'You bought a crate for 2 food.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.food -= 2
            player.crates += 1
        else:
            player.channel.message = "You don't have enough food for this!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        
        self.Out(player)

    def buy_gate(self, player):
        if player.gold > 39:
            player.channel.message = 'You bought a gate for 40 gold.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.gold -= 40
            player.channel.text = 'Press x to place gate'
        else:
            player.channel.message = "You don't have enough gold for this!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        
        self.Out(player)

    def buy_tnt(self, player):
        if player.gold > 99:
            if player.food > 99:
                player.channel.message = 'You bought TNT for 100 gold and 100 food.'
                player.channel.message_count = 150
                player.channel.message_color = (255,205,0)
                player.gold -= 100
                player.food -= 100
                player.channel.text = 'Press x to place TNT'
            else:
                player.channel.message = "You don't have enough food for this!"
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
        else:
            if player.food > 99:
                player.channel.message = "You don't have enough gold for this!"
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
            else:
                player.channel.message = "You can't afford this!"
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
        
        self.Out(player)

    def buy_archery_tower(self, player):
        if player.food > 19:
            if player.gold > 109:

                player.channel.text = 'Right click to place building'
                player.channel.build_to_place = ArcheryTower
                player.channel.message = 'You just bought an Archery Tower for 110 gold and 20 food.'
                player.channel.message_count = 150
                player.channel.message_color = (255,205,0)
                player.gold -= 110
                player.food -= 20
                player.spence = 'gold'
            else:
                player.channel.message = "You don't have enough gold to buy this!"
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
        
        else:
            if player.gold > 109:
                player.channel.message = "You don't have enough food to buy this!"
            else:
                player.channel.message = "You can't afford an Archery Tower!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)

    def level_up(self, player):
        if player.gold > 29:
            self.level = 2
            
            
            player.channel.message = 'You upgraded this Construction Site to level 2 for 30 gold.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.gold -= 30
            self.upgradable = False
            self.health = self.max_health = 200
            
        else:
            player.channel.message = "You don't have enough gold to upgrade this building!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)

    def buy_robot_factory(self, player):
        if player.food > 4:
            if player.gold > 114:

                player.channel.text = 'Right click to place building'
                player.channel.build_to_place = RobotFactory
                player.channel.message = 'You just bought a Robot Factory for 115 gold and 5 food.'
                player.channel.message_count = 150
                player.channel.message_color = (255,205,0)
                player.gold -= 115
                player.food -= 5
                player.spence = 'gold'
            else:
                player.channel.message = "You don't have enough gold to buy this!"
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
        
        else:
            if player.gold > 114:
                player.channel.message = "You don't have enough food to buy this!"
            else:
                player.channel.message = "You can't afford this building!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)

    def buy_barrel_maker(self, player):
        if player.food > 64:
            if player.gold > 49:

                player.channel.text = 'Right click to place building'
                player.channel.build_to_place = BarrelMaker
                player.channel.message = 'You just bought a Barrel Maker for 50 gold and 65 food.'
                player.channel.message_count = 150
                player.channel.message_color = (255,205,0)
                player.gold -= 50
                player.food -= 65
                player.spence = 'food'
            else:
                player.channel.message = "You don't have enough gold to buy this!"
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
        
        else:
            if player.gold > 49:
                player.channel.message = "You don't have enough food to buy this!"
            else:
                player.channel.message = "You can't afford this building!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)
        



    def open_window(self, channel):
        if self.state == 'alive':
            if self.upgradable:
                channel.in_window = True
                channel.window = {'text':self.info,
                              '4th_info':('Upgraded', 'False'),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.level_up), (1, self.heal), (2, self.buy_crate), (3, self.buy_gate), (4, self.buy_tnt), (5, self.Out)],
                              'simp':['Upgrade (30 gold)', 'Heal (5 food)', 'Crate (2 food)', 'Gate (40 gold)', 'TNT (100 gold, 100 food)', 'Out']}
            else:
                channel.in_window = True
                channel.window = {'text':self.info,
                              '4th_info':('Upgraded', 'True'),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.heal), (1, self.buy_crate), (2, self.buy_gate), (3, self.buy_tnt), (4, self.buy_archery_tower), (5, self.buy_robot_factory), (6, self.buy_barrel_maker), (7, self.Out)],
                              'simp':['Heal (5 food)', 'Crate (2 food)', 'Gate (40 gold)', 'TNT (100 gold, 100 food)', 'Archery Tower (110 gold, 20 food)', 'Robot Factory (115 gold, 5 food)', 'Barrel Maker (50 gold, 65 food)', 'Out']}
        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              '4th_info':('Upgraded', str(self.level == 2)),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 gold)', 'Out']}




class Restaurant(Building):
    dimensions = (600, 580)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building lets you buy meals, which heal you when you eat them.', '')
        self.type = 'Restaurant'
        self.health = self.max_health = 220
        self.dimensions = type(self).dimensions

        self.post_init(rect)

    def buy_meal(self, player):

        if player.food > 11:
                if player.meal:
                    player.channel.message = "You already have a meal! Eat it before buying another one."
                    player.channel.message_count = 150
                    player.channel.message_color = (0,0,255)

                else:
                    player.meal = True
                    player.meal_type = r.randrange(DISHES)
                    player.channel.message = "You bought a meal for 12 food."
                    player.channel.message_count = 150
                    player.channel.message_color = (255,205,0)
                    player.food -= 12



            
        else:
            player.channel.message = "You don't have enough food to buy a meal!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)

    def dine_in(self, player):

        if player.food > 5:
                if player.meal:
                    player.channel.message = "You already have a meal! Eat it before ordering one."
                    player.channel.message_count = 150
                    player.channel.message_color = (0,0,255)

                else:
                    player.channel.message = "You ate a meal for 6 food."
                    player.channel.message_count = 150
                    player.channel.message_color = (255,205,0)
                    player.food -= 6
                    player.dine_in()



            
        else:
            player.channel.message = "You don't have enough food to order a meal!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)



    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            channel.window = {'text':self.info,
                              '4th_info':('Need meal', ('no' if channel.character.meal else 'yes')),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.heal), (1, self.buy_meal), (2, self.dine_in), (3, self.Out)],
                              'simp':['Heal (5 food)', 'Take out (12 food)', 'Order meal (6 food)', 'Out']}
        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              'upgradable':False,
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              '4th_info':('Need meal', ('no' if channel.character.meal else 'yes')),
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 gold)', 'Out']}


class RobotFactory(Building):
    dimensions = (504, 500)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building sends out several little robots who attack', 'other players. It\'s a good way to defend your village!')
        self.type = 'Robot Factory'
        self.health = self.max_health = 120
        self.dimensions = type(self).dimensions

        self.post_init(rect)

        Robot(self)
        Robot(self)
        Robot(self)

        self.num_bots = 3

    def level_up(self, player):
        if player.gold > 39:
            self.level  += 1
            
            
            player.channel.message = 'You upgraded this Robot Factory to level ' + str(self.level) + ' for 40 gold.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.gold -= 40
            self.upgradable = False
            if self.max_health < 320: self.max_health += 50
            self.health = self.max_health

            Robot(self)
            self.num_bots += 1
            
        else:
            player.channel.message = "You don't have enough gold to upgrade this building!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)

    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            channel.window = {'text':self.info,
                              '4th_info':('Robots', str(self.num_bots)),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.heal), (1, self.level_up), (2, self.Out)],
                              'simp':['Heal (5 food)', 'Upgrade (40 gold)', 'Out']}
        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              'upgradable':False,
                              'health':(self.health, self.max_health),
                              'building':self,
                              '4th_info':('Robots', str(self.num_bots)),
                              'level':self.level,
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 gold)', 'Out']}

    def die(self):
        for npc in self.server.NPCs:
            if type(npc).__name__ == 'Robot' and npc.factory == self:
                npc.kill()

from InnPC import *

class Inn(Building):
    dimensions = (550, 490)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building welcomes different NPCs that can trade with you.', '')
        self.type = 'Inn'
        self.health = self.max_health = 240
        self.dimensions = type(self).dimensions
        self.NPC = None
        self.count = r.randint(250, 750)
        

        self.post_init(rect)


    def level_up(self, player):
        if player.food > 99:
            self.level = 2
            
            
            player.channel.message = 'You upgraded this Inn to level 2 for 100 food.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.food -= 100
            self.upgradable = False
            self.max_health = 340
            self.health = 340
            
        else:
            player.channel.message = "You don't have enough food to upgrade this building!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)

    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            if self.NPC:
                if self.level == 1:
                    channel.window = {'text':self.info,
                                          '4th_info':('Hosting', self.NPC.type),
                                          'health':(self.health, self.max_health),
                                          'building':self,
                                          'level':self.level,
                                          'options':[(0, self.heal), (1, self.level_up), (2, self.kick_npc), (3, self.build_house), (4, self.Out)],
                                          'simp':['Heal (5 food)', 'Upgrade (100 food)', 'Kick %s (free)' % (self.NPC.type), 'Build the %s a house (%s gold, %s food)' % (self.NPC.type, self.NPC.cost[0], self.NPC.cost[1]), 'Out']}
                else:
                    channel.window = {'text':self.info,
                                          '4th_info':('Hosting', self.NPC.type),
                                          'health':(self.health, self.max_health),
                                          'building':self,
                                          'level':self.level,
                                          'options':[(0, self.heal), (1, self.kick_npc), (2, self.build_house), (3, self.Out)],
                                          'simp':['Heal (5 food)', 'Kick %s (free)' % (self.NPC.type), 'Build the %s a house (%s gold, %s food)' % (self.NPC.type, self.NPC.cost[0], self.NPC.cost[1]), 'Out']}
            else:
                if self.level == 1:
                    channel.window = {'text':self.info,
                                      '4th_info':('Hosting', 'Nobody'),
                                      'health':(self.health, self.max_health),
                                      'building':self,
                                      'level':self.level,
                                      'options':[(0, self.heal), (1, self.level_up), (2, self.Out)],
                                      'simp':['Heal (5 food)', 'Upgrade (100 food)', 'Out']}
                else:
                    channel.window = {'text':self.info,
                                      '4th_info':('Hosting', 'Nobody'),
                                      'health':(self.health, self.max_health),
                                      'building':self,
                                      'level':self.level,
                                      'options':[(0, self.heal), (1, self.Out)],
                                      'simp':['Heal (5 food)', 'Out']}
        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              'upgradable':False,
                              'health':(self.health, self.max_health),
                              'building':self,
                              '4th_info':('Hosting', ('Nobody' if self.NPC is None else self.NPC.type)),
                              'level':self.level,
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 gold)', 'Out']}

    def update(self):
        super().update()
        if self.state != 'broken':
            if self.NPC is not None:
                self.NPC.update()
            else:
                if self.server.event.__class__.__name__ != 'BarbarianRaid':
                    self.count -= 1
                    if self.count == 0:
                        self.NPC = get_innpc(self)
                

    def kick_npc(self, player):
        if player.channel == self.owner:
            name = self.NPC.type
            self.NPC.depart()
            player.channel.message = 'You have kicked the %s.' % name
            player.channel.message_color = (128,0,128)
        else:
            player.channel.message = "This isn't your Inn!"
            player.channel.message_count = 160
            player.channel.message_color = (255,0,0)
        self.Out(player)

    def build_house(self, player):
        if player == self.owner.character:
            if player.food > self.NPC.cost[1]:
                if player.gold > self.NPC.cost[0]:

                    player.channel.text = 'Right click to place building'
                    player.channel.build_to_place = self.NPC.building
                    NPC = self.NPC
                    self.NPC.depart()
                    player.channel.message = 'You just bought the %s a house for %s gold and %s food.' % (NPC.type, NPC.cost[0], NPC.cost[1])
                    player.channel.message_count = 150
                    player.channel.message_color = (255,205,0)
                    player.gold -= NPC.cost[0]
                    player.food -= NPC.cost[1]
                    player.spence = ('gold' if NPC.cost[0] >= NPC.cost[1] else 'food')
                else:
                    player.channel.message = "You don't have enough gold to buy this!"
                    player.channel.message_count = 150
                    player.channel.message_color = (255,0,0)
                
            else:
                if player.gold > self.NPC.cost[0]:
                    player.channel.message = "You don't have enough food to buy this!"
                else:
                    player.channel.message = "You can't afford this building!"
                player.channel.message_count = 150
                player.channel.message_color = (255,0,0)
        else:
            player.channel.message = "This isn't your Inn!"
            player.channel.message_count = 160
            player.channel.message_color = (255,0,0)
        self.Out(player)
        
           
class BarrelMaker(Building):
    dimensions = (670, 440)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building lets you buy barrels!! Z to hide. Z+Click to throw.', '(: (: (: (: (: (: (: (:')
        self.type = 'Barrel Maker'
        self.health = self.max_health = 250
        
        self.upgrade_cost = 100

        self.post_init(rect)

    def level_up(self, player):
        if player.gold > self.upgrade_cost - 1:
            self.level += 1
            player.channel.message = 'You upgraded this Barrel Maker to level ' + str(self.level) + ' for ' + str(self.upgrade_cost) + ' gold.'
            player.channel.message_count = 150
            player.channel.message_color = (255,205,0)
            player.gold -= self.upgrade_cost
            self.upgrade_cost += 20
            if self.level < 15:
                self.health = self.max_health = self.max_health + 20
            
        else:
            player.channel.message = "You don't have enough gold to upgrade this building!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)

        
        self.Out(player)

    def buy_barrel(self, player):

        if player.food > 16:
            if player.barrel_health > 0:
                player.channel.message = "You already have a barrel! Get rid of it before buying a new one."
                player.channel.message_count = 150
                player.channel.message_color = (0,0,255)

            else:
                player.channel.message = "You bought a barrel! (17 food)"
                player.channel.message_count = 150
                player.channel.message_color = (255,205,0)
                player.food -= 17
                player.barrel_health = player.barrel_max_health = 10 + (5 * self.level)
                player.explosive = False



            
        else:
            player.channel.message = "You don't have enough food to buy a barrel!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)
        
    def buy_barrel_tnt(self, player):

        if player.gold > 149:
            if player.barrel_health > 0:
                player.channel.message = "You already have a barrel! Get rid of it before buying a NEW one."
                player.channel.message_count = 150
                player.channel.message_color = (0,0,255)

            else:
                player.channel.message = "You bought an explosive barrel! (150 gold)"
                player.channel.message_count = 150
                player.channel.message_color = (255,205,0)
                player.gold -= 150
                player.barrel_health = player.barrel_max_health = 10 + (5 * self.level)
                player.explosive = True



            
        else:
            player.channel.message = "You don't have enough gold to buy this quality barrel!"
            player.channel.message_count = 150
            player.channel.message_color = (255,0,0)
        self.Out(player)



    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            channel.window = {'text':self.info,
                              '4th_info':('Barrel Health', str(channel.character.barrel_health)),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.level_up), (1, self.heal), (2, self.buy_barrel), (3, self.buy_barrel_tnt), (4, self.Out)],
                              'simp':['Upgrade (%s gold)' % self.upgrade_cost, 'Heal (5 food)', 'Barrel (17 food)', 'Explosive Barrel (150 gold)', 'Out']}
            
        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              'upgradable':False,
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              '4th_info':('Barrel Health', str(channel.character.barrel_health)),
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 gold)', 'Out']}            


                
            
__ALL__ = ['CentralBuilding', 'PortableCentralBuilding', 'FitnessCenter', 'Balloonist', 'Gym', 'RunningTrack', 'HealthCenter', 'BarrelMaker', 'ConstructionSite', 'RobotFactory', 'Restaurant', 'MinersGuild', 'FarmersGuild', 'Inn']
