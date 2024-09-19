import pygame
import toolbox as t
from animations import *
import random as r

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, server, x, y):
        pygame.sprite.Sprite.__init__(self, self.gp)
        self.server = server
        self.image = None
        self.dimentions = (50, 50)
        self.x = x
        self.y = y
        self.max_health = self.health = 300
        self.owner = None

    def update(self):
        

        for p in self.server.players:
            if not p.pending:
                screen = pygame.Rect(0, 0, 1000, 650)
                rect = pygame.Rect(0, 0, 1, 1)
                rect.size = self.innerrect.size
                rect.topleft = (p.character.get_x(self.innerrect), p.character.get_y(self.innerrect))
                if screen.colliderect(rect):
                    p.to_send.append({'action':'draw_obstacle',
                            'image':self.image,
                            'coords':(p.character.get_x(self), p.character.get_y(self)),
                            'health':self.health,
                            'max_health':self.max_health})

    def getHurt(self, damage, attacker):
        if self.health > 0:
            self.health -= damage
            if self.health < 1:
                self.server.building_blocks.remove(self.innerrect)
                self.server.obs.remove(self)
                self.kill()

    def isBuilding(self):
        return False


    def explode(self):
        self.getHurt(80, None)


class Tree(pygame.sprite.Sprite):
    def __init__(self, server, x, y):
        pygame.sprite.Sprite.__init__(self, self.gp)
        self.server = server
        self.image = None
        self.x = x
        self.y = y
        self.max_health = self.health = 300
        self.owner = None
        self.surf = pygame.Surface((200, 280))
        self.rect = self.surf.get_rect(center=(x,y))
        self.innerrect = pygame.Surface((50, 120)).get_rect(midtop=self.rect.center)
        
        server.building_blocks.append(self.innerrect)
        server.obs.append(self)

    def update(self):
        

        for p in self.server.players:
            if not p.pending:
                screen = pygame.Rect(0, 0, 1000, 650)
                rect = pygame.Rect(0, 0, 1, 1)
                rect.size = self.rect.size
                rect.center = (p.character.get_x(self), p.character.get_y(self))
                if screen.colliderect(rect):
                    p.to_send.append({'action':'draw_obstacle',
                            'image':'tree',
                            'coords':(p.character.get_x(self), p.character.get_y(self)),
                            'health':self.health,
                            'max_health':self.max_health})

    def getHurt(self, damage, attacker):
        if self.health > 0:
            self.health -= damage
            if self.health < 1:
                self.server.building_blocks.remove(self.innerrect)
                self.server.obs.remove(self)
                self.kill()

    def isBuilding(self):
        return False


    def explode(self):
        self.getHurt(160, None)


class Sappling(pygame.sprite.Sprite):
    def __init__(self, server, x, y):
        pygame.sprite.Sprite.__init__(self, Tree.gp)
        self.server = server
        self.x = x
        self.count = 100 #30*60*1
        self.y = y
        self.max_health = self.health = 120
        self.owner = None
        self.surf = pygame.Surface((60, 90))
        self.rect = self.surf.get_rect(center=(x,y))
        
        server.building_blocks.append(self.rect)

    def update(self):
        self.count -= 1
        if not self.count:
            self.server.building_blocks.remove(self.rect)
            Tree(self.server, self.x, self.y)
            self.kill()
            return

        for p in self.server.players:
            if not p.pending:
                screen = pygame.Rect(0, 0, 1000, 650)
                rect = pygame.Rect(0, 0, 1, 1)
                rect.size = self.rect.size
                rect.center = (p.character.get_x(self), p.character.get_y(self))
                if screen.colliderect(rect):
                    p.to_send.append({'action':'draw_obstacle',
                            'image':'sappling',
                            'coords':(p.character.get_x(self), p.character.get_y(self)),
                            'health':self.health,
                            'max_health':self.max_health})

    def getHurt(self, damage, attacker):
        if self.health > 0:
            self.health -= damage
            if self.health < 1:
                self.server.building_blocks.remove(self.innerrect)
                self.server.obs.remove(self)
                self.kill()

    def isBuilding(self):
        return False


    def explode(self):
        self.getHurt(120, None)


        

class Boulder(Obstacle):
    def __init__(self, server, x, y):
        Obstacle.__init__(self, server, x, y)
        self.image = 'boulder'
        self.max_health = self.health = r.randint(18, 32) * 10
        self.p = pygame.image.load('../assets/boulder.png')
        self.innerrect = self.p.get_rect(center=(x,y))
        server.building_blocks.append(self.innerrect)
        server.obs.append(self)


class Crate(Obstacle):
    def __init__(self, player, x, y):
        Obstacle.__init__(self, player.channel.server, x, y)
        self.image = 'crate'
        self.max_health = self.health = 800
        self.p = pygame.Surface((50, 50))
        self.innerrect = self.p.get_rect(center=(x,y))
        self.server.building_blocks.append(self.innerrect)
        self.server.obs.append(self)
        self.owner = player

    def explode(self):
        self.server.building_blocks.remove(self.innerrect)
        self.server.obs.remove(self)
        self.kill()

    def update(self):
        
        

        for p in self.server.players:
            
            if not p.pending:
                screen = pygame.Rect(0, 0, 1000, 650)
                rect = pygame.Rect(0, 0, 1, 1)
                rect.size = self.innerrect.size
                rect.topleft = (p.character.get_x(self.innerrect), p.character.get_y(self.innerrect))
                if screen.colliderect(rect):

                    p.to_send.append({'action':'draw_obstacle',
                                'image':self.image,
                                'coords':(p.character.get_x(self), p.character.get_y(self)),
                                'health':self.health,
                                'max_health':self.max_health})

class Barrel(Obstacle):
    def __init__(self, player, x, y, angle, health=15, max_health=15, explosive=False):
        Obstacle.__init__(self, player.channel.server, x, y)
        self.image = 'barrel'
        self.explosive = explosive
        self.max_health = max_health
        self.health = health
        self.p = pygame.Surface((50, 50))
        self.innerrect = self.p.get_rect(center=(x,y))
        
        self.player = player
        self.obs = self.player.channel.server.obs
        self.angle = angle
        self.speed = 16
        self.sedentary = False
        self.roll_angle = angle 
        self.damage = self.health
        self.knockback = 80

        if -90 <= angle <= 90:
            self.roll_direction = -10
        else:
            self.roll_direction = 10

        

    def explode(self):
        if self.innerrect in self.server.building_blocks:
            self.server.building_blocks.remove(self.innerrect)
            self.server.obs.remove(self)
        self.kill()

    def update(self):
        
        self.damage = self.health
        if not self.sedentary:
            self.roll_angle += self.roll_direction
            self.move(self.angle)
        

        for p in self.server.players:
            if not p.pending:
                screen = pygame.Rect(0, 0, 1000, 650)
                rect = pygame.Rect(0, 0, 1, 1)
                rect.size = self.innerrect.size
                rect.topleft = (p.character.get_x(self), p.character.get_y(self))
                if screen.colliderect(rect):

                    p.to_send.append({'action':'draw_obstacle',
                            'image':self.image,
                            'coords':(p.character.get_x(self), p.character.get_y(self)),
                            'health':self.health,
                            'max_health':self.max_health,
                            'angle':self.roll_angle,
                            'explosive':self.explosive})
    def sedent(self):
        if self.explosive:
            self.this_explode()
            self.kill()
            return
        self.sedentary = True
        self.server.building_blocks.append(self.innerrect)
        self.server.obs.append(self)
        self.getHurt(10, 'Santa Clause') # Placeholder
        for p in self.server.players:
            if not p.pending:
                screen = pygame.Rect(0, 0, 1000, 650)
                rect = pygame.Rect(0, 0, 1, 1)
                rect.size = self.innerrect.size
                rect.topleft = (p.character.get_x(self), p.character.get_y(self))
                if screen.colliderect(rect):
                    p.to_send.append({'action':'sound','sound':'barrel'})

    def this_explode(self): # warning: self may be player object
        BAM(self)
        try:
            self.server
        except:
            self.server = self.channel.server
            self.innerrect = self.rect
            self.player = self
        for p in self.server.players:
            screen = pygame.Rect(0, 0, 1000, 650)
            screen.center = p.character.rect.center
            if screen.colliderect(self.innerrect):
                p.Send({'action':'sound', 'sound':'TNT'})

        if True:  # Too lazy to unindent
            ray = pygame.Rect(0, 0, 350, 350)
            ray.center = self.x, self.y
            for item in self.server.obstacles:
                if item != self and item.innerrect.colliderect(ray):
                    item.explode()
            for item in self.server.trees:
                if item != self and item.innerrect.colliderect(ray):
                    item.explode()
            for item in self.server.buildings:
                if item.innerrect.colliderect(ray):
                    item.getHurt(120, self.player)
                elif item.rect.colliderect(ray):
                    item.getHurt(120, self.player)
            print('Explosion')
            for item in self.server.players:
                print(item.username)
                if item.character.rect.colliderect(ray):
                    print(item.username.upper())
                    item.character.getHurt(80, self.player, t.getAngle(self.x, self.y, item.character.x, item.character.y), 120, '<Victim> was blown up by <Attacker>')
                    
            for item in self.server.NPCs:
                if item.innerrect.colliderect(ray):
                    if item.__class__.__name__ == 'ArcheryTower':
                        item.explode(self.player)
                    else:
                        item.explode(t.getAngle(self.x, self.y, item.x, item.y), 80)
            for item in self.server.event.NPCs:
                if item.rect.colliderect(ray):
                    item.explode(self.player, self)
            for item in self.server.bushes:
                if item.rect.colliderect(ray):
                    item.explode()
        if self.player == self:
            del self.server
            del self.innerrect
            del self.player
        
                    
    def move(self, angle):
        obs = self.obs[:]

        x, y = t.getDir(angle, self.speed)
        self.move_x(round(x), obs)
        self.move_y(round(y), obs)
        for item in obs:
            rect = item.innerrect if hasattr(item, 'innerrect') else item.rect
            if self.innerrect.colliderect(rect):
                try:
                    item.getHurt(self.damage, self.player)
                except:
                    item.getHurt(self.damage, self.player, self.angle, self.knockback)
                self.sedent()
                return
        for p in self.server.players:
            if self.innerrect.colliderect(p.character.rect) and p.character != self.player:
                self.sedent()
                p.character.getHurt(self.damage, self.player, self.angle, self.knockback, msg='<Victim> got rolled over.')
                return
        for b in self.server.bushes:
            if self.innerrect.colliderect(b.rect):
                self.sedent()
                b.getHurt(self.damage, self.player)
                return
        for npc in self.server.NPCs:
            if npc.__class__.__name__ == 'Robot' and self.innerrect.colliderect(npc.rect):
                self.sedent()
                npc.getHurt(self.damage, self.angle, self.knockback)
                return
            if npc.__class__.__name__ == 'ArcheryTower' and self.innerrect.colliderect(npc.innerrect):
                self.sedent()
                npc.getHurt(self.damage, self.angle, self.knockback)
                return
        for npc in self.server.event.NPCs:
            if self.innerrect.colliderect(npc.rect):
                self.sedent()
                result = npc.getHurt(self.player, self.damage, self.angle, self.knockback)
        
        

    def move_x(self, a, obs):
        self.innerrect.x += a
        self.x, self.y = self.innerrect.center
        
                
    def move_y(self, a, obs):
        self.innerrect.y += a
        self.x, self.y = self.innerrect.center
    


class Vine(Obstacle):
    def __init__(self, player, x, y, direction=None, speed=r.randint(25, 110)):
        Obstacle.__init__(self, player.channel.server, x, y)
        self.image = 'vine'
        self.max_health = self.health = speed * 2
        self.p = pygame.Surface((50, 50))
        self.innerrect = self.p.get_rect(center=(x,y))
        self.server.building_blocks.append(self.innerrect)
        self.server.obs.append(self)
        self.owner = player
        self.speed = speed
        self.count = self.speed

        
        dirs = [(0, 50), (50, 0), (-50, 0), (0, -50)]
        if direction:
            dirs.remove(direction)
        self.dir = r.choice(dirs)
        for v in self.server.obstacles:
            if v.__class__ == Vine and self.innerrect.colliderect(v.innerrect) and v != self:
                v.count = 1
                v.health = v.max_health
                v.dir = self.dir
                v.owner = self.owner
                self.explode()

    def explode(self):
        if self.innerrect in self.server.building_blocks:
            self.server.building_blocks.remove(self.innerrect)
        if self in self.server.obs:
            self.server.obs.remove(self)
        self.kill()

    def update(self):
        if self.count:
            self.count -= 1
            if not self.count:
                Vine(self.owner, self.x + self.dir[0], self.y + self.dir[1], direction=self.dir, speed=self.speed)
        

        for b in self.server.buildings:
            if not b.owner == self.owner.channel and self.innerrect.colliderect(b.innerrect):
                b.getHurt(0.02, self.owner.channel.username + '\'s invasive vine')
        
        for p in self.server.players:
            if not p.pending:
                p.to_send.append({'action':'draw_obstacle',
                            'image':self.image,
                            'coords':(p.character.get_x(self), p.character.get_y(self)),
                            'health':self.health,
                            'max_health':self.max_health})


class SpikyBush(pygame.sprite.Sprite):
    def __init__(self, player, x, y):
        pygame.sprite.Sprite.__init__(self, self.gp)
        self.server = player.channel.server
        self.x = x
        self.y = y
        self.dimensions = (50, 50)
        self.max_health = self.health = 260
        self.p = pygame.Surface(self.dimensions)
        self.rect = self.p.get_rect(center=(x,y))
        self.server.building_blocks.append(self.innerrect)
        self.owner = player

    @property
    def innerrect(self):
        return self.rect

    def explode(self):
        self.server.building_blocks.remove(self.innerrect)
        self.kill()

    def update(self):
        
        

        for p in self.server.players:
            if not p.pending:
                p.to_send.append({'action':'draw_obstacle',
                            'image':'spiky bush',
                            'coords':(p.character.get_x(self), p.character.get_y(self)),
                            'health':self.health,
                            'max_health':self.max_health})

    def getHurt(self, damage, attacker):
        if self.health > 0:
            self.health -= damage
            if self.health < 1:
                self.explode()

    def isBuilding(self):
        return False

class Gate(Obstacle):
    def __init__(self, player, x, y, rot):
        Obstacle.__init__(self, player.channel.server, x, y)
        self.image = 'gate'
        self.max_health = self.health = 1000
        if rot == False:
            self.p = pygame.Surface((100, 200))
        else:
            self.p = pygame.Surface((200, 100))
        self.innerrect = self.p.get_rect(center=(x,y))
        self.server.building_blocks.append(self.innerrect)
        self.server.obs.append(self)
        self.owner = player
        self.rotated = rot

    def explode(self):
        self.getHurt(900, None)

    def update(self):

        

        for p in self.server.players:
            if not p.pending:
                p.to_send.append({'action':'draw_obstacle',
                            'image':self.image,
                            'coords':(p.character.get_x(self), p.character.get_y(self)),
                            'health':self.health,
                            'max_health':self.max_health,
                            'rotated?':self.rotated})

class TNT(pygame.sprite.Sprite):
    def __init__(self, player, x, y):
        pygame.sprite.Sprite.__init__(self, self.gp)
        self.health = 130
        self.x = x
        self.y = y
        self.p = pygame.Surface((50, 50))
        self.innerrect = self.p.get_rect(center=(x,y))
        self.server = player.channel.server
        self.server.building_blocks.append(self.innerrect)
        self.server.obs.append(self)
        self.owner = player
        #player.channel.achievement('You used TNT! (Watch out)')

    def update(self):
        self.health -= 1
        if self.health == 0:
            BAM(self)
            for p in self.server.players:
                screen = pygame.Rect(0, 0, 1000, 650)
                screen.center = p.character.rect.center
                if screen.colliderect(self.innerrect):
                    p.Send({'action':'sound', 'sound':'TNT'})
            self.server.building_blocks.remove(self.innerrect)
            self.server.obs.remove(self)
            
            ray = pygame.Rect(0, 0, 400, 400)
            ray.center = self.x, self.y
            for item in self.server.obstacles:
                if item != self and item.innerrect.colliderect(ray):
                    item.explode()
            for item in self.server.trees:
                if item != self and item.innerrect.colliderect(ray):
                    item.explode()
            for item in self.server.buildings:
                if item.innerrect.colliderect(ray):
                    item.getHurt(120, self.owner)
                elif item.rect.colliderect(ray):
                    item.getHurt(120, self.owner)
            for item in self.server.players:
                if item.character.rect.colliderect(ray):
                    item.character.getHurt(80, self.owner, t.getAngle(self.x, self.y, item.character.x, item.character.y), 120, '<Victim> was blown up by <Attacker>')
            for item in self.server.NPCs:
                if item.innerrect.colliderect(ray):
                    if item.__class__.__name__ == 'ArcheryTower':
                        item.explode(self.owner)
                    else:
                        item.explode(t.getAngle(self.x, self.y, item.x, item.y), 80)
            for item in self.server.event.NPCs:
                if item.rect.colliderect(ray):
                    item.explode(self.owner, self)

            for item in self.server.bushes:
                if item.rect.colliderect(ray):
                    item.explode()
                
            self.kill()

        for p in self.server.players:
            if not p.pending:
                p.to_send.append({'action':'draw_obstacle',
                            'image':'TNT',
                            'coords':(p.character.get_x(self), p.character.get_y(self))})
    def isBuilding(self):
        return False
    def getHurt(self, damage, attacker):
        pass
    def explode(self):
        ''' Ha! '''
        pass

class Block():
    def __init__(self, topleft, size):
        self.innerrect = pygame.Rect(topleft[0], topleft[1], size[0], size[1])
        self.owner = None
    def isBuilding(self):
        return False
    def getHurt(self, damage, attacker):
        pass
        
        
        
