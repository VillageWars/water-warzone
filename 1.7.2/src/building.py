import pygame
import toolbox as t
import toolbox
import math
import logging
import random as r
import random
from NPC import ArcheryTower, Robot, Collector
import os
import configuration as conf
from elements import Building
from InnPC import get_innpc, INNSTART, INNEND

try:
    DISHES = len(os.listdir(conf.path + 'assets/meals')) - 2
except:
    DISHES = 1

# As to not repeat this in the "no" option
BTB = 'buy this building!'  
UPG = 'upgrade this building!'
BUY = 'buy this!'

def buy_building(channel, building):
    channel.build_to_place = building
    channel.text = 'Right click to place building'

class CentralBuilding(Building):
    type = 'Central Building'
    info = 'The Central Building is for buying other buildings.', 'If all your buildings are destroyed, you will not respawn.'
    dimensions = (675, 550)
    max_health = 420
    def options(self, character):
        return [{'name': 'Portable Central Building',
                    'gold-cost': 10,
                    'food-cost': 10,
                    'action': self.buy_portable_central_building,
                    'no': BTB},
                {'name': 'Fitness Center',
                    'food-cost': 50,
                    'action': self.buy_fitness_center,
                    'no': BTB},
                {'name': 'Balloonist',
                    'gold-cost': 30,
                    'action': self.buy_balloonist,
                    'no': BTB},
                {'name': 'Farmer\'s Guild',
                    'food-cost': 25,
                    'action': self.buy_farmers_guild,
                    'no': BTB},
                {'name': 'Miner\'s Guild',
                    'gold-cost': 25,
                    'action': self.buy_miners_guild,
                    'no': BTB},
                {'name': 'Construction Site',
                    'gold-cost': 60,
                    'action': self.buy_construction_site,
                    'no': BTB},
                {'name': 'Restaurant',
                    'food-cost': 60,
                    'action': self.buy_restaurant,
                    'no': BTB},
                {'name': 'Inn',
                    'food-cost': 100,
                    'action': self.buy_inn,
                    'condition': 'not [building for building in channel.get_buildings() if building.type == "Inn"]',
                    'no': BTB}]

    def get_4th_info(self, channel):
        return 'Number of non-broken buildings', str(len(channel.get_buildings()))

    def buy_portable_central_building(self, character):
        buy_building(character.channel, PortableCentralBuilding)
        character.channel.add_message('You just bought a Portable Central Building for 10 gold and 10 food.')

    def buy_fitness_center(self, character):
        buy_building(character.channel, FitnessCenter)
        character.channel.add_message('You just bought a Fitness Center for 50 food.')

    def buy_farmers_guild(self, character):
        buy_building(character.channel, FarmersGuild)
        character.channel.add_message('You just bought a Farmer\'s Guild for 25 food.')

    def buy_miners_guild(self, character):
        buy_building(character.channel, MinersGuild)
        character.channel.add_message('You just bought a Miner\'s Guild for 25 gold.')

    def buy_balloonist(self, character):
        buy_building(character.channel, Balloonist)
        character.channel.add_message('You just bought a Balloonist for 30 gold.')

    def buy_construction_site(self, character):
        buy_building(character.channel, ConstructionSite)
        character.channel.add_message('You just bought a Construction Site for 60 gold.')

    def buy_restaurant(self, character):
        buy_building(character.channel, Restaurant)
        character.channel.add_message('You just bought a Restaurant for 80 food.')

    def buy_inn(self, character):
        buy_building(character.channel, Inn)
        character.channel.add_message('You just bought an Inn for 100 food.')


class PortableCentralBuilding(CentralBuilding):
    type = 'Portable Central Building'
    info = 'This offers the same options as the Central Building, so you', 'can buy buildings even after your Central Buildings is broken.'
    dimensions = (560, 560)
    max_health = 110

class RunningTrack(Building):
    type = 'Running Track'
    info = 'This building increases your speed! Upgrade it to increase it', 'even more. You can only have one Running Track at a time.'
    dimensions = (700, 620)
    max_health = 180
    upgrade_cost = [0, 90]
    def init(self):
        self.character.speed += 3
    def options(self, character):
        return [{'name': 'Upgrade', 'food-cost': self.upgrade_cost[1], 'action': self.upgrade, 'condition': 'self.level < 3', 'no': UPG}]
    def get_4th_info(self, channel):
        return 'Speed', str(channel.character.speed)
    def level_up(self, character):
        self.character.speed += 3
        self.upgrade_cost[1] += 30
        self.health = self.max_health = self.max_health + 40
    def die(self):
        self.character.speed = 8
                
class Gym(Building):
    type = 'Gym'
    info = 'This building increases your resistance! Upgrade it to increase', 'it even more. You can only have one Gym at a time.'
    dimensions = (700, 620)
    max_health = 180
    upgrade_cost = [0, 90]
    def init(self):
        self.character.resistance += 2
    def options(self, character):
        return [{'name': 'Upgrade', 'food-cost': self.upgrade_cost[1], 'action': self.upgrade, 'condition': 'self.level < 3', 'no': UPG}]
    def get_4th_info(self, channel):
        return 'Resistance', str(channel.character.resistance)
    def level_up(self, character):
        self.character.resistance += 2
        self.upgrade_cost[1] += 30
        self.health = self.max_health = self.max_health + 40
    def die(self):
        self.character.resistance = 0
                
class HealthCenter(Building):
    type = 'Health Center'
    info = 'This building increases your maximum health! Upgrade it to increase it', 'even more. You can only have one Health Center at a time.'
    dimensions = (700, 620)
    max_health = 180
    upgrade_cost = [0, 90]
    def init(self):
        self.character.max_health += 30
        self.character.health += 30
    def options(self, character):
        return [{'name': 'Upgrade', 'food-cost': self.upgrade_cost[1], 'action': self.upgrade, 'condition': 'self.level < 3', 'no': UPG}]
    def get_4th_info(self, channel):
        return 'character health', ('%s/%s' % (channel.character.health, channel.character.max_health))
    def level_up(self, character):
        self.character.max_health += 30
        self.character.health += 30
        self.upgrade_cost[1] += 30
        self.health = self.max_health = self.max_health + 40
    def die(self):
        self.character.max_health = 100
        self.character.health = min(100, self.character.health)

class FitnessCenter(Building):
    type = 'Fitness Center'
    info = 'This building lets you buy the 3 fitness', 'buildings: Running Track, Gym and Health Center.'
    dimensions = (585, 600)
    max_health = 140
    def options(self, character):
        return [{'name': 'Running Track',
                    'food-cost': 75,
                    'action': self.buy_running_track,
                    'condition': 'not [building for building in channel.get_buildings() if building.type == "Running Track"]',
                    'no': BTB},
                {'name': 'Gym',
                    'food-cost': 75,
                    'action': self.buy_gym,
                    'condition': 'not [building for building in channel.get_buildings() if building.type == "Gym"]',
                    'no': BTB},
                {'name': 'Health Center',
                    'food-cost': 75,
                    'action': self.buy_health_center,
                    'condition': 'not [building for building in channel.get_buildings() if building.type == "Health Center"]',
                    'no': BTB}]
    def get_4th_info(self, channel):
        return 'Number of fitness buildings', ('%s/3' % len([b for b in channel.get_buildings() if b.type in ('Health Center', 'Gym', 'Running Track')]))
    def buy_running_track(self, character):
        buy_building(character.channel, RunningTrack)
        character.channel.add_message('You just bought a Running Track for 75 food.')
    def buy_gym(self, character):
        buy_building(character.channel, Gym)
        character.channel.add_message('You just bought a Gym for 75 food.')
    def buy_health_center(self, character):
        buy_building(character.channel, HealthCenter)
        character.channel.add_message('You just bought a Health Center for 75 food.')

class Balloonist(Building):
    type = 'Balloonist'
    info = 'This building lets you upgrade some of your attack stats.', 'Note: Other characters can\'t upgrade their own attack here.'
    dimensions = (500, 495)
    max_health = 120
    upgrade_cost = [50, 0]
    def options(self, character):
        return [{'name': 'Upgrade', 'gold-cost': self.upgrade_cost[0], 'action': self.upgrade, 'no': UPG},
                {'name': '+ Balloon Damage',
                    'gold-cost': self.character.damage_cost,
                    'action': self.upgrade_balloon_damage,
                    'no': 'upgrade your balloon damage!'},
                {'name': '+ Balloon Velocity',
                    'gold-cost': self.character.speed_cost,
                    'action': self.upgrade_balloon_speed,
                    'no': 'upgrade your balloon velocity!'}]
    def get_4th_info(self, channel):
        return 'Balloon Damage', str(channel.character.balloon_damage)
    def level_up(self, character):
        self.upgrade_cost[0] += 20
        self.health = self.max_health = self.max_health + 50
    def upgrade_balloon_speed(self, character):
        character.balloon_speed += 3
        character.channel.add_message('You upgraded your balloon velocity for ' + str(character.speed_cost) + ' gold!')
        character.speed_cost += 2
    def upgrade_balloon_damage(self, character):
        character.balloon_damage += 1
        character.channel.add_message('You upgraded your balloon damage for ' + str(character.damage_cost) + ' gold!')
        character.damage_cost += 10

class FarmersGuild(Building):
    type = 'Farmer\'s Guild'
    info = 'This building sends farmers out to collect food for you.', ''
    dimensions = (600, 500)
    max_health = 140
    def init(self):
        self.farmer = Collector(self)
    def get_4th_info(self, channel):
        return 'Food Production Rate', str(1250 - self.farmer.yard.production)
    def die(self):
        return [farmer.kill() for farmer in self.server.NPCs if farmer.building == self]  # Kill farmers

class MinersGuild(Building):
    type = 'Miner\'s Guild'
    info = 'This building sends miners out to mine gold for you.', ''
    dimensions = (500, 600)
    max_health = 140
    def init(self):
        self.miner = Collector(self)
    def get_4th_info(self, channel):
        return 'Gold Discovery Rate', str(1250 - self.miner.yard.production)
    def die(self):
        return [miner.kill() for miner in self.server.NPCs if miner.building == self]  # Kill miners

class ConstructionSite(Building):
    type = 'Construction Site'
    info = 'This building lets you buy defenses for your village.', 'Upgrade to buy Archery Towers, Robot Factories, Barrels...'
    dimensions = (560, 560)
    max_health = 160
    def options(self, character):  # Building.condition() removes unavailable options automatically
        return [{'name': 'Upgrade', 'gold-cost': 30, 'action': self.upgrade, 'condition': 'self.level == 1', 'no': UPG},
                {'name': 'Crate', 'food-cost': 2, 'action': self.buy_crate, 'no': 'buy a crate!'},
                {'name': 'Gate', 'gold-cost': 40, 'action': self.buy_gate, 'no': 'buy a gate!'},
                {'name': 'TNT', 'gold-cost': 100, 'food-cost': 100, 'action': self.buy_tnt, 'no': 'buy TNT!'},
                {'name': 'Archery Tower', 'gold-cost': 110, 'food-cost': 20, 'action': self.buy_archery_tower, 'condition': 'self.level == 2', 'no': 'buy an Archery Tower!'},
                {'name': 'Robot Factory', 'gold-cost': 115, 'food-cost': 5, 'action': self.buy_robot_factory, 'condition': 'self.level == 2', 'no': BTB},
                {'name': 'Barrel Maker', 'gold-cost': 50, 'food-cost': 65, 'action': self.buy_barrel_maker, 'condition': 'self.level == 2', 'no': BTB}]
        return options
    def get_4th_info(self, channel):
        return 'Upgraded', str(self.level == 2)
    def buy_crate(self, character):
        character.channel.add_message('You bought a crate for 2 food.')
        character.crates += 1
    def buy_gate(self, character):
        character.channel.add_message('You bought a gate for 40 gold.')
        character.channel.text = 'Press x to place gate'
    def buy_tnt(self, character):
        character.channel.add_message('You bought TNT for 100 gold and 100 food.')
        character.channel.text = 'Press x to place TNT'
    def buy_archery_tower(self, character):
        character.channel.text = 'Right click to place Archery Tower'
        character.channel.build_to_place = ArcheryTower
        character.channel.add_message('You just bought an Archery Tower for 110 gold and 20 food.')
    def level_up(self, character):
        self.health = self.max_health = 200  # Just one upgrade allowed
    def buy_robot_factory(self, character):
        buy_building(character.channel, RobotFactory)
        character.channel.add_message('You just bought a Robot Factory for 115 gold and 5 food.')
    def buy_barrel_maker(self, character):
        buy_building(character.channel, BarrelMaker)
        character.channel.add_message('You just bought a Barrel Maker for 50 gold and 65 food.')

class Restaurant(Building):
    type = 'Restaurant'
    info = 'This building lets you buy meals, which restore your health', 'when you eat them.'
    dimensions = (600, 580)
    max_health = 220
    def options(self, character):
        return [{'name': 'Takeout',
                    'action': self.buy_takeout,
                    'food-cost': 12,
                    'condition': 'not character.meal',
                    'no': 'buy takeout!'},
                {'name': 'Order Meal',
                    'action': self.order_meal,
                    'food-cost': 6,
                    'no': 'order a meal!'}]
    def get_4th_info(self, channel):
        return 'Need takeout', ('No' if channel.character.meal else 'Yes')
    def buy_takeout(self, character):
        character.channel.add_message('You bought a meal for 12 food.')
        character.meal = True
        character.meal_type = random.randrange(DISHES)
    def order_meal(self, character):
        character.channel.add_message('You ate a meal for 6 food.')
        character.health = character.max_health

class RobotFactory(Building):
    type = 'Robot Factory'
    info = 'This building sends out several little robots who attack', 'nearby enemy characters. It\'s a good way to defend your village!'
    dimensions = (504, 500)
    max_health = 120
    num_bots = 3
    def init(self):
        for i in range(self.num_bots): Robot(self)
    def options(self, character):
        return [{'name': 'Upgrade', 'action': self.upgrade, 'gold-cost': 40, 'no': UPG}]
    def get_4th_info(self, channel):
        return 'Robots', str(self.num_bots)
    def level_up(self, character):
        if self.max_health < 320:
            self.max_health += 50
        self.health = self.max_health
        self.num_bots += 1
        Robot(self)
    def die(self):
        return [npc.kill() for npc in self.server.NPCs if (type(npc).__name__ == 'Robot' and npc.building == self)] # Kill robots

class Inn(Building):
    type = 'Inn'
    info = 'This building welcomes different NPCs that can trade', 'with you.'
    dimensions = (550, 490)
    max_health = 240
    NPC = None
    upgrade_cost = [0, 100]
    def init(self):
        self.count = random.randint(INNSTART, INNEND)
    def options(self, character):
        options = [{'name': 'Upgrade',
                    'action': self.upgrade,
                    'condition': 'self.level == 1',
                    'food-cost': self.upgrade_cost[1]}]
        if self.NPC:
            options.extend([{'name': 'Kick ' + self.NPC.type,
                                'action': self.kick_npc,
                                'condition': 'character.channel == self.channel'},
                            {'name': 'Build the %s a house' % self.NPC.type,
                                'action': self.build_house,
                                'gold-cost': self.NPC.building_cost[0],
                                'food-cost': self.NPC.building_cost[1],
                                'condition': 'character.channel == self.channel'}])
        return options
    def get_4th_info(self, channel):
        return 'Hosting', (self.NPC.type if self.NPC else 'Nobody')
    def level_up(self, character):
        self.health = self.max_health = 340
    def update(self):
        super().update()
        if self.state == 'broken' or 'Barbarian Raid' in [event.type for event in self.server.events]:
            return
        if self.NPC:
            self.NPC.update()
        else:
            self.count -= 1
            if self.count <= 0:
                self.NPC = get_innpc(self)
    def kick_npc(self, character):
        character.channel.add_message('You have kicked the %s.' % self.NPC.type, color=(128,0,128))
        self.NPC.depart()
    def build_house(self, character):
        buy_building(character.channel, self.NPC.create_building())
        character.channel.add_message('You just built the %s a house for %s.' % (self.NPC.type, toolbox.format_cost(self.NPC.building_cost)))
        self.NPC.depart()

class BarrelMaker(Building):
    type = 'Barrel Maker'
    info = 'This building lets you buy barrels!', 'Z to hide. Z+Click to toss.'
    dimensions = (670, 440)
    max_health = 250
    upgrade_cost = [70, 0]
    def options(self, character):
        return [{'name': 'Upgrade',
                    'action': self.upgrade,
                    'gold-cost': self.upgrade_cost[0],
                    'no': UPG},
                {'name': 'Barrel',
                    'action': self.buy_barrel,
                    'food-cost': 17,
                    'condition': 'character.barrel_health <= 0',
                    'no': BUY},
                {'name': 'Explosive Barrel',
                    'action': self.buy_explosive_barrel,
                    'gold-cost': 150,
                    'condition': 'character.barrel_health <= 0',
                    'no': 'buy this quality barrel!'}]
    def get_4th_info(self, channel):
        return 'Barrel Health', str(channel.character.barrel_health)
    def level_up(self, character):
        self.upgrade_cost[0] += 5
        if self.level < 15:
            self.health = self.max_health = self.max_health + 20
    def buy_barrel(self, character):
        character.channel.add_message('You bought a barrel for 17 food.')
        character.barrel_health = character.barrel_max_health = 10 + (5 * self.level)
        character.has_explosive_barrel = False  # Not explosive barrel        
    def buy_explosive_barrel(self, character):
        character.channel.add_message('You bought an explosive barrel for 150 gold.')
        character.barrel_health = character.barrel_max_health = 10 + (5 * self.level)
        character.has_explosive_barrel = True  # Explosive barrel


def test_build(character):  # Returns a building's rect if the building fits
    building = character.channel.build_to_place
    width, height = building.dimensions
    if building.type != 'Archery Tower':
        if character.has_builder: width *= 0.8; height *= 0.8
        y_distance = 240
    else:
        y_distance = 420
    rect = pygame.Rect(0, 0, width, height)
    rect.midtop = (character.x, character.y - y_distance)
    map_rect = pygame.Rect(0, 0, 6000, 3500)
    if not map_rect.colliderect(rect) or character.server.obstacles.collide(character, rect) or character.server.zones.collide(character, rect):
        return False
    return True
                
            
__ALL__ = ['CentralBuilding', 'PortableCentralBuilding', 'FitnessCenter', 'Balloonist', 'Gym', 'RunningTrack', 'HealthCenter', 'BarrelMaker', 'ConstructionSite', 'RobotFactory', 'Restaurant', 'MinersGuild', 'FarmersGuild', 'Inn']
