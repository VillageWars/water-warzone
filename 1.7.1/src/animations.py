import pygame

class Animation(pygame.sprite.Sprite):
    def __init__(self, item):
        super().__init__(self.gp)
        self.frame = 0
        self.len = 3
        self.server = (item.server if hasattr(item, 'server') else item.channel.server)
        self.size = 50
        self.x = item.x
        self.y = item.y
        
    def __len__(self):
        return self.len

    def update(self):
        self.frame += 1
        if len(self) == self.frame:
            self.kill()
        else:
            for p in self.server.players:
                if not p.pending:
                    screen = pygame.Rect(0, 0, 1000, 650)
                    rect = pygame.Rect(0, 0, self.size, self.size)
                    rect.center = (p.character.get_x(self), p.character.get_y(self))
                    if screen.colliderect(rect):
                        p.to_send.append({'action':'animation',
                                    'coords':(p.character.get_x(self), p.character.get_y(self)),
                                    'name':self.__class__.__name__,
                                    'frame':self.frame})


class Splash(Animation):
    def __init__(self, balloon):
        super().__init__(balloon)
        self.size = 30

class Explosion(Animation):
    def __init__(self, item):
        super().__init__(item)
        self.size = 64

class BAM(Animation):
    def __init__(self, TNT):
        super().__init__(TNT)
        self.size = 360
        self.len = 6
