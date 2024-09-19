import pygame
import toolbox as t
from animations import *
import random as r


class Balloon(pygame.sprite.Sprite):
    def __init__(self, server, owner):
        pygame.sprite.Sprite.__init__(self, self.gp)
        self.server = server
        self.owner = owner
        self._owner = owner.channel.username
        self.speed = owner.balloon_speed
        self.x = owner.x
        self.y = owner.y
        self.angle = owner.angle
        self.damage = owner.attack
        self.knockback = owner.knockback

        self.image = pygame.image.load('../assets/balloon.png')
        self.type = ('normal' if self.damage < 20 else 'op')
        if self.owner.shot_speed < 8:
            self.type = ('speedy' if self.damage < 20 else 'speedy+op')


    def update(self):
        
        self.move()

        if self.alive():
            for p in self.server.players:
                if not p.pending:
                    p.to_send.append({'action':'draw_balloon',
                        'coords':(p.character.get_x(self), p.character.get_y(self)),
                        'angle':self.angle,
                        'type':self.type})

        self.test_collide()        

    def test_collide(self):
        result = False
        
        obstacles = self.server.obs

        if self.x > 7000 or self.x < -1000 or self.y > 4400 or self.y < -500:
            self.kill()
            return

        self.rect = self.image.get_rect(center=(self.x, self.y))

        for item in obstacles:
            if hasattr(item, 'image') and item.image == 'barrel' and not item.sedentary:
                continue
            try:
                if self.rect.colliderect(item.innerrect) and not (self.__class__ == Arrow  and item.__class__.__name__ == 'ArcheryTower') and not (self.__class__ == Arrow  and item.owner == self.owner):
                    try:
                        item.getHurt(self.damage, self.owner)
                    except:
                        item.getHurt(self.damage, self.owner, 0)
                    self.pop()
            except:
                pass
        for item in self.server.bushes:
            if self.rect.colliderect(item.innerrect) and not (self.__class__ == Arrow  and item.owner == self.owner):
                item.getHurt(self.damage, self.owner)
                self.pop()
                
                

                    
        for p in self.server.players:
            if not p.pending:
                if self.rect.colliderect(p.character.rect) and p != self.owner.channel and p.character.dead == False:
                    if self.__class__ == Arrow:
                        result = p.character.getHurt(self.damage, self._owner, self.angle, self.knockback, '<Victim> was shot by <Attacker>')
                    else:
                        result = p.character.getHurt(self.damage, self.owner, self.angle, self.knockback)
                    if result == 'repelled':
                        bb = type(self)(self.server, p.character)
                        bb.damage = self.owner.attack
                        bb.knockback = self.owner.knockback
                        bb.angle = self.angle + 180 + r.randint(-20, 20)
                        bb.speed = self.owner.balloon_speed
                        self.kill()
                        if hasattr(bb, 'bb'):
                            bb.bb.damage = self.owner.attack
                            bb.bb.knockback = self.owner.knockback
                            bb.bb.angle = self.angle + 180 + r.randint(-20, 20)
                            bb.bb.speed = self.owner.balloon_speed
                        return
                    else: 
                        self.pop()

                    
        for npc in self.server.NPCs:
            if npc.__class__.__name__ == 'Robot':
                if self.rect.colliderect(npc.rect) and not (self.owner == npc.player) and not npc.dead:
                    npc.getHurt(self.damage, self.angle, self.knockback)
                    self.pop()

        
        for npc in self.server.event.NPCs:
            if self.rect.colliderect(npc.rect):
                result = npc.getHurt(self.owner, self.damage, self.angle, self.knockback)
                if result and result[0] == 'repelled' and self.server.event.__class__.__name__ == 'BarbarianRaid':
                    BounceBalloon(self, result[1])
                    self.kill()
                else:
                    self.pop()   

    def move(self):
        dist = self.speed

        while dist > 16:

            x, y = t.getDir(self.angle, 16)
        
            self.x += x
            self.y += y

            dist -= 16
            
            self.test_collide()

            #print(self.alive())
            if not self.alive():
                return

        x, y = t.getDir(self.angle, dist)
        
        self.x += x
        self.y += y

    def pop(self):
        for p in self.server.players:
            if not p.pending:
                screen = pygame.Rect(0, 0, 1000, 650)
                screen.center = p.character.rect.center
                if screen.colliderect(self.rect):
                    if self.type == 'normal' or self.type == 'speedy':
                        p.to_send.append({'action':'sound', 'sound':'splash'})
                    elif self.type == 'op' or self.type == 'speedy+op':
                        p.to_send.append({'action':'sound', 'sound':'opsplash'})
                    
        Splash(self)
        self.kill()



class Arrow(Balloon):
    def __init__(self, server=None, tower=None):
        if tower.__class__.__name__ == 'Character':
            self.bb = Balloon(server=server, owner=tower)
            return None
        Balloon.__init__(self, tower.server, tower.owner)
        self.x = tower.innerrect.center[0]
        self.y = tower.innerrect.center[1]
        self.speed = tower.balloon_speed
        self.angle = tower.angle
        self.damage = tower.attack
        self.knockback = tower.knockback
        self._owner = tower.owner.channel.username + "'s Archery Tower"
        self.type = 'normal'

class Bolt(pygame.sprite.Sprite):
    def __init__(self, server=None, archer=None):
        pygame.sprite.Sprite.__init__(self, Balloon.gp)
        if archer.__class__.__name__ == 'Character':
            self.server = archer.channel.server
            self.speed = archer.balloon_speed
            self.x = archer.x
            self.y = archer.y
            self.angle = archer.angle
            self.damage = 10
            self.knockback = 50
            self.owner = archer
            self.archer = None
        else:
            self.server = archer.event.server
            self.speed = 17
            self.x = archer.x
            self.y = archer.y
            self.angle = archer.angle
            self.damage = 10
            self.knockback = 50
            self.owner = 'A Barbarian Archer'
            self.archer = archer

        self.image = pygame.image.load('../assets/balloon.png')


    def update(self):
        
        self.move()

        if self.alive():
            for p in self.server.players:
                if not p.pending:
                    p.to_send.append({'action':'draw_balloon',
                        'coords':(p.character.get_x(self), p.character.get_y(self)),
                        'angle':self.angle,
                        'type':'bolt'})

        self.test_collide()

    def test_collide(self):
        obstacles = self.server.obs
        
        if self.x > 7000 or self.x < -1000 or self.y > 4400 or self.y < -500:
            self.kill()
            return

        self.rect = self.image.get_rect(center=(self.x, self.y))

        for item in obstacles:
            if self.rect.colliderect(item.innerrect):
                item.getHurt(self.damage, self.owner)
                self.pop()
                
                
            elif item.isBuilding() and not (not self.archer and item.owner != self.owner.channel):
                if self.rect.colliderect(item.rect):
                    item.getHurt(self.damage, self.owner)
                    self.pop()

                    
        for p in self.server.players:
            if not (not self.archer and p.character == self.owner):  # If not the player shooting the bolt
                if not p.pending:
                    if self.rect.colliderect(p.character.rect) and p.character.dead == False:
                        if self.archer:
                            result = p.character.getHurt(self.damage, 'A Barbarian Archer', self.angle, self.knockback, msg='<Attacker> shot <Victim> and stole their gold and food.')
                            if p.character.dead and result != 'BAM':
                                self.archer.gold += p.character.gold
                                self.archer.food += p.character.food
                                p.character.gold = 0
                                p.character.food = 0

                            
                        else:
                            result = p.character.getHurt(self.damage, self.owner, self.angle, self.knockback, msg='<Attacker> shot <Victim> with a barbarian crossbow.')

                        if result == 'repelled':
                            bb = type(self)(archer=p.character)
                            bb.speed = 17
                            bb.damage = 10
                            bb.knockback = 50
                            bb.angle = self.angle + 180 + r.randint(-20, 20)
                            self.kill()
                            return
                        else: 
                            self.pop()

                    
        for npc in self.server.NPCs:
            if npc.__class__.__name__ == 'Robot' and not (self.archer and npc.player == self.owner):
                if self.rect.colliderect(npc.rect) and not npc.dead:
                    npc.getHurt(self.damage, self.angle, self.knockback)
                    self.pop()

        if self.server.event.__class__.__name__ != 'BarbarianRaid' or not self.archer:
            for npc in self.server.event.NPCs:
                if self.rect.colliderect(npc.rect):
                    npc.getHurt(self.owner, self.damage, self.angle, self.knockback)
                    self.pop()

    move = Balloon.move

    def pop(self):
        self.kill()

class BounceBalloon(pygame.sprite.Sprite):
    def __init__(self, old_self, angle):
        pygame.sprite.Sprite.__init__(self, Balloon.gp)
        self.server = old_self.server
        self.owner = 'A Barbarian'
        self.speed = old_self.speed
        self.x = old_self.x
        self.y = old_self.y
        self.angle = angle
        self.damage = old_self.damage
        self.knockback = old_self.knockback
        self.mock_owner = old_self.owner
        self.type = old_self.type

        self.image = pygame.image.load('../assets/balloon.png')


    def update(self):
        
        self.move()

        if self.alive():
            for p in self.server.players:
                if not p.pending:
                    p.to_send.append({'action':'draw_balloon',
                        'coords':(p.character.get_x(self), p.character.get_y(self)),
                        'angle':self.angle,
                        'type':self.type})

        self.test_collide()

        

    def test_collide(self):
        obstacles = self.server.obs

        if self.x > 7000 or self.x < -1000 or self.y > 4400 or self.y < -500:
            self.kill()
            return

        self.rect = self.image.get_rect(center=(self.x, self.y))

        for item in obstacles:
            if self.rect.colliderect(item.innerrect):
                item.getHurt(self.damage, self.owner)
                self.pop()
                
                
            elif item.isBuilding():
                if self.rect.colliderect(item.rect):
                    item.getHurt(self.damage, self.owner)
                    self.pop()

                    
                    
        for p in self.server.players:
            if not p.pending:
                if self.rect.colliderect(p.character.rect) and p.character.dead == False:
                    
                    result = p.character.getHurt(self.damage, self.owner, self.angle, self.knockback)

                    if result == 'repelled':
                        bb = Balloon(self.server, p.character)
                        bb.damage = self.damage
                        bb.knockback = self.knockback
                        bb.angle = self.angle + 180 + r.randint(-20, 20)
                        bb.speed = self.speed
                        self.kill()
                        return
                    else: 
                        self.pop()

                    
        for npc in self.server.NPCs:
            if npc.__class__.__name__ == 'Robot':
                if self.rect.colliderect(npc.rect) and not npc.dead:
                    npc.getHurt(self.damage, self.angle, self.knockback)
                    self.pop()

    move = Balloon.move

    def pop(self):
        for p in self.server.players:
            if not p.pending:
                screen = pygame.Rect(0, 0, 1000, 650)
                screen.center = p.character.rect.center
                if screen.colliderect(self.rect):
                    p.to_send.append({'action':'sound', 'sound':'splash'})
                    
        Splash(self)
        self.kill()









        
