import sys, time
sys.path.append('../')

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')


from net2web import Client, Clock

class MyClient(Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clock = Clock(30)
    def update(self):
        self.pump()
        if self.connected and round(time.time()) % 2 == 0:
            self.send({'action':'channel'})
        self.clock()
    def Network_server(self, data):
        logging.critical('Client reveived data!')


client = MyClient(host='localhost')
while True:
    client.update()
