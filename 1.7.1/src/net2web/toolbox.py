import time
import socket
import requests


class Clock:
    def __init__(self, fps=30):
        self.frame_delay = 1 / fps
        self.start_time = time.time()
        self.fps = fps
        
    def __call__(self, fps=None):
        if fps and fps != self.fps:
            self.frame_delay = 1 / fps
            self.fps = fps
        time.sleep(self.get_tick())  # Delay for the remaining time

    def get_tick(self):
        end_time = time.time()
        frame_time = end_time - self.start_time
        self.start_time = end_time
        if frame_time < self.frame_delay:
            return self.frame_delay - frame_time
        return 0
        
        
def getmyip(local=True):
    """
    Finds the IP address of the local computer
    """
    if local:
        return socket.gethostbyname(socket.gethostname())

    else:
        url = 'https://api.ipify.org?format=json'
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        return data['ip']
