import pygame
import toolbox as t
from animations import *
import random

import elements

class Balloon(elements.Balloon):
    def pop(self):
        for p in self.server.users:
            screen = pygame.Rect(0, 0, 1000, 650)
            screen.center = p.character.rect.center
            if screen.colliderect(self.rect):
                p.to_send.append({'action':'sound', 'sound':'splash'})
        Splash(self)
        self.kill()

class ArcheryBalloon(Balloon):
    def __init__(self, owner, **kwargs):
        Balloon.__init__(self, owner, **kwargs)
        if self.shooter.type != 'Archery Tower':
            self.shooter_name = 'An Archery Tower balloon'
        else:
            self.shooter_name = self.shooter.name + '\'s Archery Tower'
        self.image_id = 0

class Bolt(elements.Balloon):
    def __init__(self, owner, **kwargs):
        if owner.type == 'Character':
            kwargs['msg'] = '<Attacker> shot <Victim> with a barbarian crossbow.'
        else:
            kwargs['msg'] = '<Attacker> shot <Victim> and stole their gold and food.'
        elements.Balloon.__init__(self, owner, **kwargs)
        self.image_id = 4
    def pop(self):
        self.kill()


class TraitorBalloon(Balloon):  # Not used in vanilla
    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        if self.shooter and not self.rect.colliderect(self.shooter.rect):
            self.shooter = elements.Dummy