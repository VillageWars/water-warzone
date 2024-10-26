import pygame

from elements import Obstacle

class Walls(Obstacle):
    def __init__(self, server, direction):
        self.server = server
        if direction == 'left-right':
            rect = pygame.Rect(0, 1860, 6000, 180)
        elif direction == 'up-down':
            rect = pygame.Rect(2965, 0, 80, 3900)
        self.dimensions = rect.size
        Obstacle.__init__(self, self.server, *rect.center)
        self.dir = direction
        self.count = round(30 * 60 * server.walls_time)
        
    def update(self):
        if self.count > 0:
            self.count -= 1
        if self.count == 0:
            if self.dir == 'up-down':
                self.server.Fall()
            self.kill()

    def getHurt(*args, **kwargs):
        pass

    def explode(self):
        pass