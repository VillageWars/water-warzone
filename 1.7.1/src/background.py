
class Background():

    def __init__(self, server):
        self.server = server
        self.x = 0
        self.y = 0
        

    def update(self):

        for p in self.server.players:
            if not p.pending:
                p.to_send.append({'action':'draw_setting', 'coords':(p.character.get_x(self), p.character.get_y(self))})
