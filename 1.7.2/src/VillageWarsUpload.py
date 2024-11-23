import os
import zipfile2 as zipfile
import sys
import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
log = logging.getLogger()
log.debug('Initializing')
import pymsgbox
import re
import requests
import toolbox
import shutil

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
    log.debug('Successfully Uploaded VillageWars to remote server')
    upload_version_info()

def upload_version_info():
    log.debug('Uploading version information...')
    url = 'https://villagewars.pythonanywhere.com/upload_version_info'
    with open('../../version screenshots/version_info.json','r') as file:
        files=[('file', ('version_info.json', file, 'text/json'))]
        response = requests.post(url, files=files)
    response.raise_for_status()
    log.debug('Successfully uploaded version info')

print('This will upload the current version the the VillageWars server. Are you sure you want to do this? (y/n)')
a = input('> ').strip()[0].lower()
print()
if a == 'n':
    print('Ok, thanks!')
    print()
    input('Press enter to exit')
    sys.exit()
assert a == 'y'

#compress_version(skip=SKIP)

input('Press enter to continue to prepare WaterWarzone')

with open('../../WaterWarzone/app.py', 'w') as fo:
    fo.write(f"import os\nos.chdir('{__version__}')\nresult = os.system('python -m app')")

discontinued_version = input('Enter the name of the discontinued version: ')
while not os.path.exists(f'../../WaterWarzone/{discontinued_version}'):
    discontinued_version = input('That directory does not exist.\nEnter the name of the discontinued version: ')
shutil.rmtree(f'../../WaterWarzone/{discontinued_version}')
log.info(f'Unlinked version {discontinued_version} from WaterWarzone directory')


shutil.copytree('../', f'../../WaterWarzone/{__version__}', ignore=lambda src, names: [name for name in names if name.endswith('.zip') or name in ['screenshots', '__pycache__']])
log.info(f'Successfully copied version {__version__} to WaterWarzone directory')

input('Press enter to start heroku upload')

os.chdir('../../WaterWarzone')
os.system('git add .')
os.system('git commit -m "%s"' % input('Commit name: '))
os.system('git push -u origin master')
os.system('git push heroku')
os.system('heroku logs --tail --app water-warzone')
