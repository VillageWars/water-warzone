import pyperclip
import pygame as p
from pygame.locals import *
from time import monotonic

class Typing:
    def __init__(self, character='|', block=['@', '/', '.', ' ']):
        self.typing = character
        self.character = character
        self.shifting = False
        self.ctrling = False
        self.block = block

    @property
    def result(self):
        return self.typing[:self.typing.find(self.character)] + self.typing[self.typing.find(self.character) + 1:]


    def shift(self):
        self.shifting = not self.shifting

    def ctrl(self):
        self.ctrling = not self.ctrling

    def type(self, event):
        if event.key == K_a:
            self.add('a')
        if event.key == K_b:
            self.add('b')
        if event.key == K_c:
            self.add('c')
        if event.key == K_d:
            self.add('d')
        if event.key == K_e:
            self.add('e')
        if event.key == K_f:
            self.add('f')
        if event.key == K_g:
            self.add('g')
        if event.key == K_h:
            self.add('h')
        if event.key == K_i:
            self.add('i')
        if event.key == K_j:
            self.add('j')
        if event.key == K_k:
            self.add('k')
        if event.key == K_l:
            self.add('l')
        if event.key == K_m:
            self.add('m')
        if event.key == K_n:
            self.add('n')
        if event.key == K_o:
            self.add('o')
        if event.key == K_p:
            self.add('p')
        if event.key == K_q:
            self.add('q')
        if event.key == K_r:
            self.add('r')
        if event.key == K_s:
            self.add('s')
        if event.key == K_t:
            self.add('t')
        if event.key == K_u:
            self.add('u')
        if event.key == K_v and not self.ctrling:
            self.add('v')
        if event.key == K_w:
            self.add('w')
        if event.key == K_x:
            self.add('x')
        if event.key == K_y:
            self.add('y')
        if event.key == K_z:
            self.add('z')
        if event.key == K_1:
            self.add('1')
        if event.key == K_2:
            self.add('2')
        if event.key == K_3:
            self.add('3')
        if event.key == K_4:
            self.add('4')
        if event.key == K_5:
            self.add('5')
        if event.key == K_6:
            self.add('6')
        if event.key == K_7:
            self.add('7')
        if event.key == K_8:
            self.add('8')
        if event.key == K_9:
            self.add('9')
        if event.key == K_0:
            self.add('0')
        if event.key == K_PERIOD:
            self.add('.')
        if event.key == K_SLASH:
            self.add('/')

        if event.key == K_SPACE:
            self.add(' ')

        if event.key == K_BACKSPACE:
            self.typing = self.typing[:-2] + self.character

        if event.key == K_v and self.ctrling:
            self.typing = self.typing[:self.typing.find(self.character)] + pyperclip.paste() + self.typing[self.typing.find(self.character):]
        
    def add(self, letter):
        if self.shifting:
            letter = letter.upper()
            if letter == '2':
                letter = '@'
        if letter not in self.block:
            self.typing = self.typing[:self.typing.find(self.character)] + letter + self.typing[self.typing.find(self.character):]

    def text(self):
        if monotonic() % 1.2 > 0.6:
            return self.typing[:-1]
        return self.typing
