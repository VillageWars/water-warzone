import pygame
import toolbox as t
import random as r
from building import *
from events import *

INNSTART = 300
INNEND = 900

def get_innpc(inn):
    npcs = [Botanist, Merchant, Rancher, Alchemist]
    if inn.level > 1:
        npcs.extend([Mayor, Repairer, Builder, Advanced_balloonist])
    bds = inn.owner.get_buildings()
    for NPC in npcs[:]:
        if NPC.building in [bd.__class__ for bd in bds]:
            npcs.remove(NPC)
        
    try:
        return r.choice(npcs)(inn)
    except:
        return


class Builders(Building):
    dimensions = (490 * 0.8, 490 * 0.8)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building is for the Builder. As long as this buildings isn\'t broken, all the buildings you buy will be smaller.', '')
        self.type = 'Builder\'s'
        self.health = self.max_health = 300
        self.dimensions = type(self).dimensions

        self.post_init(rect)

    def minute(self, player):
        if not self.server.fallen:
            if player.food > 90:
                player.food -= 90
                player.channel.message = 'You added a minute till the Walls fall.'
                player.channel.message_color = (255, 205, 0)
                player.channel.message_count = 160
                self.server.upwall.count += 30*60
                self.server.leftwall.count += 30*60
                self.server.barbarian_count += 30*60
                
            else:
                player.channel.message = 'You don\'t have enough food to do this.'
                player.channel.message_color = (255,0,0)
                player.channel.message_count = 150
        else:
            player.channel.message = 'The Walls have already fallen!'
            player.channel.message_color = (0,0,255)
            player.channel.message_count = 150
        self.Out(player)

    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            if self.server.fallen:
                channel.window = {'text':self.info,
                                  '4th_info':('Walls Fallen', 'True'),
                                  'health':(self.health, self.max_health),
                                  'building':self,
                                  'level':self.level,
                                  'options':[(0, self.heal), (1, self.Out)],
                                  'simp':('Heal', 'Out')}
            else:
                channel.window = {'text':self.info,
                                  '4th_info':('Time till the Walls fall', self.server.getTime()),
                                  'health':(self.health, self.max_health),
                                  'building':self,
                                  'level':self.level,
                                  'options':[(0, self.heal), (1, self.minute), (2, self.Out)],
                                  'simp':('Heal', 'Add a minute till the Walls fall (90 food)', 'Out')}

        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              '4th_info':('Walls Fallen', str(self.server.fallen)),
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 food)', 'Out']}

class RepairCenter(Building):
    dimensions = (490, 490)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building is for the Repairer, so that you can repair your village with ease!', '')
        self.type = 'Repair Center'
        self.health = self.max_health = 290
        self.dimensions = type(self).dimensions

        self.post_init(rect)

    def repair(self, player):
        if player.gold > 49:
            player.gold -= 50
            player.channel.message = 'Your village has been repaired for 50 gold.'
            player.channel.message_color = (255, 205, 0)
            player.channel.message_count = 160
            for b in player.channel.get_buildings():
                b.health = b.max_health
            
        else:
            player.channel.message = 'You don\'t have enough gold!'
            player.channel.message_color = (255,0,0)
            player.channel.message_count = 150
        self.Out(player)

    




    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            channel.window = {'text':self.info,
                              '4th_info':('Buildings needing repair', str(len([b for b in channel.get_buildings() if b.health < b.max_health]))),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.heal), (1, self.repair), (2, self.Out)],
                              'simp':('Heal', 'Repair Village (50 gold)', 'Out')}

        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              '4th_info':('Buildings needing repair', str(len([b for b in channel.get_buildings() if b.health < b.max_health]))),
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 food)', 'Out']}


class AdvancedBalloonistBuilding(Building):
    dimensions = (490, 490)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building is for the Advanced Balloonist NPC, so that you can upgrade your shot speed easily.', '')
        self.type = 'Advanced Balloonist'
        self.health = self.max_health = 300
        self.dimensions = type(self).dimensions

        self.post_init(rect)

    def speedgun(self, player):
        if player.shot_speed != 1:
            if player.gold > 279:
                player.gold -= 280
                player.channel.message = 'You increased your shoot speed for 280 gold.'
                player.channel.message_color = (255, 205, 0)
                player.channel.message_count = 160
                player.shot_speed -= 1
                
            else:
                player.channel.message = 'You don\'t have enough gold to do this.'
                player.channel.message_color = (255,0,0)
                player.channel.message_count = 150
        else:
            player.channel.message = 'Your balloon gun is already at its max! (Nobody\'s gonna stop you now)'
            player.channel.message_color = (0,0,255)
            player.channel.message_count = 150
        self.Out(player)

    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            channel.window = {'text':self.info,
                              '4th_info':('Shot Speed', str(16-channel.character.shot_speed)),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.heal), (1, self.speedgun), (2, self.Out)],
                              'simp':('Heal', '+ Shot Speed (280 gold)', 'Out')}

        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              '4th_info':('Shot Speed', str(16-channel.character.shot_speed)),
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 food)', 'Out']}


class TownHall(Building):
    dimensions = (560, 540)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building has 500 HP! It\'ll also repair itself fully if it hasn\'t been attacked in a minute.', '')
        self.type = 'Town Hall'
        self.health = self.max_health = 500
        self.dimensions = type(self).dimensions
        self.count = 0

        self.post_init(rect)

    def update(self):
        super().update()
        if self.count:
            self.count -= 1
            if not self.count:
                self.health = self.max_health

    def getHurt(self, damage, attacker):
        super().getHurt(damage, attacker)
        self.count = 1800


class AlchemistsLab(Building):
    dimensions = (490, 490)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building is for the Alchemist, so that you can always trade with it.', '')
        self.type = 'Alchemist\'s Lab'
        self.health = self.max_health = 220
        self.dimensions = type(self).dimensions

        self.post_init(rect)

    def rate1(self, player):
        if player.gold > 9:
            mine = None
            for b in self.owner.get_buildings():
                if b.__class__.__name__ == 'MinersGuild':
                    mine = b.miner.farm
                    break
            if mine is None:
                player.channel.message = 'Get a Miner\'s Guild first!'
                player.channel.message_color = (0,0,255)
                player.channel.message_count = 150
                self.Out(player)
                return
            if not mine.production == 250:
                player.gold -= 10
                player.channel.message = 'You have increased your Gold Discovery Rate by 10 for 10 gold.'
                player.channel.message_color = (255,205,0)
                player.channel.message_count = 150
                
                mine.production -= 10
                if mine.production < 250:
                    mine.production = 250
            else:
                player.channel.message = 'The Gold Discovery Rate is at its maximum!'
                player.channel.message_color = (0,0,255)
                player.channel.message_count = 150
        else:
            player.channel.message = 'You don\'t have enough gold!'
            player.channel.message_color = (255,0,0)
            player.channel.message_count = 150
        self.Out(player)

    def rate2(self, player):
        if player.gold > 149:
            mine = None
            for b in self.owner.get_buildings():
                if b.__class__.__name__ == 'MinersGuild':
                    mine = b.miner.farm
                    break
            if mine is None:
                player.channel.message = 'Get a Miner\'s Guild first!'
                player.channel.message_color = (0,0,255)
                player.channel.message_count = 150
                self.Out(player)
                return
            if not mine.production == 250:
                player.gold -= 150
                player.channel.message = 'You have increased your Gold Discovery Rate by 250 for 150 gold.'
                player.channel.message_color = (255,205,0)
                player.channel.message_count = 150
                
                mine.production -= 250
                if mine.production < 250:
                    mine.production = 250
            else:
                player.channel.message = 'The Gold Discovery Rate is at its maximum!'
                player.channel.message_color = (0,0,255)
                player.channel.message_count = 150
            
        else:
            player.channel.message = 'You don\'t have enough gold!'
            player.channel.message_color = (255,0,0)
            player.channel.message_count = 150
        self.Out(player)

    




    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            channel.window = {'text':self.info,
                              '4th_info':('Gold', str(channel.character.gold)),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.heal), (1, self.rate1), (2, self.rate2), (3, self.Out)],
                              'simp':('Heal', 'Increase Gold Discovery Rate by 10 (10 gold)', 'Increase Gold Discovery Rate by 250 (150 gold)', 'Out')}

        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              '4th_info':('Gold', str(channel.character.gold)),
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 food)', 'Out']}

class Ranch(Building):
    dimensions = (490, 490)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building is for the Rancher, so that you can always trade with it.', '')
        self.type = 'Ranch'
        self.health = self.max_health = 220
        self.dimensions = type(self).dimensions

        self.post_init(rect)

    def rate1(self, player):
        if player.food > 9:
            farm = None
            for b in self.owner.get_buildings():
                if b.__class__.__name__ == 'FarmersGuild':
                    farm = b.farmer.farm
                    break
            if farm is None:
                player.channel.message = 'Get a Farmer\'s Guild first!'
                player.channel.message_color = (0,0,255)
                player.channel.message_count = 150
                self.Out(player)
                return
            if not farm.production == 250:
                player.food -= 10
                player.channel.message = 'You have increased your Food Production Rate by 10 for 10 food.'
                player.channel.message_color = (255,205,0)
                player.channel.message_count = 150
                
                farm.production -= 10
                if farm.production < 250:
                    farm.production = 250
            else:
                player.channel.message = 'The Food Production Rate is at its maximum!'
                player.channel.message_color = (0,0,255)
                player.channel.message_count = 150
        else:
            player.channel.message = 'You don\'t have enough food!'
            player.channel.message_color = (255,0,0)
            player.channel.message_count = 150
        self.Out(player)

    def rate2(self, player):
        if player.food > 149:
            farm = None
            for b in self.owner.get_buildings():
                if b.__class__.__name__ == 'FarmersGuild':
                    farm = b.farmer.farm
                    break
            if farm is None:
                player.channel.message = 'Get a Farmer\'s Guild first!'
                player.channel.message_color = (0,0,255)
                player.channel.message_count = 150
                self.Out(player)
                return
            if not farm.production == 250:
                player.food -= 150
                player.channel.message = 'You have increased your Food Production Rate by 250 for 150 food.'
                player.channel.message_color = (255,205,0)
                player.channel.message_count = 150
                
                farm.production -= 250
                if farm.production < 250:
                    farm.production = 250
            else:
                player.channel.message = 'The Food Production Rate is at its maximum!'
                player.channel.message_color = (0,0,255)
                player.channel.message_count = 150
            
        else:
            player.channel.message = 'You don\'t have enough food!'
            player.channel.message_color = (255,0,0)
            player.channel.message_count = 150
        self.Out(player)



    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            channel.window = {'text':self.info,
                              '4th_info':('Food', str(channel.character.food)),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.heal), (1, self.rate1), (2, self.rate2), (3, self.Out)],
                              'simp':('Heal', 'Increase Food Production Rate by 10 (10 food)', 'Increase Food Production Rate by 250 (150 food)', 'Out')}

        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              '4th_info':('Gold', str(channel.character.gold)),
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 food)', 'Out']}


class BotanistsLab(Building):
    dimensions = (490, 490)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building is for the Botanist, so that you can always buy from it.', '')
        self.type = 'Botanist\'s Lab'
        self.health = self.max_health = 220
        self.dimensions = type(self).dimensions

        self.post_init(rect)

    def spiky_bush(self, player):
        if player.food > 0:
            player.food -= 1
            player.channel.message = 'You have bought a spiky bush for 1 food.'
            player.spiky_bushes += 1
            player.channel.message_color = (255,205,0)
            player.channel.message_count = 150
            player.garden_xp += 1
        else:
            player.channel.message = 'You don\'t have enough food to buy this!'
            player.channel.message_color = (255,0,0)
            player.channel.message_count = 150
        self.Out(player)

    def sappling(self, player):
        if player.food > 6:
            player.food -= 7
            player.channel.message = 'You have bought a sappling for 7 food.'
            player.channel.text = 'Press c to place sappling'
            player.channel.message_color = (255,205,0)
            player.channel.message_count = 150
            player.garden_xp += 20
        else:
            player.channel.message = 'You don\'t have enough food to buy this!'
            player.channel.message_color = (255,0,0)
            player.channel.message_count = 150
        self.Out(player)

    def vine(self, player):
        if player.food > 14:
            player.food -= 15
            player.channel.message = 'You have bought an invasive vine for 15 food.'
            player.channel.text = 'Press c to place invasive vine'
            player.channel.message_color = (255,205,0)
            player.channel.message_count = 150
        else:
            player.channel.message = 'You don\'t have enough food to buy this!'
            player.channel.message_color = (255,0,0)
            player.channel.message_count = 150
        self.Out(player)




    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            channel.window = {'text':self.info,
                              '4th_info':('Gardening XP', str(channel.character.garden_xp)),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.heal), (1, self.sappling), (2, self.spiky_bush), (3, self.Out)],
                              'simp':('Heal', 'Buy a sappling (7 food)', 'Buy a spiky bush (1 food)', 'Out')}

        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              '4th_info':('Gardening XP', str(channel.character.garden_xp)),
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 food)', 'Out']}

class Market(Building):
    dimensions = (490, 490)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building is for the Merchant, so that you can always trade', 'gold for food and food for gold.')
        self.type = 'Market'
        self.health = self.max_health = 220
        self.dimensions = type(self).dimensions

        self.post_init(rect)

    def tradegold(self, player):
        if player.food > 9:
            player.food -= 10
            player.gold += 10
            player.channel.message = 'You have traded 10 food for 10 gold.'
            player.channel.message_color = (255,205,0)
            player.channel.message_count = 150
        else:
            player.channel.message = 'You don\'t have enough food to trade!'
            player.channel.message_color = (255,0,0)
            player.channel.message_count = 150
        self.Out(player)
    def tradefood(self, player):
        if player.gold > 9:
            player.gold -= 10
            player.food += 10
            player.channel.message = 'You have traded 10 gold for 10 food.'
            player.channel.message_color = (255,205,0)
            player.channel.message_count = 150
        else:
            player.channel.message = 'You don\'t have enough gold to trade!'
            player.channel.message_color = (255,0,0)
            player.channel.message_count = 150
        self.Out(player)

    
    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            channel.window = {'text':self.info,
                              '4th_info':('Resources', str(self.owner.character.gold) + ' gold, ' + str(self.owner.character.food) + ' food'),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.heal), (1, self.tradegold), (2, self.tradefood), (3, self.Out)],
                              'simp':('Heal', 'Trade 10 food for 10 gold', 'Trade 10 gold for 10 food', 'Out')}

        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              '4th_info':('Resources', str(self.owner.character.gold) + ' gold, ' + str(self.owner.character.food) + ' food'),
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 food)', 'Out']}

    
class RetiredBarbarianOutpost(Building):
    dimensions = (600, 490)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building is for the Retired Barbarian.', '')
        self.type = 'Retired Barbarian Outpost'
        self.health = self.max_health = 160
        self.dimensions = type(self).dimensions

        self.post_init(rect)

    def crossbow(self, player):
        if player.barbshoot_cooldown >= 0:
            player.channel.message = 'You already have a barbarian crossbow!'
            player.channel.message_color = (0,0,255)
            player.channel.message_count = 150
        elif player.food > 99:
            player.food -= 100
            player.channel.message = 'You bought a barbarian crossbow for 100 food.'
            player.channel.message_color = (255, 205, 0)
            player.channel.message_count = 160
            player.barbshoot_cooldown = 50
        else:
            player.channel.message = 'You don\'t have enough food to buy this.'
            player.channel.message_color = (255,0,0)
            player.channel.message_count = 150
        self.Out(player)

    def shield(self, player):
        if player.has_shield:
            player.channel.message = 'You already have a shield!'
            player.channel.message_color = (0,0,255)
            player.channel.message_count = 150
        elif player.food > 159:
            player.food -= 160
            player.channel.message = 'You bought a Barbarian Shield for 160 food.'
            player.channel.message_color = (255, 205, 0)
            player.channel.message_count = 160
            player.has_shield = True
        else:
            player.channel.message = 'You don\'t have enough food to buy this.'
            player.channel.message_color = (255,0,0)
            player.channel.message_count = 150
        self.Out(player)    




    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            channel.window = {'text':self.info,
                              '4th_info':('Need Shield', str(not channel.character.has_shield)),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              'options':[(0, self.heal), (1, self.shield), (2, self.crossbow), (3, self.Out)],
                              'simp':('Heal', 'Buy a shield (160 food)', 'Buy a barbarian crossbow (100 food)', 'Out')}

        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              '4th_info':('Need Shield', str(not channel.character.has_shield)),
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 food)', 'Out']}


class AdventuringCenter(Building):
    dimensions = (510, 400)
    def __init__(self, server, x, y, owner, rect):
        Building.__init__(self, server, x, y, owner)
        self.info = ('This building is for the Adventurer. Having this building is the best.', '')
        self.type = 'Adventuring Center'
        self.health = self.max_health = 300
        self.dimensions = type(self).dimensions

        self.post_init(rect)

    def barbarianRaid(self, player):
        if player.gold > 44:
            player.gold -= 45
            BarbarianRaid(self.server)
            
        else:
            player.channel.message = 'You don\'t have enough gold!'
            player.channel.message_color = (255,0,0)
            player.channel.message_count = 150
        self.Out(player)

    def barbarianRaidHuge(self, player):
        if player.gold > 99:
            player.gold -= 100
            BarbarianRaid(self.server, 19 + randint(0, 4))
            
        else:
            player.channel.message = 'You don\'t have enough gold!'
            player.channel.message_color = (255,0,0)
            player.channel.message_count = 150
        self.Out(player)

    def end(self, player):
        for p in self.server.players:
            p.message = player.channel.username + ' has ended the current event.'
            p.message_color = (255, 205, 0)
            p.message_count = 160
            p.to_send.append({'action':'music_change', 'music':'village'})
        self.server.event = Event(self.server)
        self.Out(player)

    def open_window(self, channel):
        if self.state == 'alive':
            channel.in_window = True
            if self.server.event.__class__ != Event:
                channel.window = {'text':self.info,
                                  '4th_info':('Current Event', self.server.event.__class__.__name__),
                                  'health':(self.health, self.max_health),
                                  'building':self,
                                  'level':self.level,
                                  'options':[(0, self.heal), (1, self.end), (2, self.Out)],
                                  'simp':('Heal', 'End Current Event (Free)', 'Out')}
            else:
                channel.window = {'text':self.info,
                                  '4th_info':('Buildings needing repair', str(len([b for b in channel.get_buildings() if b.health < b.max_health]))),
                                  'health':(self.health, self.max_health),
                                  'building':self,
                                  'level':self.level,
                                  'options':[(0, self.heal), (1, self.barbarianRaid), (2, self.barbarianRaidHuge), (3, self.Out)],
                                  'simp':('Heal', 'Trigger a Barbarian Raid (45 gold)', 'Trigger a huge Barbarian Raid (100 gold)', 'Out')}

        elif self.state == 'broken':
            channel.in_window = True
            channel.window = {'text':('This building is broken.', ''),
                              'health':(self.health, self.max_health),
                              'building':self,
                              'level':self.level,
                              '4th_info':('Buildings needing repair', str(len([b for b in channel.get_buildings() if b.health < b.max_health]))),
                              'options':[(0, self.clear), (1, self.Out)],
                              'simp':['Clear (2 food)', 'Out']}



class InnPC():
    def __init__(self, inn):
        self.inn = inn
        self.type = type(self).__name__.replace('_', ' ').title()
        self.server = inn.server
        self.angle = 0
        self.x = self.inn.x + r.randint(-100, 100)
        self.y = self.inn.y + 130
        self.health = 100
        p = self.inn.owner
        p.message = 'The %s has arrived!' % self.type
        p.message_count = 160
        p.message_color = (128,0,128)
        self.count = r.randint(30*60*1, 30*60*5)
        self.rect = pygame.Surface((50, 50)).get_rect(center=(self.x, self.y))
        self.building = None
        
    @property
    def window(self):
        return {'text':(self.type + ':', 'Hello, there!'),
                'options':(('Out', self.Out),)}


    def Out(self, channel):
        channel.in_window = False
        channel.in_innpc_window = False
        channel.Send({'action':'sound', 'sound':'cw'})

    def update(self):
        self.count -= 1
        if self.count == 0:
            self.depart()
        self.angle = t.getAngle(self.x, self.y, self.inn.owner.character.x, self.inn.owner.character.y)
        for p in self.server.players:
            if not p.pending:
                p.to_send.append({'action':'draw_InnPC',
                                  'type':self.type,
                                  'coords':(p.character.get_x(self), p.character.get_y(self)),
                                  'angle':self.angle,
                                  'color':self.inn.owner.color,
                                  'health':self.health})

    def depart(self, comeback=True):
        self.inn.NPC = None
        p = self.inn.owner
        p.message = 'The %s has departed.' % self.type
        p.message_count = 160
        p.message_color = (128,0,128)
        if comeback:
            self.inn.count = r.randint(INNSTART, INNEND)
            if self.inn.level > 1 and self.inn.count > 150:
                self.inn.count -= 150


class Botanist(InnPC):
    building = BotanistsLab
    def __init__(self, inn):
        super().__init__(inn)
        self.cost = (0, 70)
        self.building = BotanistsLab

    @property
    def window(self):
        return {'text':(self.type + ':', 'Hello, there! I sell sapplings, that will grow into any of the trees that the game started with!',
                                         'I also sell spiky bushes. You might have heard of crates, they are the same size except that',
                                         'people can go through the spiky bush, it\'s just that they take damage.'),
                'options':(('Buy a sappling (7 food)', self.sappling), ('Buy a spiky bush (1 food)', self.spiky_bush), ('Out', self.Out))}


    def spiky_bush(self, channel):
        if channel.character.food > 0:
            channel.character.food -= 1
            channel.message = 'You have bought a spiky bush for 1 food.'
            channel.character.spiky_bushes += 1
            channel.message_color = (255,205,0)
            channel.message_count = 150
            channel.character.garden_xp += 1
        else:
            channel.message = 'You don\'t have enough food to buy this!'
            channel.message_color = (255,0,0)
            channel.message_count = 150
        self.Out(channel)

    def sappling(self, channel):
        if channel.character.food > 6:
            channel.character.food -= 7
            channel.message = 'You have bought a sappling for 7 food.'
            channel.text = 'Press c to place sappling'
            channel.message_color = (255,205,0)
            channel.message_count = 150
            channel.character.garden_xp += 20
        else:
            channel.message = 'You don\'t have enough food to buy this!'
            channel.message_color = (255,0,0)
            channel.message_count = 150
        self.Out(channel)

    



class Alchemist(InnPC):
    building = AlchemistsLab
    def __init__(self, inn):
        super().__init__(inn)
        self.cost = (80, 0)
        self.building = AlchemistsLab

    @property
    def window(self):
        return {'text':(self.type + ':', 'Greetings. I can change stone into gold. I might do so for you, for a little money.'),
                'options':(('Increase Gold Discovery Rate by 10 (10 gold)', self.rate1), ('Increase Gold Discovery Rate by 250 (150 gold)', self.rate2), ('Out', self.Out))}

    def rate1(self, channel):
        if channel.character.gold > 9:
            mine = None
            for b in self.inn.owner.get_buildings():
                if b.__class__.__name__ == 'MinersGuild':
                    mine = b.miner.farm
                    break
            if mine is None:
                player.channel.message = 'Get a Miner\'s Guild first!'
                player.channel.message_color = (0,0,255)
                player.channel.message_count = 150
                self.Out(player)
                return
            if mine and not mine.production == 250:
                channel.character.gold -= 10
                channel.message = 'You have increased your Gold Discovery Rate by 10 for 10 gold.'
                channel.message_color = (255,205,0)
                channel.message_count = 150
                mine.production -= 10
                if mine.production < 250:
                    mine.production = 250
            else:
                channel.message = 'The Gold Discovery Rate is at its maximum!'
                channel.message_color = (0,0,255)
                channel.message_count = 150
            
        else:
            channel.message = 'You don\'t have enough gold!'
            channel.message_color = (255,0,0)
            channel.message_count = 150
        self.Out(channel)

    def rate2(self, channel):
        if channel.character.gold > 149:
            mine = None
            for b in self.inn.owner.get_buildings():
                if b.__class__.__name__ == 'MinersGuild':
                    mine = b.miner.farm
                    break
            if mine is None:
                player.channel.message = 'Get a Miner\'s Guild first!'
                player.channel.message_color = (0,0,255)
                player.channel.message_count = 150
                self.Out(player)
                return
            if mine and not mine.production == 250:
                channel.character.gold -= 150
                channel.message = 'You have increased your Gold Discovery Rate by 250 for 150 gold.'
                channel.message_color = (255,205,0)
                channel.message_count = 150
                mine.production -= 250
                if mine.production < 250:
                    mine.production = 250
            else:
                channel.message = 'The Gold Discovery Rate is at its maximum!'
                channel.message_color = (0,0,255)
                channel.message_count = 150
            
        else:
            channel.message = 'You don\'t have enough gold!'
            channel.message_color = (255,0,0)
            channel.message_count = 150
        self.Out(channel)

class Rancher(InnPC):
    building = Ranch
    def __init__(self, inn):
        super().__init__(inn)
        self.cost = (0, 80)
        self.building = Ranch

    @property
    def window(self):
        return {'text':(self.type + ':', 'Howdy, folks! I know better techniques for growing food. I could sell some of those ideas, if you want.'),
                'options':(('Increase Food Production Rate by 10 (10 food)', self.rate1), ('Increase Food Production Rate by 250 (150 food)', self.rate2), ('Out', self.Out))}

    def rate1(self, channel):
        if channel.character.food > 9:
            farm = None
            for b in self.inn.owner.get_buildings():
                if b.__class__.__name__ == 'FarmersGuild':
                    farm = b.farmer.farm
                    break
            if farm is None:
                player.channel.message = 'Get a Farmer\'s Guild first!'
                player.channel.message_color = (0,0,255)
                player.channel.message_count = 150
                self.Out(player)
                return
            if not farm.production == 250:
                channel.character.food -= 10
                channel.message = 'You have increased your Food Production Rate by 10 for 10 food.'
                channel.message_color = (255,205,0)
                channel.message_count = 150
                
                farm.production -= 10
                if farm.production < 250:
                    farm.production = 250
            else:
                channel.message = 'The Food Production Rate is at its maximum!'
                channel.message_color = (0,0,255)
                channel.message_count = 150
                
        else:
            channel.message = 'You don\'t have enough food!'
            channel.message_color = (255,0,0)
            channel.message_count = 150
        self.Out(channel)

    def rate2(self, channel):
        if channel.character.food > 149:
            farm = None
            for b in self.inn.owner.get_buildings():
                if b.__class__.__name__ == 'FarmersGuild':
                    farm = b.farmer.farm
                    break
            if farm is None:
                player.channel.message = 'Get a Farmer\'s Guild first!'
                player.channel.message_color = (0,0,255)
                player.channel.message_count = 150
                self.Out(player)
                return
            if farm and not farm.production == 250:
                channel.character.food -= 150
                channel.message = 'You have increased your Food Production Rate by 250 for 150 food.'
                channel.message_color = (255,205,0)
                channel.message_count = 150
                
                farm.production -= 250
                if farm.production < 250:
                    farm.production = 250
            else:
                channel.message = 'The Food Production Rate is at its maximum!'
                channel.message_color = (0,0,255)
                channel.message_count = 150
                
            
        else:
            channel.message = 'You don\'t have enough food!'
            channel.message_color = (255,0,0)
            channel.message_count = 150
        self.Out(channel)


class Merchant(InnPC):
    building = Market
    def __init__(self, inn):
        super().__init__(inn)
        self.building = Market
        self.cost = (27, 27)

    @property
    def window(self):
        return {'text':(self.type + ':', 'Hello, there! Give me food or gold and I\'ll give you the other.'),
                'options':(('Trade 10 food for 10 gold', self.gold), ('Trade 10 gold for 10 food', self.food), ('Out', self.Out))}

    def gold(self, channel):
        if channel.character.food > 9:
            channel.character.food -= 10
            channel.character.gold += 10
            channel.message = 'You have traded 10 food for 10 gold.'
            channel.message_color = (255,205,0)
            channel.message_count = 150
        else:
            channel.message = 'You don\'t have enough food to trade.'
            channel.message_color = (255,0,0)
            channel.message_count = 150
        self.Out(channel)

    def food(self, channel):
        if channel.character.gold > 9:
            channel.character.gold -= 10
            channel.character.food += 10
            channel.message = 'You have traded 10 gold for 10 food.'
            channel.message_color = (255,205,0)
            channel.message_count = 150
        else:
            channel.message = 'You don\'t have enough gold to trade.'
            channel.message_color = (255,0,0)
            channel.message_count = 150
        self.Out(channel)



class Mayor(InnPC):
    building = TownHall
    def __init__(self, inn):
        super().__init__(inn)
        self.building = TownHall
        self.cost = (100, 50)

    @property
    def window(self):
        return {'text':(self.type + ':', 'I\'m in politics. Maybe I\'m useless to you for now, but build me a town hall and you won\'t regret\nit. It\'ll have five hundred health and will repair itself.'),
                'options':(('Out', self.Out),)}

class Retired_barbarian(InnPC):
    building = RetiredBarbarianOutpost
    def __init__(self, inn):
        super().__init__(inn)
        self.building = RetiredBarbarianOutpost
        self.cost = (0, 20)

    @property
    def window(self):
        return {'text':(self.type + ':', 'Hello. I\'m a barbarian. What\'s that? No, I mean I used to be a barbarian. I see you\'ve had the honor', 'of defeating the enemy tribe of my old one. As a reward, I am selling you some useful barbarian stuff.'),
                'options':(('Out', self.Out), ('Buy a Barbarian Shield (160 food)', self.shield), ('Buy a Barbarian Crossbow (100 food)', self.crossbow))}

    def shield(self, channel):
        if channel.character.has_shield:
            channel.message = 'You already have a shield!'
            channel.message_color = (0,0,255)
            channel.message_count = 150
        elif channel.character.food > 159:
            channel.character.food -= 160
            channel.message = 'You bought a Barbarian Shield for 160 food.'
            channel.message_color = (255,205,0)
            channel.message_count = 150
            channel.character.has_shield = True
        else:
            channel.message = 'You don\'t have enough food to buy this.'
            channel.message_color = (255,0,0)
            channel.message_count = 150
        self.Out(channel)

    def crossbow(self, channel):
        if channel.character.barbshoot_cooldown >= 0:
            channel.message = 'You already have a barbarian crossbow!'
            channel.message_color = (0,0,255)
            channel.message_count = 150
        elif channel.character.food > 99:
            channel.character.food -= 100
            channel.message = 'You bought a barbarian crossbow for 100 food.'
            channel.message_color = (255,205,0)
            channel.message_count = 150
            channel.character.barbshoot_cooldown = 50
        else:
            channel.message = 'You don\'t have enough food to buy this.'
            channel.message_color = (255,0,0)
            channel.message_count = 150
        self.Out(channel)


class Adventurer(InnPC):
    building = AdventuringCenter
    def __init__(self, inn):
        super().__init__(inn)
        self.building = AdventuringCenter
        self.cost = (40, 40)

    @property
    def window(self):
        return {'text':(self.type + ':', 'Hello, I\'m the Adventurer. See for youself what I can do!'),
                'options':(('Out', self.Out), ('Trigger a Barbarian Raid (45 gold)', self.barbarianRaid), ('Trigger a huge Babarian Raid (100 gold)', self.barbarianRaidHuge))}

    def barbarianRaid(self, channel):
        if channel.character.gold > 44:
            channel.character.gold -= 45
            BarbarianRaid(self.server)
        else:
            channel.message = 'You don\'t have enough gold to trigger a Barbarian Raid.'
            channel.message_color = (255,0,0)
            channel.message_count = 150
        self.Out(channel)
        
    def barbarianRaidHuge(self, channel):
        if channel.character.gold > 99:
            channel.character.gold -= 100
            BarbarianRaid(self.server, 19 + randint(0, 4))
        else:
            channel.message = 'You don\'t have enough gold to trigger a huge Barbarian Raid.'
            channel.message_color = (255,0,0)
            channel.message_count = 150
        self.Out(channel)



class Repairer(InnPC):
    building = RepairCenter
    def __init__(self, inn):
        super().__init__(inn)
        self.building = RepairCenter
        self.cost = (10, 60)

    @property
    def window(self):
        return {'text':(self.type + ':', 'Hello, there! Low on food? I\'ll repair everything in your village for just 50 gold!'),
                'options':(('Repair Village (50 gold)', self.repair), ('Out', self.Out))}

    def repair(self, channel):
        if channel.character.gold > 49:
            channel.character.gold -= 50
            channel.message = 'You repaired your entire village for 50 gold.'
            channel.message_color = (255,205,0)
            channel.message_count = 150
            for b in channel.get_buildings():
                b.health = b.max_health
        else:
            channel.message = 'You don\'t have enough gold to repair your village.'
            channel.message_color = (255,0,0)
            channel.message_count = 150
        self.Out(channel)




class Builder(InnPC):
    building = Builders
    def __init__(self, inn):
        super().__init__(inn)
        self.building = Builders
        self.cost = (30, 0)

    @property
    def window(self):
        base = {'text':(self.type + ':', 'As long as I\'m at the Inn, all the buildings you buy are smaller!')}
        if self.inn.server.fallen:
            base['options'] = (('Out', self.Out),)
        else:
            base['options'] = (('Add a minute till the Walls fall (100 food)', self.minute), ('Out', self.Out))
        return base
                

    def minute(self, channel):
        if not self.inn.server.fallen:
            if channel.character.food > 99:
                channel.character.food -= 100
                channel.message = 'You added a minute till the Walls fall.'
                channel.message_color = (255,205,0)
                channel.message_count = 150
                self.inn.server.upwall.count += 30*60
                self.inn.server.leftwall.count += 30*60
                self.inn.server.barbarian_count += 30*60
                
            else:
                channel.message = 'You don\'t have enough food to do this.'
                channel.message_color = (255,0,0)
                channel.message_count = 150
        else:
            channel.message = 'The Walls have already fallen!'
            channel.message_color = (0,0,255)
            channel.message_count = 150
        self.Out(channel)



class Advanced_balloonist(InnPC):
    building = AdvancedBalloonistBuilding
    def __init__(self, inn):
        super().__init__(inn)
        self.building = AdvancedBalloonistBuilding
        self.cost = (140, 0)

    @property
    def window(self):
        base = {'text':(self.type + ':', 'I\'m much more talented than the regular balloonist. You\'re lucky you got me!')}
        base['options'] = (('+ Shot Speed (280 gold)', self.speedgun), ('Out', self.Out))
        return base
                

    def speedgun(self, channel):
        player = channel.character
        if player.shot_speed != 1:
            if player.gold > 279:
                player.gold -= 280
                player.channel.message = 'You increased your shoot speed for 280 gold.'
                player.channel.message_color = (255, 205, 0)
                player.channel.message_count = 160
                player.shot_speed -= 1
                
            else:
                player.channel.message = 'You don\'t have enough gold to do this.'
                player.channel.message_color = (255,0,0)
                player.channel.message_count = 150
        else:
            player.channel.message = 'Your balloon gun is already at its max! (Nobody\'s gonna stop you now)'
            player.channel.message_color = (0,0,255)
            player.channel.message_count = 150
        self.Out(channel)

