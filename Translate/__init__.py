from .server import Server, Channel
from .client import Client
import socket
import requests

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
