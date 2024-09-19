import sys, time
sys.path.append('../')

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

from net2web import Server, Channel, Clock

class MyChannel(Channel):
    def Network_channel(self, data):
        logging.critical('Channel reveived data!')
        
class MyServer(Server):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ChannelClass = MyChannel
        self.clock = Clock(30)
        
    def update(self):
        self.clock()
        self.pump()
        for p in self.players:
            if p.connected and round(time.time()) % 2 == 0:
                p.Send({'action':'server'})


server = MyServer(host='localhost')
while True:
    server.update()
