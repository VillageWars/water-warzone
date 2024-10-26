import pygame
import random
import toolbox
import math
from balloon import Bolt
import InnPC

from elements import Sprite, SCREEN, Dummy

class Event(Sprite):
    def __init__(self, server, *args, **kwargs):
        Sprite.__init__(self, self.groups)
        self.NPCs = pygame.sprite.Group()
        self.server = server
    def update(self):
        pass
    def get_coords(self):
        return (3000, 1950)
    def end(self, **kwargs):
        for NPC in self.NPCs:
            NPC.kill()
        self.kill()
    def update(self):
        for NPC in self.NPCs:
            NPC.update()

class BarbarianRaid(Event):
    type = 'Barbarian Raid'
    spawn_coords = {'North':(3000, 400),
                    'South':(3000, 3500),
                    'East':(5600, 1800),
                    'West':(400, 1800)}
    def __init__(self, server, num=None, spawn=None):
        Event.__init__(self, server)
        for b in server.buildings:
            if b.type == 'Inn' and b.NPC:
                b.NPC.depart()
        self.num_barbarians = num or random.randint(4, 7) + 2 * len(self.server.playing)
        self.spawn = spawn or random.choice(['North', 'East', 'South', 'West'])
        self.x, self.y = self.spawn_coords[self.spawn]
        self.leader = BarbarianLeader(self)
        for b in range(self.num_barbarians - 1):
            # Create an instance of one of the two, weight 1:2
            random.choice([BarbarianArcher, BarbarianSwordsman, BarbarianSwordsman])(self)
        for p in self.server.players:
            p.add_message('A tribe of %s barbarians is aproaching from the %s!' % (self.num_barbarians, self.spawn), color=(128,0,128))
        for p in self.server.users:
            p.Send({'action':'music_change', 'music':'barbarianraid'})

    def end(self, attacker=None):
        super().end(attacker=attacker)
        another_raid = False
        for event in self.server.events:
            if event.type == 'Barbarian Raid':
                another_raid = True
        if not another_raid:
            for p in self.server.users:
                p.Send({'action':'music_change', 'music':'village'})
            if attacker.channel:
                victor_buildings = attacker.channel.get_buildings()
                for building in victor_buildings:
                    if building.type == 'Inn':
                        options = [InnPC.RetiredBarbarian, InnPC.Adventurer]
                        for NPC in options[:]:
                            if NPC.building_type in [b.type for b in victor_buildings]:
                                options.remove(NPC)
                        if options:
                            building.NPC = random.choice(options)(building)
        

    def get_coords(self):
        def rect(x, y):
            r = pygame.Rect(0, 0, 50, 50); r.center = x, y; return r
        x, y = self.spawn_coords[self.spawn]
        extra_x, extra_y = toolbox.getDir(random.randrange(0, 360), 60)
        alright = False  # Set to False to restart search for obstacles
        while not alright:
            alright = True
            for barbarian in self.NPCs:
                if barbarian.rect.colliderect(rect(x, y)):
                    x += extra_x
                    y += extra_y
                    alright = False
            obstacle = self.server.obstacles.collide(Dummy, rect(x, y))
            if obstacle and obstacle.type != 'Spiky bush':
                x += extra_x
                y += extra_y
                alright = False
        if x < 50 or x > 5950 or y < 50 or y > 3850:
            return self.get_coords()
        return x, y

class Barbarian(Sprite):
    max_health = 100
    resistance = 0
    id = 0
    gold = 0
    food = 0
    type = 'Barbarian'
    def __init__(self, event):
        self.event = event
        self.channel = None
        self.server = event.server
        self.x, self.y = self.event.get_coords()
        Sprite.__init__(self, event.NPCs, *self.groups)
        self.melee_damage = 10
        self.melee_knockback = 50
        self.balloon_damage = 10
        self.balloon_speed = 17
        self.shoot_cooldown = 0
        self.shot_speed = 50
        self.hurt_count = 0
        self.name = 'A Barbarian'
        self.kill_msg = '<Attacker> killed <Victim> and stole their gold and food.'
        self.shield_count = 0
        self.shield_angle = 0
        self.speed = 2
        self.health = self.max_health
        self.id = Barbarian.id
        Barbarian.id += 1
    def closest_player(self):
        closest = None
        closest_dist = float('inf')
        for character in self.server.characters:
            dist = toolbox.getDist(self.x, self.y, character.x, character.y)
            if dist < closest_dist and not character.dead:
                closest_dist = dist
                closest = character
        return closest
    def closest_dist(self):
        closest = self.closest_player()
        return (toolbox.getDist(self.x, self.y, closest.x, closest.y) if closest else float('inf'))
    @property
    def angle(self):
        closest = self.closest_player() or self.event; return toolbox.getAngle(self.x, self.y, closest.x, closest.y)
    @property
    def rect(self):
        rect = pygame.Rect(0, 0, 50, 50); rect.center = (self.x, self.y); return rect
    def respawn(self):  # Instead of suffocating, teleport to right behind the leader.
        self.x, self.y = self.event.leader.x, self.event.leader.y
        x, y = toolbox.getDir(self.angle + 180, 60)
        self.x += round(x)
        self.y += round(y)

    def update(self):
        if self.hurt_count:
            self.hurt_count -= 1
        if self.shield_count:
            self.shield_count -= 1
        if self.shoot_cooldown:
            self.shoot_cooldown -= 1
        obstacle = self.server.obstacles.collide(self, self.rect)
        if obstacle:
            if obstacle.type == 'Crate' or self.type == 'Barbarian Leader':  # The leader gets pushed back instead of teleported
                x, y = toolbox.getDir(self.angle + 180, 40)
                self.x += round(x)
                self.y += round(y)
            else:
                self.respawn()
        for character in self.server.characters:
            if character.rect.colliderect(self.rect) and not character.dead:
                angle = toolbox.getAngle(self.x, self.y, character.x, character.y)
                character.getHurt(self.melee_damage, attacker=self, name=self.name, angle=angle, knockback=self.melee_knockback, msg=self.kill_msg)
                if character.dead and self.alive():
                    self.gold += character.gold
                    self.food += character.food
                    character.gold = character.food = 0

        for p in self.server.users:
            visible_rect = pygame.Rect(0, 0, 700, 700)  # Bigger so that the F3 radius is visible (350 * 2)
            visible_rect.center = p.character.get_coords(self)
            if SCREEN.colliderect(visible_rect):
                p.to_send.append({'action':'draw_barbarian',
                                  'type':{'Barbarian Leader': 'leader',
                                          'Barbarian Archer': 'archer',
                                          'Barbarian Swordsman': 'swordsman'}[self.type],
                                  'hurt': self.hurt_count,
                                  'coords': visible_rect.center,
                                  'angle': self.angle,
                                  'health': self.health,
                                  'shield': (self.shield_angle if self.shield_count else None)})
        collisions = []
        for barbarian in self.event.NPCs:
            if barbarian.rect.colliderect(self.rect):
                collisions.append(barbarian)
        max_id_barbarian = max(collisions, key=lambda b: b.id)
        if self == max_id_barbarian:
            self.move()
    def move(self):
        x, y = toolbox.getDir(self.angle, self.speed)
        self.move_x(x)
        self.move_y(y)
    def move_x(self, amount):
        self.x += amount
        obstacle = self.server.obstacles.collide(self, self.rect)
        if obstacle:
            self.x -= amount
    def move_y(self, amount):
        self.y += amount
        obstacle = self.server.obstacles.collide(self, self.rect)
        if obstacle:
            self.y -= amount
    def shield_use(self):
        return random.randint(0, 2) == 0
    def getHurt(self, damage, attacker=Dummy, angle=0, knockback=0, **kwargs):
        if self.shield_use() and attacker != self:
            self.shield_angle = angle + 180
            self.shield_count = 20
            for p in self.event.server.users:
                rect = p.character.get_rect(self.rect)
                if SCREEN.colliderect(rect):
                    p.Send({'action':'sound','sound':'bump'})
            return self.shield_angle + random.randint(-20, 20)
        else:
            self.health -= damage - self.resistance
            self.hurt_count = 10
            if self.health <= 0:
                self.health = 0
                self.kill()
                for p in self.event.server.users:
                    p.add_message(self.name + ' has been defeated!')
                if hasattr(attacker, 'gold'):
                    attacker.gold += self.gold
                    attacker.food += self.food
            x, y = toolbox.getDir(angle, knockback)
            self.move_x(x)
            self.move_y(y)
    def kill(self):
        Sprite.kill(self)
    def __repr__(self):
        return f'<{self.type} {self.id}>'
class BarbarianLeader(Barbarian):
    type = 'Barbarian Leader'
    resistance = 2  # + 1.5 per player
    gold = 300
    food = 300
    def __init__(self, event):
        Barbarian.__init__(self, event)
        self.resistance += math.floor(1.5 * len(self.server.playing))
        self.name = 'The Barbarian Leader'
    def update(self):
        super().update()
        self.speed = (1 if self.closest_dist() <= 400 else 2)
    def shield_use(self):
        return random.randint(0, 2) != 0  # 2:1 weight
    def getHurt(self, damage, attacker=Dummy, **kwargs):
        result = super().getHurt(damage, attacker=attacker, **kwargs)
        if self.health <= 0:
            self.event.end(attacker)
            for p in self.event.server.users:
                p.add_message('The Barbarian tribe has been defeated.', color=(128,0,128))
        return result

class BarbarianArcher(Barbarian):
    type = 'Barbarian Archer'
    resistance = 4
    gold = 50
    food = 50
    def __init__(self, event):
        Barbarian.__init__(self, event)
        self.name = 'A Barbarian Archer'
    def update(self):
        super().update()
        self.speed = 2
        if self.closest_dist() <= 350:
            self.speed = 0
            self.shoot()
    def shoot(self):
        if not self.shoot_cooldown:
            self.shoot_cooldown = self.shot_speed
            Bolt(self)

class BarbarianSwordsman(Barbarian):
    type = 'Barbarian Swordsman'
    gold = 50
    food = 50
    resistance = 4
    def __init__(self, event):
        Barbarian.__init__(self, event)
        self.name = 'A Barbarian Swordsman'
    def update(self):
        super().update()
        self.speed = (5 if self.closest_dist() <= 350 else 2)