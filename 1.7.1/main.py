import os, sys, json
import subprocess

with open('preferences.json', 'r') as fo:
    preferences = json.loads(fo.read())
    py = preferences.get('py', 'python')

missing_modules = []
try:
    import pygame
except:
    missing_modules.append('pygame')
try:
    import requests
except:
    missing_modules.append('requests')
try:
    import bs4
except:
    missing_modules.append('beautifulsoup4')
try:
    import pymsgbox
except:
    missing_modules.append('pymsgbox')
try:
    import pyperclip
except:
    missing_modules.append('pyperclip')
try:
    import progress_bar
except:
    missing_modules.append('progress_bar')
try:
    import send2trash
except:
    missing_modules.append('send2trash')
try:
    import zipfile2
except:
    missing_modules.append('zipfile2')

try:
    fo = open('../version screenshots/version_info.json', 'r')
    fo.close()
except OSError:
    missing_modules.append('version_info.json')



os.chdir('src')
#pymsgbox.alert('*'.join(missing_modules))
#print(missing_modules)
if len(missing_modules) > 0:
    os.system(py + ' -m setup ' + '*'.join(missing_modules))

else:
    os.system(py + ' -m VillageWarsClient')
    input()
    
