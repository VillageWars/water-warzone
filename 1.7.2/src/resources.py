import pygame
import pygame as p
import random as r

class Farm(pygame.sprite.Sprite):
    def __init__(self, server, coords):
        pygame.sprite.Sprite.__init__(self, self.gp)
        self.x = coords[0]
        self.y = coords[1]
        self.server = server
        self.foods = pygame.sprite.Group()
        server.building_blocks.append(pygame.Rect(self.x, self.y, 400, 150))
        self.production = 1000
        

        coords = []
        while len(list(self.foods)) < 32:
            food = Wheat(self, self.foods)
            if (food.x, food.y) not in coords:
                coords.append((food.x, food.y))
            else:
                food.kill()
        

        del coords
    

    def update(self): 
        self.foods.update()

    def HandleInput(self, mouse, player):
        for food in self.foods:
            food.drawrect.x, food.drawrect.y = player.get_x(food), player.get_y(food)
            if food.drawrect.collidepoint(mouse[:2]) and bool(mouse[2]) and (food.image == 'good' or food.image == 'mine'):
                if not player.dead:
                    food.mine(player)
                    return True
                    
        return False


class Wheat(pygame.sprite.Sprite):
    def __init__(self, farm, gp):
        pygame.sprite.Sprite.__init__(self, gp)
        self.farm = farm
        self.x = r.randint(farm.x, farm.x + 375)
        self.y = r.randint(farm.y, farm.y + 40)
        self.image = 'good'
        self.count = 0
        self.mining = 15
        self.drawrect = p.Rect(0,0,45,45)

    def pick(self, player):
        self.image = 'used'
        self.count = self.farm.production
        player.food += r.randint(1,4)


    def mine(self, player):
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
        
        for p in self.farm.server.players:
            if not p.pending:
                self.drawrect.x, self.drawrect.y = p.character.get_x(self), p.character.get_y(self)
                screen = pygame.Rect(0, 0, 1000, 650)
                if screen.colliderect(self.drawrect):
                    p.to_send.append({'action':'draw_farm',
                        'coords':(p.character.get_x(self), p.character.get_y(self)),
                        'state':self.image})



class Mine(pygame.sprite.Sprite):
    def __init__(self, server, coords):
        pygame.sprite.Sprite.__init__(self, self.gp)
        self.x = coords[0]
        self.y = coords[1]
        self.server = server
        self.golds = pygame.sprite.Group()
        server.building_blocks.append(pygame.Rect(self.x, self.y, 200, 600))
        self.production = 1000

        self.right = self.x > 3000

        wall = MineWalls(coords, (200, 18))
        server.obs.append(wall)
        wall = MineWalls((self.x, self.y + 570), (200, 30))
        server.obs.append(wall)

        if not self.right:
            wall = MineWalls(coords, (30, 600))
            server.obs.append(wall)
        else:
            wall = MineWalls((self.x + 170, self.y), (30, 600))
            server.obs.append(wall)

        coords = []
        while len(list(self.golds)) < 32:
            gold = Gold(self, self.golds)
            if (gold.x, gold.y) not in coords:
                coords.append((gold.x, gold.y))
            else:
                gold.kill()

        del coords
        


    def update(self):
        for p in self.server.players:
            if not p.pending:
                p.to_send.append({'action':'draw_mine',
                    'coords':(p.character.get_x(self), p.character.get_y(self)),
                    'right':self.right})
            
        self.golds.update()

    def HandleInput(self, mouse, player):
        for gold in self.golds:
            gold.drawrect.x, gold.drawrect.y = player.get_x(gold), player.get_y(gold)
            if gold.drawrect.collidepoint(mouse[:2]) and bool(mouse[2]) and (gold.image == 'good' or gold.image == 'mine'):
                if not player.dead:
                    gold.collect(player)
                    return True

                    
        return False
    

class Gold(pygame.sprite.Sprite):
    def __init__(self, mine, gp):
        pygame.sprite.Sprite.__init__(self, gp)
        self.mine = mine
        self.x = r.randint(mine.x + 30, mine.x + 140)
        self.y = r.randint(mine.y + 15, mine.y + 540)
        self.image = 'good'
        self.count = 0
        self.mining = 30
        self.drawrect = p.Rect(0,0,45,30)


    def pick(self, player):
        self.image = 'used'
        self.count = self.mine.production
        player.gold += r.randint(1,3)


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
        
        for p in self.mine.server.players:
            if not p.pending:
                screen = pygame.Rect(0, 0, 1000, 650)
                self.drawrect.x, self.drawrect.y = p.character.get_x(self), p.character.get_y(self)
                if screen.colliderect(self.drawrect):
                    p.to_send.append({'action':'draw_gold',
                        'coords':(p.character.get_x(self), p.character.get_y(self)),
                        'state':self.image})




class MineWalls():
    def __init__(self, topleft, size):
        self.innerrect = pygame.Rect(topleft[0], topleft[1], size[0], size[1])
        self.owner = None
    def isBuilding(self):
        return False
    def getHurt(self, damage, attacker):
        pass







