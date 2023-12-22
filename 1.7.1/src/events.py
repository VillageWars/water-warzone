import pygame
from random import *
import toolbox as t
from balloon import Bolt
import InnPC

class Event():
    def __init__(self, server):
        self.server = server
        self.NPCs = []
    def update(self):
        pass


class BarbarianRaid():
    def __init__(self, server, num=None, spawn=None):
        self.server = server
        self.server.event = self

        for p in server.players:
            for b in p.get_buildings():
                if b.__class__.__name__ == 'Inn':
                    if b.NPC:
                        b.NPC.depart()
        if not num:
            self.num_barbarians = randint(4, 7)
            for p in self.server.playing:
                self.num_barbarians += 2
        else:
            self.num_barbarians = num
        if spawn is None:
            self.spawn = choice(['North', 'East', 'South', 'West'])
        else:
            self.spawn = spawn
        for p in self.server.players:
            p.message = 'A tribe of %s barbarians is aproaching from the %s!' % (self.num_barbarians, self.spawn)
            p.message_color = (128,0,128)
            p.message_count = 160
        
        self.barbarians = []
        self.NPCs = self.barbarians
        self.leader = BarbarianLeader(self)
        for b in range(self.num_barbarians - 1):
            Barbarian(self)

        for p in self.server.players:
            if not p.pending:
                p.Send({'action':'music_change', 'music':'barbarianraid'})

    def end(self, attacker=None):
        self.barbarians.clear()
        for p in self.server.players:
            if not p.pending:
                p.Send({'action':'music_change', 'music':'village'})
        if attacker:
            for b in attacker.channel.get_buildings():
                if b.__class__.__name__ == 'Inn':
                    npcs = [InnPC.Retired_barbarian, InnPC.Adventurer]
                    bds = attacker.channel.get_buildings()
                    for NPC in npcs[:]:
                        if NPC.building in [bd.__class__ for bd in bds]:
                            npcs.remove(NPC)
                    if npcs:
                        b.NPC = choice(npcs)(b)
        self.server.event = Event(self.server)

    def get_coords(self, r=240):
        coords = {'North':(3000, 400),
                'South':(3000, 3500),
                'East':(5600, 1800),
                'West':(400, 1800)
                }
        x, y = coords[self.spawn]

        starting = True
        while x < 50 or x > 5950 or y < 50 or y > 3850 or starting:
            x += randint(-r, r)
            y += randint(-r, r)
            starting = False

        
            

        for b in self.barbarians:
            if b.rect.colliderect(b.surf.get_rect(center=(x, y))):
                return self.get_coords(r=r+100)

        return x, y

    def update(self):
        if True:#try:
            for b in self.barbarians:
                b.update()
        #except:
            #self.end()
    

def Barbarian(event):
    eval(choice(['BarbarianArcher', 'BarbarianSwordsman', 'BarbarianSwordsman']) + '(event)')


class BarbarianLeader():
    def __init__(self, event):
        self.hurt = 0
        self.shield_count = 0
        self.shield_angle = 0
        self.speed = 2
        self.resistance = 2
        self.health = 100
        self.angle = 0
        self.touching = False
        
        self.event = event
        self.surf = pygame.Surface((50, 50))
        self.rect = self.surf.get_rect(center=(0, 0))
        self.x, self.y = self.event.get_coords()
        self.event.barbarians.append(self)
        self.surf = pygame.Surface((50, 50))
        self.rect = self.surf.get_rect(center=(self.x, self.y))

        for p in self.event.server.playing:
            self.resistance += 1.5

    @property
    def innerrect(self):
        return self.rect

    def explode(self, player, tnt):
        self.getHurt(player, 60, t.getAngle(tnt.x, tnt.y, self.x, self.y), 120)
        
    def update(self):
        if self.hurt:
            self.hurt -= 1
        if self.shield_count:
            self.shield_count -= 1

        

        touching = False
        for ob in self.event.server.obs:
            if self.rect.colliderect(ob.innerrect):
                touching = True
                if not self.touching:
                    self.getHurt(None, 12, self.angle + 180, 100)
        self.touching = touching
            

        maxdist = 10000
        player = None
        playerdist = maxdist
        for p in self.event.server.players:
            if not p.pending and not p.character.dead:
                if t.getDist(self.x, self.y, p.character.x, p.character.y) < maxdist:
                    maxdist = t.getDist(self.x, self.y, p.character.x, p.character.y)
                    player = p
                    playerdist = maxdist

        if player == None:
            for p in self.event.server.players:
                if not p.pending:
                    p.to_send.append({'action':'draw_barbarian',
                                  'type':'leader',
                                  'hurt':self.hurt,
                                  'coords':(p.character.get_x(self), p.character.get_y(self)),
                                  'angle':self.angle,
                                  'health':self.health,
                                  'shield':(self.shield_angle if self.shield_count else None)})
            return

        self.angle = t.getAngle(self.x, self.y, player.character.x, player.character.y)

        if playerdist < 400:
            self.speed = 1
        else:
            self.speed = 2

        x, y = t.getDir(self.angle, total=self.speed)

        self.x += x
        rect = self.surf.get_rect(center=(self.x, self.y))
        for ob in self.event.server.obs + self.event.barbarians:
            if rect.colliderect(ob.innerrect) and ob != self:
                if not self.touching:
                    self.x -= x
        self.y += y
        rect = self.surf.get_rect(center=(self.x, self.y))
        for ob in self.event.server.obs + self.event.barbarians:
            if rect.colliderect(ob.innerrect) and ob != self:
                if not self.touching:
                    self.y -= y

        self.rect = self.surf.get_rect(center=(self.x, self.y))



        for p in self.event.server.players:
            if not p.pending:
                if p.character.rect.colliderect(self.rect) and not p.character.dead:
                    result = p.character.getHurt(10, 'The Barbarian Leader', self.angle, 50)
                    if p.character.dead and result != 'BAM':
                        p.character.gold = 0
                        p.character.food = 0
        
        for p in self.event.server.players:
            if not p.pending:
                p.to_send.append({'action':'draw_barbarian',
                                  'type':'leader',
                                  'hurt':self.hurt,
                                  'coords':(p.character.get_x(self), p.character.get_y(self)),
                                  'angle':self.angle,
                                  'health':self.health,
                                  'shield':(self.shield_angle if self.shield_count else None)})
                
    def getHurt(self, attacker, damage, angle, knockback):
        if randint(0, 2) < 2 and attacker != self:
            self.shield_angle = angle + 180
            self.shield_count = 20
            for p in self.event.server.players:
                if not p.pending:
                    screen = pygame.Rect(0, 0, 1000, 650)
                    rect = pygame.Rect(0, 0, 1, 1)
                    rect.size = self.rect.size
                    rect.topleft = (p.character.get_x(self.rect), p.character.get_y(self.rect))
                    if screen.colliderect(rect):
                        p.to_send.append({'action':'sound','sound':'bump'})
            return ('repelled', self.shield_angle + randint(-20, 20))
        else:
            x, y = t.getDir(angle, total=(self.speed+knockback))

            self.x += x
            rect = self.surf.get_rect(center=(self.x, self.y))
            for ob in self.event.server.obs + self.event.barbarians:
                if rect.colliderect(ob.innerrect) and ob != self:
                    if not self.touching:
                        self.x -= x
            self.y += y
            rect = self.surf.get_rect(center=(self.x, self.y))
            for ob in self.event.server.obs + self.event.barbarians:
                if rect.colliderect(ob.innerrect) and ob != self:
                    if not self.touching:
                        self.y -= y

            self.hurt = 10

            self.rect = self.surf.get_rect(center=(self.x, self.y))

            self.health -= damage - self.resistance
            if self.health <= 0:
                if self in self.event.barbarians:
                    self.event.barbarians.remove(self)
                self.health = 0
                self.event.end(attacker)
                self.event.server.event = Event(self.event.server)
                for p in self.event.server.players:
                    if not p.pending:
                        p.message = 'The Barbarian tribe has been defeated.'
                        p.message_color = (128,0,128)
                        p.message_count = 160
                try:
                    attacker.gold += 300
                    attacker.food += 300
                except:
                    pass


class BarbarianArcher():
    
    def __init__(self, event):
        self.hurt = 0
        self.shield_count = 0
        self.shield_angle = 0
        self.gold = 50
        self.food = 50
        self.attack = 10
        self.knockback = 40
        self.balloon_speed = 17
        self.shoot_cooldown = 0
        self.speed = 2
        self.health = 100
        self.angle = 0
        
        self.event = event
        self.surf = pygame.Surface((50, 50))
        self.event.barbarians.append(self)
        self.rect = self.surf.get_rect(center=(0, 0))
        self.x, self.y = self.event.get_coords()
        self.surf = pygame.Surface((50, 50))
        self.rect = self.surf.get_rect(center=(self.x, self.y))
        
        

    @property
    def innerrect(self):
        return self.rect

    def explode(self, player, tnt):
        self.getHurt(player, 60, t.getAngle(tnt.x, tnt.y, self.x, self.y), 120)
        
    def update(self):
        if self.hurt:
            self.hurt -= 1
        if self.shield_count:
            self.shield_count -= 1
        if self.shoot_cooldown:
            self.shoot_cooldown -= 1

        

        for ob in self.event.server.obs:
            if self.rect.colliderect(ob.innerrect):
                self.x = self.event.leader.x
                self.y = self.event.leader.y
                condition = True
                while condition:
                    condition = False
                    x, y = t.getDir(self.angle, total=self.speed)
                    self.x += x
                    self.y += y
                    self.rect = self.surf.get_rect(center=(self.x, self.y))
                    
                    for ob in self.event.server.obs + self.event.barbarians:
                        if self.rect.colliderect(ob.innerrect) and ob != self:
                            condition = True
                    

                    
            
        maxdist = 10000
        playerdist = maxdist
        player = None
        for p in self.event.server.players:
            if not p.pending and not p.character.dead:
                if t.getDist(self.x, self.y, p.character.x, p.character.y) < maxdist:
                    maxdist = t.getDist(self.x, self.y, p.character.x, p.character.y)
                    player = p
                    playerdist = maxdist

        if player == None:
            for p in self.event.server.players:
                if not p.pending:
                    p.to_send.append({'action':'draw_barbarian',
                                  'type':'archer',
                                  'hurt':self.hurt,
                                  'coords':(p.character.get_x(self), p.character.get_y(self)),
                                  'angle':self.angle,
                                  'health':self.health,
                                  'shield':(self.shield_angle if self.shield_count else None)})
            return

        self.angle = t.getAngle(self.x, self.y, player.character.x, player.character.y)

        if playerdist < 350:
            self.speed = 0
            self.shoot()
        else:
            self.speed = 2

        x, y = t.getDir(self.angle, total=self.speed)

        self.x += x
        rect = self.surf.get_rect(center=(self.x, self.y))
        for ob in self.event.server.obs + self.event.barbarians:
            if rect.colliderect(ob.innerrect) and ob != self:
                self.x -= x
        self.y += y
        rect = self.surf.get_rect(center=(self.x, self.y))
        for ob in self.event.server.obs + self.event.barbarians:
            if rect.colliderect(ob.innerrect) and ob != self:
                self.y -= y

        self.rect = self.surf.get_rect(center=(self.x, self.y))

        for item in self.event.server.bushes:
            if self.rect.colliderect(item.innerrect):
                if item.__class__.__name__ == 'SpikyBush':
                    self.getHurt(self, 4.4, self.angle + 180, 0)
                else:
                    self.getHurt(self, 4, self.angle + 180, 0)

        for p in self.event.server.players:
            if not p.pending:
                if p.character.rect.colliderect(self.rect) and not p.character.dead:
                    result = p.character.getHurt(10, 'a Barbarian Archer', self.angle, 50, msg='<Victim> ran into <Attacker>. Their gold and food were stolen.')
                    if p.character.dead and result != 'BAM':
                        self.gold += p.character.gold
                        self.food += p.character.food
                        p.character.gold = 0
                        p.character.food = 0

        
        for p in self.event.server.players:
            if not p.pending:
                p.to_send.append({'action':'draw_barbarian',
                                  'type':'archer',
                                  'hurt':self.hurt,
                                  'coords':(p.character.get_x(self), p.character.get_y(self)),
                                  'angle':self.angle,
                                  'health':self.health,
                                  'shield':(self.shield_angle if self.shield_count else None)})

    def getHurt(self, attacker, damage, angle, knockback):
        if randint(0, 2) == 0 and attacker != self:
            self.shield_angle = angle + 180
            self.shield_count = 20
            for p in self.event.server.players:
                if not p.pending:
                    screen = pygame.Rect(0, 0, 1000, 650)
                    rect = pygame.Rect(0, 0, 1, 1)
                    rect.size = self.rect.size
                    rect.topleft = (p.character.get_x(self.rect), p.character.get_y(self.rect))
                    if screen.colliderect(rect):
                        p.to_send.append({'action':'sound','sound':'bump'})
            return ('repelled', self.shield_angle + randint(-20, 20))
        else:
        
            x, y = t.getDir(angle, total=(self.speed+knockback))

            self.x += x
            rect = self.surf.get_rect(center=(self.x, self.y))
            for ob in self.event.server.obs + self.event.barbarians:
                if rect.colliderect(ob.innerrect) and ob != self:
                    self.x -= x
            self.y += y
            rect = self.surf.get_rect(center=(self.x, self.y))
            for ob in self.event.server.obs + self.event.barbarians:
                if rect.colliderect(ob.innerrect) and ob != self:
                    self.y -= y
            self.hurt = 10
            self.rect = self.surf.get_rect(center=(self.x, self.y))

            self.health -= damage - 4
            if self.health <= 0:
                self.health = 0
                if self in self.event.barbarians:
                    self.event.barbarians.remove(self)
                for p in self.event.server.players:
                    if not p.pending:
                        p.message = 'A Barbarian Archer has been defeated!'
                        p.message_color = (255,205,0)
                        p.message_count = 160
                attacker.gold += self.gold
                attacker.food += self.food

    def shoot(self):
        if not self.shoot_cooldown:
            self.shoot_cooldown = 50
            Bolt(archer=self)


class BarbarianSwordsman():
    def __init__(self, event):
        self.hurt = 0
        self.angle = 0
        self.speed = 5
        self.health = 100
        self.shield_count = 0
        self.shield_angle = 0
        self.gold = 50
        self.food = 50
        self.speed = 2
        
        self.event = event
        self.surf = pygame.Surface((50, 50))
        self.event.barbarians.append(self)
        self.rect = self.surf.get_rect(center=(0, 0))
        self.x, self.y = self.event.get_coords()
        self.rect = self.surf.get_rect(center=(self.x, self.y))
        


    @property
    def innerrect(self):
        return self.rect

    def explode(self, player, tnt):
        self.getHurt(player, 60, t.getAngle(tnt.x, tnt.y, self.x, self.y), 120)
        
    def update(self):
        if self.hurt:
            self.hurt -= 1
        if self.shield_count:
            self.shield_count -= 1


        for ob in self.event.server.obs:
            if self.rect.colliderect(ob.innerrect):
                self.x = self.event.leader.x
                self.y = self.event.leader.y
                condition = True
                while condition:
                    condition = False
                    x, y = t.getDir(self.angle, total=self.speed)
                    self.x += x
                    self.y += y
                    self.rect = self.surf.get_rect(center=(self.x, self.y))
                    for ob in self.event.server.obs + self.event.barbarians:
                        if self.rect.colliderect(ob.innerrect) and ob != self:
                            condition = True
            
        maxdist = 10000
        playerdist = maxdist
        player = None
        for p in self.event.server.players:
            if not p.pending and not p.character.dead:
                if t.getDist(self.x, self.y, p.character.x, p.character.y) < maxdist:
                    maxdist = t.getDist(self.x, self.y, p.character.x, p.character.y)
                    player = p
                    playerdist = maxdist

        if player == None:
            for p in self.event.server.players:
                if not p.pending:
                    p.to_send.append({'action':'draw_barbarian',
                                  'type':'swordsman',
                                  'hurt':self.hurt,
                                  'coords':(p.character.get_x(self), p.character.get_y(self)),
                                  'angle':self.angle,
                                  'health':self.health,
                                  'shield':(self.shield_angle if self.shield_count else None)})
            return

        self.angle = t.getAngle(self.x, self.y, player.character.x, player.character.y)

        if playerdist < 350:
            self.speed = 5
        else:
            self.speed = 2

        x, y = t.getDir(self.angle, total=self.speed)

        self.x += x
        rect = self.surf.get_rect(center=(self.x, self.y))
        for ob in self.event.server.obs + self.event.barbarians:
            if rect.colliderect(ob.innerrect) and ob != self:
                self.x -= x
        self.y += y
        rect = self.surf.get_rect(center=(self.x, self.y))
        for ob in self.event.server.obs + self.event.barbarians:
            if rect.colliderect(ob.innerrect) and ob != self:
                self.y -= y

        self.rect = self.surf.get_rect(center=(self.x, self.y))

        for item in self.event.server.bushes:
            if self.rect.colliderect(item.innerrect):
                if item.__class__.__name__ == 'SpikyBush':
                    self.getHurt(self, 4.4, self.angle + 180, 0)
                else:
                    self.getHurt(self, 4, self.angle + 180, 0)

        for p in self.event.server.players:
            if not p.pending:
                if p.character.rect.colliderect(self.rect) and not p.character.dead:
                    result = p.character.getHurt(10, 'A Barbarian Swordsman', self.angle, 50, msg='<Attacker> killed <Victim> and stole their gold and food.')
                    if p.character.dead and result != 'BAM':
                        self.gold += p.character.gold
                        self.food += p.character.food
                        p.character.gold = 0
                        p.character.food = 0



        
        for p in self.event.server.players:
            if not p.pending:
                p.to_send.append({'action':'draw_barbarian',
                                  'type':'swordsman',
                                  'hurt':self.hurt,
                                  'coords':(p.character.get_x(self), p.character.get_y(self)),
                                  'angle':self.angle,
                                  'health':self.health,
                                  'shield':(self.shield_angle if self.shield_count else None)})

    def getHurt(self, attacker, damage, angle, knockback):

        if randint(0, 2) == 0 and attacker != self:
            self.shield_angle = angle + 180
            self.shield_count = 20
            for p in self.event.server.players:
                if not p.pending:
                    screen = pygame.Rect(0, 0, 1000, 650)
                    rect = pygame.Rect(0, 0, 1, 1)
                    rect.size = self.rect.size
                    rect.topleft = (p.character.get_x(self.rect), p.character.get_y(self.rect))
                    if screen.colliderect(rect):
                        p.to_send.append({'action':'sound','sound':'bump'})
            return ('repelled', self.shield_angle + randint(-20, 20))
        else:
        
            x, y = t.getDir(angle, total=(self.speed+knockback))

            self.x += x
            rect = self.surf.get_rect(center=(self.x, self.y))
            for ob in self.event.server.obs + self.event.barbarians:
                if rect.colliderect(ob.innerrect) and ob != self:
                    self.x -= x
            self.y += y
            rect = self.surf.get_rect(center=(self.x, self.y))
            for ob in self.event.server.obs + self.event.barbarians:
                if rect.colliderect(ob.innerrect) and ob != self:
                    self.y -= y
            self.hurt = 10
            self.rect = self.surf.get_rect(center=(self.x, self.y))

            self.health -= damage - 4
            if self.health <= 0:
                self.health = 0
                if self in self.event.barbarians:
                    self.event.barbarians.remove(self)
                for p in self.event.server.players:
                    if not p.pending:
                        p.message = 'A Barbarian Swordsman has been defeated!'
                        p.message_color = (255,205,0)
                        p.message_count = 160
                attacker.gold += self.gold
                attacker.food += self.food
            





















            

