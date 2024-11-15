class Background():
    def __init__(self, server):
        self.server = server
        self.x = -1500
        self.y = -800
    def update(self):
        if not self.server.in_lobby:
            self.x = 0
            self.y = 0
        for p in self.server.users:
            p.to_send.append({'action':'draw_setting', 'coords':(p.character.get_x(self), p.character.get_y(self))})