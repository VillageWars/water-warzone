import pygame
import random as r
import toolbox as t
from balloon import Arrow
from animations import *

class Farmer(pygame.sprite.Sprite):
    def __init__(self, building):
        try:
            pygame.sprite.Sprite.__init__(self, self.gp)
        except:
            pass
        self.building = building
        self.x, self.y = building.rect.x, building.rect.y
        self.setout()
        self.speed = 2
        self.obs = []
        self.food = 0

        self.rect = None


    @property
    def innerrect(self):
        return self.rect

    def setout(self):
        self.status = 'Going to Farms'
        sm_dist = 8000
        x = y = 0
        for farm in self.building.server.resources:
            if farm.__class__.__name__ == 'Farm':
                dx, dy = r.randint(farm.x + 90, farm.x + 310), farm.y + 50
                dist = t.getDist(self.x, self.y, dx, dy)
                if dist < sm_dist:
                    sm_dist = dist
                    x, y = dx, dy
                    self.farm = farm
        self.dest_x = x
        self.dest_y = y
        self.angle = t.getAngle(self.x, self.y, x, y)

    def start_gather(self):
        self.status = 'Gathering Food'
        sm_dist = 1000
        for food in self.farm.foods:
            if food.image == 'good':
                dist = t.getDist(self.x, self.y, food.x, food.y)
                if dist < sm_dist:
                    sm_dist = dist
                    self.the_food = food
                    self.dest_x = food.x
                    self.dest_y = food.y

    def mine(self):
        try:
            self.the_food.mine(self)
            if self.the_food.image == 'used':
                self.start_gather()
        except:
            self.start_gather()

    def at_dest(self):
        return t.getDist(self.x, self.y, self.dest_x, self.dest_y) < 10

    def go_back(self):
        self.status = 'Returning to Guild'
        self.dest_x, self.dest_y = self.building.rect.center

    def update(self):

        
        self.obs = self.building.server.obs
        
        self.angle = t.getAngle(self.x, self.y, self.dest_x, self.dest_y)
        x, y = t.getDir(self.angle, self.speed)
        
        lx, ly = self.x, self.y
        if self.status != 'Gathering Food':
            self.x += x
            self.rect = pygame.Rect(self.x, self.y, 50, 50)
            for ob in self.obs:
                if self.rect.colliderect(ob.innerrect) and (ob.__class__.__name__ != 'Gate' or ob.owner.channel != self.building.owner):
                    self.x -= x
            
            self.y += y
            self.rect = pygame.Rect(self.x, self.y, 50, 50)
            for ob in self.obs:
                if self.rect.colliderect(ob.innerrect) and (ob.__class__.__name__ != 'Gate' or ob.owner.channel != self.building.owner):
                    self.y -= y
            if round(lx) == round(self.x) and round(ly) == round(self.y) and self.status != 'Gathering Food':
                blocked = True
                while blocked:
                    blocked = False
                    
                    self.x += x
                    self.rect = pygame.Rect(self.x, self.y, 50, 50)
                    for ob in self.obs:
                        if self.rect.colliderect(ob.innerrect):
                            blocked = True
            
                    self.y += y
                    self.rect = pygame.Rect(self.x, self.y, 50, 50)
                    for ob in self.obs:
                        if self.rect.colliderect(ob.innerrect):
                            blocked = True
                

        if self.status == 'Gathering Food':
            if self.food < 20:
                self.mine()
            else:
                self.go_back()
            

        if self.at_dest():
            if self.status == 'Going to Farms':
                self.start_gather()
            elif self.status == 'Returning to Guild':
                self.food = 0
                self.building.owner.character.food += 20
                self.setout()
        
        for p in self.building.server.players:
            if not p.pending:
                screen = pygame.Rect(0, 0, 1000, 650)
                rect = pygame.Rect(0, 0, 1, 1)
                rect.size = self.rect.size
                rect.topleft = (p.character.get_x(self.rect), p.character.get_y(self.rect))
                if screen.colliderect(rect):
                    if self.status == 'Gathering Food':
                        p.to_send.append({'action':'draw_NPC',
                            'coords':(p.character.get_x(self), p.character.get_y(self)),
                            'image':'farmer',
                            'status':'Gathering Food : ' + str(self.food) + '/20',
                            'color':self.building.owner.color,
                            'angle':self.angle})
                    else:
                        p.to_send.append({'action':'draw_NPC',
                            'coords':(p.character.get_x(self), p.character.get_y(self)),
                            'image':'farmer',
                            'status':self.status,
                            'color':self.building.owner.color,
                            'angle':self.angle})
    def explode(self, angle, knockback):
        x, y = t.getDir(angle, knockback)
        self.x += x
        self.rect = pygame.Rect(self.x, self.y, 50, 50)
        for ob in self.obs:
            if self.rect.colliderect(ob.innerrect) and (ob.__class__.__name__ != 'Gate' or ob.owner.channel != self.building.owner):
                self.x -= x
            
        self.y += y
        self.rect = pygame.Rect(self.x, self.y, 50, 50)
        for ob in self.obs:
            if self.rect.colliderect(ob.innerrect) and (ob.__class__.__name__ != 'Gate' or ob.owner.channel != self.building.owner):
                self.y -= y


class Miner(pygame.sprite.Sprite):
    def __init__(self, building):
        try:
            pygame.sprite.Sprite.__init__(self, self.gp)
        except:
            pass
        self.building = building
        self.x, self.y = building.rect.x, building.rect.y
        self.setout()
        self.speed = 2
        self.gold = 0
        self.obs = []

    @property
    def innerrect(self):
        return self.rect        

    def setout(self):
        self.status = 'Heading to Mines'
        sm_dist = 8000
        x = y = 0
        for farm in self.building.server.resources:
            if farm.__class__.__name__ == 'Mine':
                dx, dy = farm.x+100, r.randint(farm.y + 50, farm.y + 400)
                dist = t.getDist(self.x, self.y, dx, dy)
                if dist < sm_dist:
                    sm_dist = dist
                    x, y = dx, dy
                    self.farm = farm
        self.dest_x = x
        self.dest_y = y
        self.angle = t.getAngle(self.x, self.y, x, y)

    def start_gather(self):
        self.status = 'Mining'
        sm_dist = 1000
        for food in self.farm.golds:
            if food.image == 'good':
                dist = t.getDist(self.x, self.y, food.x, food.y)
                if dist < sm_dist:
                    sm_dist = dist
                    self.the_food = food
                    self.dest_x = food.x
                    self.dest_y = food.y

    def mine(self):
        try:
            self.the_food.collect(self)
            if self.the_food.image == 'used':
                self.start_gather()
        except:
            self.start_gather()

    def at_dest(self):
        return t.getDist(self.x, self.y, self.dest_x, self.dest_y) < 10

    def go_back(self):
        self.status = 'Returning to Guild'
        self.dest_x, self.dest_y = self.building.rect.center

    def update(self):
        self.obs = self.building.server.obs
        self.angle = t.getAngle(self.x, self.y, self.dest_x, self.dest_y)
        x, y = t.getDir(self.angle, self.speed)
        
        lx, ly = self.x, self.y
        if self.status != 'Mining':
            self.x += x
            self.rect = pygame.Rect(self.x, self.y, 50, 50)
            for ob in self.obs:
                if self.rect.colliderect(ob.innerrect) and (ob.__class__.__name__ != 'Gate' or ob.owner.channel != self.building.owner):
                    self.x -= x
            
            self.y += y
            self.rect = pygame.Rect(self.x, self.y, 50, 50)
            for ob in self.obs:
                if self.rect.colliderect(ob.innerrect) and (ob.__class__.__name__ != 'Gate' or ob.owner.channel != self.building.owner):
                    self.y -= y
            if round(lx) == round(self.x) and round(ly) == round(self.y) and self.status != 'Mining':
                blocked = True
                while blocked:
                    blocked = False
                    
                    self.x += x
                    self.rect = pygame.Rect(self.x, self.y, 50, 50)
                    for ob in self.obs:
                        if self.rect.colliderect(ob.innerrect):
                            blocked = True
            
                    self.y += y
                    self.rect = pygame.Rect(self.x, self.y, 50, 50)
                    for ob in self.obs:
                        if self.rect.colliderect(ob.innerrect):
                            blocked = True
                

        if self.status == 'Mining':
            if self.gold < 20:
                self.mine()
            else:
                self.go_back()
            

        if self.at_dest():
            if self.status == 'Heading to Mines':
                self.start_gather()
            elif self.status == 'Returning to Guild':
                self.gold = 0
                self.building.owner.character.gold += 20
                self.setout()
        
        for p in self.building.server.players:
            if not p.pending:
                screen = pygame.Rect(0, 0, 1000, 650)
                rect = pygame.Rect(0, 0, 1, 1)
                rect.size = self.rect.size
                rect.topleft = (p.character.get_x(self.rect), p.character.get_y(self.rect))
                if screen.colliderect(rect):
                    if self.status == 'Mining':
                        p.to_send.append({'action':'draw_NPC',
                            'coords':(p.character.get_x(self), p.character.get_y(self)),
                            'image':'miner',
                            'status':'Mining : ' + str(self.gold) + '/20',
                            'color':self.building.owner.color,
                            'angle':self.angle})
                    else:
                        p.to_send.append({'action':'draw_NPC',
                            'coords':(p.character.get_x(self), p.character.get_y(self)),
                            'image':'miner',
                            'status':self.status,
                            'color':self.building.owner.color,
                            'angle':self.angle})
                        
    def explode(self, angle, knockback):
        x, y = t.getDir(angle, knockback)
        self.x += x
        self.rect = pygame.Rect(self.x, self.y, 50, 50)
        for ob in self.obs:
            if self.rect.colliderect(ob.innerrect) and (ob.__class__.__name__ != 'Gate' or ob.owner.channel != self.building.owner):
                self.x -= x
            
        self.y += y
        self.rect = pygame.Rect(self.x, self.y, 50, 50)
        for ob in self.obs:
            if self.rect.colliderect(ob.innerrect) and (ob.__class__.__name__ != 'Gate' or ob.owner.channel != self.building.owner):
                self.y -= y


class ArcheryTower(pygame.sprite.Sprite):
    dimensions = (360, 360)
    def __init__(self, server, x, y, channel, rect):
        pygame.sprite.Sprite.__init__(self, self.gp)
        self.building = self
        
        self.server = server
        self.x, self.y = x, y - 100
        self.owner = channel.character
        self.health = 300
        self.dimensions = (360, 360)
        
        self.innerrect = rect
        self.server.building_blocks.append(self.innerrect)
        self.server.obs.append(self)

        self.balloon_speed = 45
        self.attack = 24
        self.knockback = 32

        self.shoot_cooldown = 60
        self.state = 'alive'

        self.attacking = False

    def update(self):
        self.lookx = self.owner.x
        self.looky = self.owner.y
        self.attacking = False

        for npc in self.server.event.NPCs:
            if t.getDist(self.x, self.y, npc.x, npc.y) < 800:
                    self.lookx = npc.x
                    self.looky = npc.y
                    self.attacking = True

                    
        for player in self.server.players:
            if not player.pending:
                if t.getDist(self.x, self.y, player.character.x, player.character.y) < 800 and player != self.owner.channel and player.character.dead == False:
                    self.lookx = player.character.x
                    self.looky = player.character.y
                    self.attacking = True

        
                
        if self.attacking == False:
            close_dist = 100000
            
            for robot in self.server.NPCs:
                if robot.__class__.__name__ == 'Robot' and robot.factory.owner != self.owner.channel and t.getDist(self.x, self.y, robot.x, robot.y) < close_dist:
                    self.lookx = robot.x
                    self.looky = robot.y
                    close_dist = t.getDist(self.x, self.y, robot.x, robot.y)
                    self.attacking = True

        self.angle = t.getAngle(self.x, self.y, self.lookx, self.looky)
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        if self.shoot_cooldown < 1 and self.attacking and self.state == 'alive':
            Arrow(tower=self)
            self.shoot_cooldown = 60


        for p in self.server.players:
            if not p.pending:
                p.to_send.append({'action':'archery_tower',
                    'coords':(p.character.get_x(self), p.character.get_y(self)),
                    'angle':self.angle,
                    'color':self.owner.channel.color,
                    'health':self.health,
                    'state':self.state})


    def isBuilding(self):
        return False
    
    def getHurt(self, damage, attacker):
        if attacker != self.owner:
            self.health -= damage
            if self.health < 1:
                self.state = 'broken'
                if attacker.__class__.__name__ == 'Character':
                    attacker.destroyed += 1
                    self.owner.channel.message = attacker.channel.username + ' has broken one of your Archery Towers.'
                else:
                    self.owner.channel.message = attacker + ' has broken one of your Archery Towers.'
                    
                self.owner.channel.message_count = 150
                self.owner.channel.message_color = (255,0,0)
                self.server.obs.remove(self)

    def explode(self, player):
        if self.state == 'broken':
            self.server.building_blocks.remove(self.innerrect)
            self.kill()
        else:
            self.getHurt(80, player)
            if self.state == 'broken':
                self.server.building_blocks.remove(self.innerrect)
                self.kill()





class Robot(pygame.sprite.Sprite):
    def __init__(self, factory):
        try:
            pygame.sprite.Sprite.__init__(self, self.gp)
        except:
            pass

        self.server = factory.server
        self.factory = factory
        self.player = factory.owner.character
        self.angle = r.randint(0, 359)

        self.x = self.factory.x
        self.y = self.factory.y + 140
        
        self.fav_dir = r.choice((5, -5))
        self.angry_test = 20
        self.regular_test = 2
        self.angry = False

        self.speed = 4
        self.health = 100
        self.hurt = 0

        self.dead = 0

        self.obs = []

        self.state = 'Peaceful'
        self.surf = pygame.Surface((50, 50))
        self.rect = self.surf.get_rect(center=(self.x, self.y))

        self.safety_zone = pygame.Surface((3400, 2190)).get_rect(center=(self.factory.x, self.factory.y))

        self.range = pygame.Surface((3000, 2000)).get_rect(center=(self.factory.x, self.factory.y))

    @property
    def innerrect(self):
        return self.rect

    @property
    def building(self):
        return self.factory


        

    def update(self):
        rect = self.surf.get_rect(center=(self.x, self.y))
        for ob in self.obs:
            if rect.colliderect(ob.innerrect) and (ob.__class__.__name__ != 'Gate' or ob.owner.channel != self.factory.owner):
                self.getHurt(100, 0, 0)

        
        self.obs = self.server.obs
        for robot in self.server.NPCs:
            if robot.__class__.__name__ == 'Robot' and robot.factory.owner != self.factory.owner:
                self.obs.append(robot)

        if self.hurt:
            self.hurt -= 1

        if self.dead:
            self.dead -= 1

        if not self.dead:
            self.AI()

            for p in self.server.players:
                if not p.pending:
                    screen = pygame.Rect(0, 0, 1000, 650)
                    rect = pygame.Rect(0, 0, 1, 1)
                    rect.size = self.rect.size
                    rect.topleft = (p.character.get_x(self.rect), p.character.get_y(self.rect))
                    if screen.colliderect(rect):
                        p.to_send.append({'action':'draw_robot',
                                'coords':(p.character.get_x(self), p.character.get_y(self)),
                                'name':'Robot',
                                'health':self.health,
                                'image':('hurt' if self.hurt else 'regular'),
                                'color':self.factory.owner.color,
                                'angle':self.angle})


            for p in self.server.players:
                if not p.pending and self.rect.colliderect(p.character.rect) and p != self.factory.owner and p.character.dead == False:
                    self.getHurt(0, self.angle + 180, 50)
                    p.character.getHurt(10, self.factory.owner.username + "'s Robots", self.angle, 2)


    def AI(self):

        if not self.rect.colliderect(self.safety_zone):
            self.state = 'Returning'
            self.angle = t.getAngle(self.x, self.y, self.factory.x, self.factory.y + 140)
        
        if self.state == 'Returning':
            if round(self.x) == round(self.factory.x) and round(self.y) == round(self.factory.y):
                self.state = 'Peaceful'

        if self.state == 'Attacking':
            speed = self.speed
        else:
            speed = 2


        origx = self.x

        
        x, y = t.getDir(self.angle, total=speed)

        self.x += x
        rect = self.surf.get_rect(center=(self.x, self.y))
        for ob in self.obs:
            if rect.colliderect(ob.innerrect) and (ob.__class__.__name__ != 'Gate' or ob.owner.channel != self.factory.owner):
                self.x -= x

        origy = self.y
            
        self.y += y
        rect = self.surf.get_rect(center=(self.x, self.y))
        for ob in self.obs:
            if rect.colliderect(ob.innerrect) and (ob.__class__.__name__ != 'Gate' or ob.owner.channel != self.factory.owner):
                self.y -= y

        for item in self.server.bushes:
            if self.rect.colliderect(item.innerrect):
                if item.__class__.__name__ == 'SpikyBush':
                    self.getHurt(1, self.angle + 180, 1.5)
                else:
                    self.getHurt(0, self.angle + 180, 1.5)
            
        self.rect = self.surf.get_rect(center=(self.x, self.y))

        suspects = []
        for p in self.server.players:
            if not p.pending:
                if p.character.rect.colliderect(self.range) and not p.character.dead and not p == self.factory.owner:
                    suspects.append(p.character)
        if len(suspects) > 1:
            closest = suspects[0]
            for suspect in suspects[1:]:
                if t.getDist(self.x, self.y, suspect.x, suspect.y) < t.getDist(self.x, self.y, closest.x, closest.y):
                    closest = suspect
                    suspect = closest
        elif len(suspects) == 1:
            suspect = suspects[0]

        else:
            suspect = None

        if suspect != None:
            self.state = 'Attacking'
            self.attacking = suspect
            self.angle = t.getAngle(self.x, self.y, self.attacking.x, self.attacking.y) + r.randint(-2,2)


    def init(self):

        self.x = self.factory.x
        self.y = self.factory.y + 140

        self.state = 'Peaceful'
        
        self.health = 100

    def getHurt(self, damage, angle, knockback):

        self.health -= damage
        if self.health <= 0:
            Explosion(self)
            self.dead = 200
            for p in self.server.players:
                if not p.pending:
                    screen = pygame.Rect(0, 0, 1000, 650)
                    screen.center = p.character.rect.center
                    if screen.colliderect(self.rect):
                        p.to_send.append({'action':'sound', 'sound':'die'})

            self.init()

        if damage != 0:
            self.hurt = 8
        
        x, y = t.getDir(angle, knockback)

        self.x += x
        rect = self.surf.get_rect(center=(self.x, self.y))
        for ob in self.obs:
            if rect.colliderect(ob.innerrect):
                self.x -= x


        
        self.y += y
        rect = self.surf.get_rect(center=(self.x, self.y))
        for ob in self.obs:
            if rect.colliderect(ob.innerrect):
                self.y -= y

    def explode(self, angle, knockback):
        self.getHurt(80, angle, knockback)

















    

                
        
