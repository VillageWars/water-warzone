import pygame as p
import toolbox as t

class LobbyAvatar():
    def __init__(self, coords):
        self.x, self.y = coords
        self.x_flip = 500-self.x # Center on screen 
        self.y_flip = 325-self.y #   (1000, 650)
        self.angle = 0
        self.speed =  8
        self.ready = False

    @property
    def coords(self):
        return self.x, self.y


    

    def get_x(self, item):
        if hasattr(item, 'x'):
            return item.x + self.x_flip
        return item + self.x_flip
        

    def get_y(self, item):
        if hasattr(item, 'y'):
            return item.y + self.y_flip
        return item + self.y_flip

    def move_x(self, amount=None):
        if amount is None:
            amount = self.speed
        
        self.x += amount
        self.x_flip -= amount

        if self.x < 50:
            self.x -= amount
            self.x_flip += amount
        if self.x > 950:
            self.x -= amount
            self.x_flip += amount
        
    def move_y(self, amount=None):
        if amount is None:
            amount = self.speed
        
        self.y += amount
        self.y_flip -= amount

        if self.y < 50:
            self.y -= amount
            self.y_flip += amount
        if self.y > 600:
            self.y -= amount
            self.y_flip += amount

    def move(self):
        x, y = t.getDir(self.angle, self.speed)
        self.move_x(round(x))
        self.move_y(round(y))

    def HandleInput(self, keys, mouse):
        if keys[p.K_SPACE]:
            self.move()
        self.angle = t.getAngle(500, 325, mouse[0], mouse[1])





