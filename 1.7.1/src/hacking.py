from building import *

def kick(self, playername):
    for p in self.server.players:
        if p.username == playername:
            p.Send({'action':'kicked'})
    
    print('Kicked ' + playername)
    del self.server.players[playername]


def makeWallsFall(self):
    self.server.upwall.count = 10
    self.server.leftwall.count = 10


def kill(self, playername):
    for p in self.server.players:
        if p.username == playername:
            break
    p = p.character
    p.getHurt(300, self.character, 0, 0, msg="<Attacker> killed <Victim> using cheats")


def win(self):
    self.server.terminate(self)


def message(self, theMessage, color=(0,0,0)):
    for p in self.server.players:
        p.message = message
        p.message_color = color
        p.message_count = 160

def redybarb(self):
    self.character.attack = 200
    self.character.has_shield = True
    makeWallsFall(self)
    BarbarianRaid(self.server, 10)
    
