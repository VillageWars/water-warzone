import pygame
import toolbox
import random
from events import *
from elements import Building, SCREEN

INNSTART, INNEND = 300, 900

# As to not repeat this in the "no" option
BTB = 'buy this building!'  
UPG = 'upgrade this building!'
BUY = 'buy this!'

def get_innpc(inn):
    NPCs = [Botanist, Merchant, Alchemist, Rancher]
    if inn.level > 1:
        NPCs.extend([Mayor, Repairer, Builder, AdvancedBalloonist])
    for NPC in NPCs[:]:
        if getattr(inn.channel.build_to_place, 'type', None) == NPC.building_type:
            NPCs.remove(NPC); continue
        for building in inn.channel.get_buildings():
            if building.type == NPC.building_type:
                NPCs.remove(NPC); break
    if NPCs:
        NPC_class = random.choice(NPCs)
        return NPC_class(inn)

class InnPC(Building):
    type = 'Erroneous Generic InnPC'
    info = 'InnPC: Hello, there!', ''
    dimensions = (50, 50)
    building_cost = (50, 0)
    building_type = 'Erroneous Generic InnPC House'
    building_info = 'Erroneous Generic InnPC House Information.', 'Please contact Aaron in order to fix this.'
    building_dimensions = (400, 400)
    building_max_health = 50
    building_methods = {}
    def __init__(self, inn, coords=None):
        self.inn = inn
        self.server = inn.server
        self.x, self.y = coords or (self.inn.x + random.randint(-100, 100), self.inn.y + 130)
        self.character = inn.character
        self.channel.add_message('The %s has arrived!' % self.type, color=(128,0,128), time=160)
        self.count = random.randint(30*60*1, 30*60*5)  # Between one and five minutes
        self.rect = pygame.Rect(0, 0, *self.dimensions)
        self.rect.center = self.x, self.y
        self.level = 1
        self.init()
    @property
    def channel(self):
        return self.character.channel
    @property
    def health(self):
        return 100
    @property
    def angle(self):
        return toolbox.getAngle(self.x, self.y, self.character.x, self.character.y)
    def create_building(self):
        attributes = {
            'type': self.building_type,
            'info': self.building_info,
            'dimensions': self.building_dimensions,
            'max_health': self.building_max_health,
            'options': self.options,
            'get_4th_info': self.get_4th_info,
            'condition': self.condition}
        for method in self.building_methods:
            attributes[method] = self.building_methods[method]
        class_name = self.building_type.replace(' ', '').replace('\'', '')
        parent_classes = (Building,)
        return type(class_name, parent_classes, attributes)  # Syntax for creating a class with a `class` statement
    def options(self, player):
        return {}
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
            l.append(option)

        options = []
        if hasattr(self, 'options'):
            for option in self.options(channel.character):
                if self.condition(channel.character, option['action']):
                    option_complete(options, option)
        option_complete(options, {'name': 'Out', 'action': self.Out})
        return options

    def gen_window(self, channel):
        window = {'text': self.info,
                  'object': self,
                  'options': self.gen_options(channel)}
        channel.window = window
        channel.in_window = True
        channel.in_innpc_window = True
        channel.Send({'action':'sound', 'sound':'ow'})

    def update(self):
        self.count -= 1
        if self.count == 0:
            self.depart()
        for p in self.server.users:
            visible_rect = p.character.get_rect(self.rect)
            if SCREEN.colliderect(visible_rect):
                p.to_send.append({'action':'draw_InnPC',
                                  'type':self.type,
                                  'coords':visible_rect.center,
                                  'angle':self.angle,
                                  'color':self.inn.channel.color,
                                  'health':self.health})

    def depart(self, comeback=True):
        self.inn.NPC = None
        self.inn.channel.add_message('The %s has departed.' % self.type, color=(128,0,128), time=160)
        if comeback:
            self.inn.count = random.randint(INNSTART, INNEND)
            if self.inn.level > 1 and self.inn.count > 150:
                self.inn.count -= 150

class Botanist(InnPC):
    type = 'Botanist'
    info = ('Botanist: Hello, there! I sell sapplings, that will grow into any of the trees that the',
            'game started with! I also sell spiky bushes. They are the same size as crates, and will',
            'inflict damage on players that travel through them.')
    building_cost = (0, 70)
    building_type = 'Botanist\'s Lab'
    building_info = 'This building is for the Botanist, so that you can always buy from it.', ''
    building_dimensions = (490, 490)
    building_max_health = 220
    def options(self, player):
        return [{'name': 'Buy a sappling',
                    'food-cost': 7,
                    'action': self.buy_sappling,
                    'no': BUY},
                {'name': 'Buy a spiky bush',
                    'food-cost': 1,
                    'action': self.buy_spiky_bush,
                    'no': BUY}]
    def get_4th_info(self, channel):
        return 'Gardening XP', str(channel.character.garden_xp)
    def buy_spiky_bush(self, character):
        character.channel.add_message('You have bought a spiky bush for 1 food.')
        character.spiky_bushes += 1
        character.garden_xp += 1
    def buy_sappling(self, character):
        character.channel.add_message('You have bought a sappling for 7 food.')
        character.channel.text = 'Press c to place sappling'
        character.garden_xp += 20

class Merchant(InnPC):
    type = 'Merchant'
    info = ('Merchant: Hello, there! Give me either food or gold and I\'ll give you the other.', '')
    building_cost = (27, 27)
    building_type = 'Market'
    building_info = 'This building is for the Merchant, so that you can always trade', 'gold for food and food for gold.'
    building_dimensions = (490, 490)
    building_max_health = 220
    def options(self, character):
        return [{'name': 'Buy 10 gold',
                    'food-cost': 10,
                    'action': self.trade_for_gold,
                    'no': 'trade!'},
                {'name': 'Buy 10 food',
                    'gold-cost': 10,
                    'action': self.trade_for_food,
                    'no': 'trade!'}]
    def get_4th_info(self, channel):
        return 'Resources', str(channel.character.gold) + ' gold, ' + str(channel.character.food) + ' food'
    def trade_for_gold(self, character):
        character.gold += 10
        character.channel.add_message('You have traded 10 food for 10 gold.')
    def trade_for_food(self, character):
        character.food += 10
        character.channel.add_message('You have traded 10 gold for 10 food.')

class Alchemist(InnPC):
    type = 'Alchemist'
    info = 'Alchemist: Greetings. I can change stone into gold. I might do so for you, for a little money.', ''
    building_cost = (60, 0)
    building_type = 'Alchemist\'s Lab'
    building_info = 'This building is for the Alchemist, so that he can always stay', 'with you.'
    building_dimensions = (490, 490)
    building_max_health = 220
    mine = None
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def determine_mine(self):
        for building in self.channel.get_buildings():
            if building.type == 'Miner\'s Guild':
                self.mine = building.miner.yard
                break
    def options(self, character):
        return [{'name': '+10 to Gold Discovery Rate',
                    'gold-cost': 4,
                    'action': self.rate1},
                {'name': '+250 to Gold Discovery Rate',
                    'gold-cost': 60,
                    'action': self.rate2}]
    def condition(self, character, action, **kwargs):
        self.determine_mine()
        if_is = self.if_is(action)
        if (if_is('rate1') or if_is('rate2')) and (self.mine is None or self.mine.production == 250):
            return False
        return super().condition(character, action, **kwargs)
    def get_4th_info(self, channel):
        return 'Gold Discovery Rate', (str(1250 - self.mine.production) if self.mine else 'unknown')
    def rate1(self, character):
        character.channel.add_message('You have increased your Gold Discovery Rate by 10 for 10 gold.')
        self.mine.production = max(250, self.mine.production - 10)
    def rate2(self, character):
        character.channel.add_message('You have increased your Gold Discovery Rate by 250 for 60 gold.')
        self.mine.production = max(250, self.mine.production - 250)

class Rancher(InnPC):
    type = 'Rancher'
    info = 'Alchemist: Howdy, folks! I know better techniques for growing food.', 'I could sell some of those ideas, if you want.'
    building_cost = (0, 60)
    building_type = 'Ranch'
    building_info = 'This building is for the Rancher, so that he can always stay', 'with you.'
    building_dimensions = (490, 490)
    building_max_health = 220
    farm = None
    def determine_farm(self):
        for building in self.channel.get_buildings():
            if building.type == 'Farmer\'s Guild':
                self.farm = building.farmer.yard
                break
    def options(self, character):
        return [{'name': '+10 to Food Production Rate',
                    'food-cost': 4,
                    'action': self.rate1},
                {'name': '+250 to Food Production Rate',
                    'food-cost': 60,
                    'action': self.rate2}]
    def condition(self, character, action, **kwargs):
        self.determine_farm()
        if_is = self.if_is(action)
        if (if_is('rate1') or if_is('rate2')) and (self.farm is None or self.farm.production == 250):
            return False
        return super().condition(character, action, **kwargs)
    def get_4th_info(self, channel):
        return 'Food Production Rate', (str(1250 - self.farm.production) if self.farm else 'unknown')
    def rate1(self, character):
        character.channel.add_message('You have increased your Food Production Rate by 10 for 10 food.')
        self.farm.production = max(250, self.farm.production - 10)
    def rate2(self, character):
        character.channel.add_message('You have increased your Food Production Rate by 250 for 60 food.')
        self.farm.production = max(250, self.farm.production - 250)

class Mayor(InnPC):
    type = 'Mayor'
    info = ('Mayor: I\'m into politics. Maybe I\'m useless to you right now, but build me a',
            'Town Hall and you won\'t regret it. It\'ll have five hundred health and will',
            'repair itself automatically if left alone.')
    building_cost = (100, 50)
    building_type = 'Town Hall'
    building_info = 'This building has 500 HP! It\'ll also repair itself', 'fully if it hasn\'t been attacked in a minute.'
    building_dimensions = (560, 540)
    building_max_health = 500
    def building_init(self):
        self.count = 0
    def building_update(self, *args, **kwargs):
        Building.update(self, *args, **kwargs)
        if self.count:
            self.count -= 1
        if self.count == 0:
            self.health = self.max_health
    def building_getHurt(self, *args, **kwargs):
        Building.getHurt(self, *args, **kwargs)
        self.count = 1800
    building_methods = {'init': building_init,
                        'update': building_update,
                        'getHurt': building_getHurt}

class Repairer(InnPC):
    type = 'Repairer'
    info = ('Repairer: Hello, there! Low on food? I\'ll repair everything in your village for just 50 gold!', '')
    building_cost = (10, 60)
    building_type = 'Repair Center'
    building_info = 'This building is for the Repairer, so that you can repair your village with ease!', ''
    building_dimensions = (490, 490)
    building_max_health = 290
    def options(self, character):
        return [{'name': 'Repair Village',
                    'gold-cost': 50,
                    'action': self.repair}]
    def condition(self, character, action, **kwargs):
        if_is = self.if_is(action)
        if if_is('repair') and len([b for b in self.channel.get_buildings() if b.health < b.max_health]) == 0:
            return False
        return super().condition(character, action, **kwargs)
    def get_4th_info(self, channel):
        return ('Buildings needing repair', str(len([b for b in self.channel.get_buildings() if b.health < b.max_health])))
    def repair(self, character):
        repaired_buildings = 0
        for building in self.channel.get_buildings():
            if building.health < building.max_health:
                repaired_buildings += 1
            building.health = building.max_health
        character.channel.add_message(f'You repaired {repaired_buildings} building(s) for 50 gold.')

class Builder(InnPC):
    type = 'Builder'
    info = ('Builder: As long as I\'m at the Inn, all the buildings you buy are', 'smaller!')
    building_cost = (30, 0)
    building_type = 'Builder\'s'
    building_info = 'This building is for the Builder. As long as this buildings isn\'t broken,', 'all the buildings you buy will be smaller.'
    building_dimensions = (392, 392)  # {490, 490} * 0.8
    building_max_health = 290
    def options(self, character):
        return [{'name': '+1 minute till the Walls fall',
                    'food-cost': 100,
                    'action': self.add_minute}]
    def condition(self, character, action, **kwargs):
        if_is = self.if_is(action)
        if if_is('add_minute') and self.server.fallen:
            return False
        return super().condition(character, action, **kwargs)
    def get_4th_info(self, channel):
        if self.server.fallen: return 'Walls fallen', 'Yes'
        return 'Time till the Walls fall', toolbox.getTime(self.server)
    def add_minute(self, character):
        character.channel.add_message('You added a minute till the Walls will fall.')
        self.server.upwall.count += 30*60
        self.server.leftwall.count += 30*60
        self.server.barbarian_count += 30*60

class AdvancedBalloonist(InnPC):
    type = 'Advanced Balloonist'
    info = ('Advanced Balloonist: I\'m much more talented than that regular balloonist.', 'You\'re lucky you got me!',)
    building_cost = (140, 0)
    building_type = 'Advanced Balloonist'
    building_info = 'This is the Advanced Balloonist\'s building, so that you can', 'upgrade your shot speed easily.'
    building_dimensions = (490, 490)
    building_max_health = 300
    def options(self, character):
        return [{'name': '+ Shot Speed',
                    'gold-cost': 280,
                    'action': self.increase_shot_speed}]
    def condition(self, character, action, **kwargs):
        if_is = self.if_is(action)
        if if_is('increase_shot_speed') and character.shot_speed == 1:
            return False
        return super().condition(character, action, **kwargs)
    def get_4th_info(self, channel):
        return 'Shot Speed', str(16-channel.character.shot_speed)  # Reversed
    def increase_shot_speed(self, character):
        character.channel.add_message('You increased your shot speed for 280 gold.')
        character.shot_speed -= 1

class RetiredBarbarian(InnPC):
    type = 'Retired Barbarian'
    info = ('Retired Barbarian: Hello. I\'m a barbarian. What\'s that? No, I',
            'mean I used to be a barbarian. I see you\'ve had the honor of',
            'defeating the enemy tribe of my old one.',
            'As a reward, I am selling you some useful barbarian stuff.')
    building_cost = (40, 40)
    building_type = 'Retired Barbarian Outpost'
    building_info = 'This is the outpost of the Retired Barbarian.', '(Note: He doesn\'t deserve this luxury! You wasted your money.)'
    building_dimensions = (600, 490)
    building_max_health = 160
    def options(self, character):
        return [{'name': 'Buy a Barbarian Shield',
                    'food-cost': 160,
                    'action': self.buy_shield},
                {'name': 'Buy a Barbarian Crossbow',
                    'food-cost': 100,
                    'action': self.buy_crossbow}]
    def condition(self, character, action, **kwargs):
        if_is = self.if_is(action)
        if if_is('buy_shield') and character.has_shield:
            return False
        if if_is('buy_crossbow') and character.barbshoot_cooldown >= 0:
            return False
        return super().condition(character, action, **kwargs)
    def get_4th_info(self, channel):
        return 'Need Shield', str(not channel.character.has_shield)
    def buy_shield(self, character):
        character.channel.add_message('You bought a Barbarian Shield for 160 food.')
        character.has_shield = True
    def buy_crossbow(self, character):
        character.channel.add_message('You bought a barbarian crossbow for 100 food.')
        character.barbshoot_cooldown = 50

class Adventurer(InnPC):
    type = 'Adventurer'
    info = ('Adventurer: Hello, I\'m the Adventurer. See for youself what I can do!', )
    building_cost = (0, 20)
    building_type = 'Adventuring Center'
    building_info = 'This building is for the Adventurer.', 'Having this building is the best.'
    building_dimensions = (510, 400)
    building_max_health = 300
    def options(self, character):
        return [{'name': 'End Current Event (Free)',
                    'action': self.end_current_event},
                {'name': 'Trigger a Barbarian Raid',
                    'gold-cost': 45,
                    'action': self.trigger_barbarian_raid,
                    'no': 'trigger a Barbarian Raid!'},
                {'name': 'Trigger a huge Barbarian Raid!',
                    'gold-cost': 100,
                    'action': self.trigger_huge_barbarian_raid,
                    'no': 'Trigger a huge Barbarian Raid!'}]
    def condition(self, character, action, **kwargs):
        if_is = self.if_is(action)
        if len(self.server.events):
            if if_is('trigger_barbarian_raid') or if_is('trigger_huge_barbarian_raid'):
                return False
        elif if_is('end_current_event'):
                return False
        return super().condition(character, action, **kwargs)
    def get_4th_info(self, channel):
        return 'Current Event', ', '.join([event.type for event in self.server.events])
    def trigger_barbarian_raid(self, character):
        BarbarianRaid(self.server)
    def trigger_huge_barbarian_raid(self, character):
        BarbarianRaid(self.server, 19 + random.randint(0, 4))
    def end_current_event(self, character):
        for channel in self.server.users:
            channel.add_message(character.name + ' has ended the current event.', color=(0,0,255))
            channel.to_send.append({'action':'music_change', 'music':'village'})
        self.server.events.empty()