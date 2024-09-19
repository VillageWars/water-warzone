# This file was created 9-10-2024 (1.7.2 beta) in order to attempt to organize the file structure better.

# Python Standard Library Modules Import

import os
import json
import sys
import logging as log

# Third-Party Imports

import pygame as p
import requests


def file_size(path='.'):
    try:
        if os.path.isdir(path):
            total = 0
            with os.scandir(path) as it:
                for entry in it:
                    if entry.is_file():
                        total += entry.stat().st_size
                    elif entry.is_dir():
                        total += file_size(entry.path)
            return total
        return os.path.getsize(path)
    except:
        return 0
      
def resolve(path):
    if path.endswith('png') or path.endswith('jpg') or path.endswith('jpeg'):
        contents = p.image.load(path)
        file_type = 'image'
    elif path.endswith('wav') or path.endswith('mp3'):
        contents = p.mixer.Sound(path)
        file_type = 'audio'
    return {'type': file_type,
            'name': os.path.split(path)[1],
            'path': path,
            'contents': contents}

def res(title, dimensions):  # `res` for resolution
    return p.transform.scale(images[title], dimensions)

def check_internet(timeout=5):
    try:
        requests.head("http://villagewars.pythonanywhere.com/test_connection", timeout=timeout)
        return True
    except:
        return False

def refresh():
    global INTERNET
    log.debug('Refreshed; Testing Internet connection')
    INTERNET = check_internet()
    return INTERNET

if not p.get_init():
    p.init()

# Obtain VillageWars path

log.debug('Fetching environment path')
src_dir = os.path.split(__file__)[0]
version_dir = src_dir[:-3]
VillageWars_dir = version_dir[:-(1 + len(os.path.basename(version_dir[:-1])))]
PATH = version_dir
assets_dir = PATH + 'assets'

VERSION = os.path.basename(PATH[:-1])
sys.path.append(PATH + 'src')
os.chdir(src_dir)

with open(PATH + 'conf/preferences.json', 'r') as fo:
    preferences = json.loads(fo.read())
    PY = preferences.get('py', 'py')
    lib = preferences.get('path', [])
    sys.path.extend(lib)
    MAP_TEXTURE = preferences.get('map', 'grass')

def init():
    global assets, images, audio, INTERNET
    log.debug('Testing Internet connection')
    INTERNET = check_internet()
    
    log.debug('Loading assets')
    assets = {}
    for root, dirs, files in os.walk(assets_dir):
        if root == assets_dir:
            for file in files:
                assets[file] = resolve(root + '\\' + file)
        else:
            for file in files:
                assets[root[len(assets_dir)+1:] + '/' + file] = resolve(root + '\\' + file)

    images = {}
    for asset in assets:
        if assets[asset]['type'] == 'image':
            images[asset] = assets[asset]['contents']

    audio = {}
    for asset in assets:
        if assets[asset]['type'] == 'audio':
            audio[asset.replace('sfx/', '')] = assets[asset]['contents']

if __name__ == '__main__':  # Only for testing
    init()
