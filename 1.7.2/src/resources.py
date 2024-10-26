import pygame
import random
from elements import Sprite, Obstacle

class Farm(Sprite):
    type = 'Farm'
    def __init__(self, server, coords):
        pygame.sprite.Sprite.__init__(self, *self.groups)
        self.x = coords[0]
        self.y = coords[1]
        self.server = server
        self.foods = pygame.sprite.Group()
        self.zone_rect = pygame.Rect(self.x, self.y, 400, 150)
        self.production = 1000  # Backwards food production rate
        coords = []
        while len(list(self.foods)) < 32:
            food = Wheat(self, self.foods)
            if (food.x, food.y) not in coords:
                coords.append((food.x, food.y))
            else:
                food.kill()

    def update(self): 
        self.foods.update()

    def HandleInput(self, mouse, player):
        for food in self.foods:
            food.drawrect.x, food.drawrect.y = player.get_x(food), player.get_y(food)
            if food.drawrect.collidepoint(mouse[:2]) and bool(mouse[2]) and (food.image == 'good' or food.image == 'mine'):
                if not player.dead:
                    food.collect(player)
                    return True
                    
        return False

class Wheat(pygame.sprite.Sprite):
    def __init__(self, farm, gp):
        pygame.sprite.Sprite.__init__(self, gp)
        self.farm = farm
        self.x = random.randint(farm.x, farm.x + 375)
        self.y = random.randint(farm.y, farm.y + 40)
        self.image = 'good'
        self.count = 0
        self.mining = 15
        self.drawrect = pygame.Rect(0, 0, 45, 45)

    def pick(self, player):
        self.image = 'used'
        self.count = self.farm.production
        player.food += random.randint(1,4)

    def collect(self, player):
        if self.image == 'good' or self.image == 'mine':
            self.image = 'mine'
            self.mining -= 1
            if self.mining == 0:
                self.pick(player)

    def update(self):
        if self.count > 0:
            self.count -= 1
            if self.count == 0:
                self.image = 'good'
                self.mining = 15
        for p in self.farm.server.users:
            self.drawrect.x, self.drawrect.y = p.character.get_coords(self)
            screen = pygame.Rect(0, 0, 1000, 650)
            if screen.colliderect(self.drawrect):
                p.to_send.append({'action':'draw_farm',
                    'coords':(p.character.get_x(self), p.character.get_y(self)),
                    'state':self.image})

class Mine(Sprite):
    type = 'Mine'
    def __init__(self, server, coords):
        pygame.sprite.Sprite.__init__(self, *self.groups)
        self.x = coords[0]
        self.y = coords[1]
        self.server = server
        self.golds = pygame.sprite.Group()
        self.zone_rect = pygame.Rect(self.x, self.y, 200, 600)
        self.production = 1000  # Backwards gold discovery rate
        self.right = self.x > 3000

        MineWalls.server = server
        wall = MineWalls(coords, (200, 18))
        server.obs.append(wall)
        wall = MineWalls((self.x, self.y + 570), (200, 30))

        if self.right:
            wall = MineWalls((self.x + 170, self.y), (30, 600))
        else:
            wall = MineWalls(coords, (30, 600))
        coords = []
        while len(list(self.golds)) < 32:
            gold = Gold(self, self.golds)
            if (gold.x, gold.y) not in coords:
                coords.append((gold.x, gold.y))
            else:
                gold.kill()
        
    def update(self):
        for p in self.server.users:
            p.to_send.append({'action':'draw_mine',
                    'coords':(p.character.get_x(self), p.character.get_y(self)),
                    'right':self.right})
        self.golds.update()

    def HandleInput(self, mouse, character):
        for gold in self.golds:
            gold.drawrect.x, gold.drawrect.y = character.get_x(gold), character.get_y(gold)
            if gold.drawrect.collidepoint(mouse[:2]) and bool(mouse[2]) and (gold.image == 'good' or gold.image == 'mine'):
                if not character.dead:
                    gold.collect(character)
                    return True
        return False

class Gold(pygame.sprite.Sprite):
    def __init__(self, mine, gp):
        pygame.sprite.Sprite.__init__(self, gp)
        self.mine = mine
        self.x = random.randint(mine.x + 30, mine.x + 140)
        self.y = random.randint(mine.y + 15, mine.y + 540)
        self.image = 'good'
        self.count = 0
        self.mining = 30
        self.drawrect = pygame.Rect(0,0,45,30)

    def pick(self, player):
        self.image = 'used'
        self.count = self.mine.production
        player.gold += random.randint(1,3)

    def collect(self, player):
        if self.image == 'good' or self.image == 'mine':
            self.image = 'mine'
            self.mining -= 1
            if self.mining == 0:
                self.pick(player)

    def update(self):
        if self.count > 0:
            self.count -= 1
            if self.count == 0:
                self.image = 'good'
                self.mining = 30
        
        for p in self.mine.server.users:
            screen = pygame.Rect(0, 0, 1000, 650)
            self.drawrect.x, self.drawrect.y = p.character.get_x(self), p.character.get_y(self)
            if screen.colliderect(self.drawrect):
                p.to_send.append({'action':'draw_gold',
                                'coords':(p.character.get_x(self), p.character.get_y(self)),
                                'state':self.image})




class MineWalls(Obstacle):
    def __init__(self, topleft, size):
        rect = pygame.Rect(topleft, size)
        x, y = rect.center
        self.dimensions = size
        Obstacle.__init__(self, self.server, x, y)
    def isBuilding(self):
        return False
    def getHurt(self, damage, **kwargs):
        pass