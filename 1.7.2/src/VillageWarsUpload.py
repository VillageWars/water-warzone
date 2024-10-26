import os
import zipfile2 as zipfile
import sys
import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
log = logging.getLogger()
import pymsgbox
import re
import requests
import toolbox

SKIP = []

path = os.path.abspath('../')
regex = re.compile(r'(\d)+\.(\d)+\.(\d)+')
__version__ = regex.search(path).group()
version = __version__

def compress_version(skip=None):
    if skip == None:
        skip = []
    log.debug('Starting Compression...')
    global version
    zipFilename = version + '.zip'
    log.debug(f'Creating {zipFilename}...')
    versionZip = zipfile.ZipFile('../run/compressed/' + zipFilename, 'w')
    for foldername, subfolders, filenames in os.walk('../'):
        if 'pycache' in foldername:
            continue
        con = False
        for i in skip:
            if i in foldername:
                con = True
        if con:
            continue
        versionZip.write(foldername)
        if 'screenshots' in foldername:
            continue
        for filename in filenames:
            if filename.endswith('.zip'):
                continue
            if filename.endswith('serverlog.txt'):
                continue
            if os.path.basename(filename) in skip:
                continue
            log.debug(f'Adding {os.path.basename(filename)}...')
            versionZip.write(foldername + '/' + filename)

    log.debug('Final compression...')
    versionZip.close()
    log.debug(f'Successfully compressed {zipFilename}!')
    log.debug('Uploading...')
    url = 'https://villagewars.pythonanywhere.com/upload_version/' + version
    payload={}
    files=[('file',(zipFilename,open('../run/compressed/' + zipFilename,'rb'),'image/zip'))]
    response = requests.post(url, files=files)
    log.debug('Successfully Uploaded to server')
    log.debug('Sending version info...')
    url = 'https://villagewars.pythonanywhere.com/upload_version_info'
    payload={}
    files=[('file',('version_info.json',open('../../version screenshots/version_info.json','r'),'text/json'))]
    response = requests.post(url, files=files)
    log.debug('Successfully uploaded version info')
    response.raise_for_status()
    
log.debug('Initializing')
print('This will upload the current version the the VillageWars server. Are you sure you want to do this? (y/n)')
a = input('> ').strip()[0].lower()
print()
if a == 'n':
    print('Ok, thanks!')
    print()
    input('Press enter to exit')
    sys.exit()
assert a == 'y'

compress_version(skip=SKIP)
