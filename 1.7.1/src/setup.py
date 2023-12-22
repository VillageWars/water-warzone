import os
import sys
import json
try:
    import text_decoration
except ImportError:  # Doesn't matter
    class text_decoration:
        def rgb(*args): return args[0]
        def holiday(): return ''

with open('../preferences.json', 'r') as fo:
    preferences = json.loads(fo.read())
    py = preferences.get('py', 'python')

version = f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'
print('Running python version', version)

print()
print()

print('Welcome to VillageWars!')

print(text_decoration.holiday())
print()

print('I hope you enjoy playing it!')

print()

print()
print('Would you to set preferences? (y/n)')
answer = input('> ').strip()[0].lower()
print()
assert answer in ('y', 'n')
if answer == 'y':
    
    print('What would you like your map\'s theme to be? (please enter one of "' + text_decoration.rgb('grass', (0,200,0)) + '" (default), "' + text_decoration.rgb('pink', (255,200,200)) + '", or "' + text_decoration.rgb('snow', (255,255,255)) + '")')
    map = input('> ').lower()
    while map not in ['grass', 'pink', 'snow']:
        print('That is invalid. Please enter one of "' + text_decoration.rgb('grass', (0,200,0)) + '" (default), "' + text_decoration.rgb('pink', (255,200,200)) + '", or "' + text_decoration.rgb('snow', (255,255,255)) + '".')
        map = input('> ').lower()
    print()
    print('Map set to "' + map + '"')
    print()
    print('Do you have a prefered python interpreter? (default is "python", but may vary)')
    interp = input('> ').lower()
    if interp not in ['python', 'py', 'python3', '', 'python.exe', 'py.exe']:
        print('That is an unusual interpreter. Please type it again to confirm.')
        interp = input('> ').lower()
    if interp == '':
        interp = 'python'
    py = interp
    print()
    print('Interpreter set to "' + interp + '"')
    print()
    preferences = {'map':map, 'py':interp}
    with open('../preferences.json', 'w') as fo:
        fo.write(json.dumps(preferences))
else:
    print('Ok, see https://villagewars.fandom.com/wiki/Setting_Preferences to learn how to set them later.')

version_info = False
if len(sys.argv) > 1:
    missing_modules = sys.argv[1].split('*')
    if 'version_info.json' in missing_modules:
        missing_modules.remove('version_info.json')
        version_info = True
else:
    missing_modules = []


print('You are missing a few elements necessary to start VillageWars.')
print('Would you like these elements to be installed? (y/n)')
answer = input('> ').strip()[0].lower()
if answer == 'n':
    print('Ok, well, see you later then!')
    print()
    input('Press enter to exit')
    sys.exit()
    
assert answer == 'y'
print()
print('You are missing the following third-party modules from VillageWars:')
print()
for module in missing_modules:
    print(module)
print()
for module in missing_modules:
    input('Press enter to install %s' % module)
    exit_code = os.system('{} -m pip install {}'.format(py, module))
    if exit_code == 1:  # maybe `py` doesn't work.
        exit_code = os.system('{} -m pip install {}'.format(('py.exe' if py == 'python.exe' else 'python.exe'), module))
    if exit_code == 1:
        print('Hmmm. Is seems like there was an error. Check your internet connection, then try again. If the problem persists, call Aaron.')
        print()
        input('Press enter to exit.')
        sys.exit()
        
    print()

from progress_bar import InitBar as Bar
import send2trash
import requests

    

print()
input('Press enter to continue')    
    
print()
if version_info:
    print('You\'re missing the version information documents that let you update VillageWars. Hold on while those documents are fetched.')
    print()
    input('Press enter to continue')
    print()
    print('Collecting version_info.json')
    print()
    bar = Bar('Downloading:')
    bar(0)
    res = requests.get('http://villagewars.pythonanywhere.com/download_version_info', stream=True)
    res.raise_for_status()
    bar(10)
    try:
        download_size = int(res.headers['Content-length'])
    except KeyError:
        download_size = 2048
    downloaded_bytes = 0
    os.makedirs('../../version screenshots', exist_ok=True)
    fo = open('../../version screenshots/version_info.json', 'wb')
    for chunk in res.iter_content(chunk_size=32):
        if chunk: # filter out keep-alive new chunks
            len_chunk = len(chunk)
            fo.write(chunk)
            downloaded_bytes += len_chunk
            bar(10 + downloaded_bytes/download_size*90)
    bar(100)
    del bar
    print('Successfully downloaded version information')
            
    fo.close()

print()
print('Successfully installed all necessary elements')
print()
#print('By the way, we are looking for French translators to help me translate the game and the wiki into French. To help me with the wiki, head to villagewars.fandom.com to familiarize yourself with the English wiki and prepare yourself for translating. Don\'t worry, I\'ll help too.')
print('Would you like your files to be refreshed? (Replace out-of-date files) (y/n)')
answer = input('> ').strip()[0].lower()
print()
assert answer in ('y', 'n')
if answer == 'n':
    print('Ok, you\'re ready to play VillageWars!')
if answer == 'y':
    files = [os.path.abspath('../run/screenshots/' + file) for file in os.listdir('../run/screenshots')]
    files.extend([os.path.abspath('../run/compressed/' + file) for file in os.listdir('../run/compressed')])
    files.extend([os.path.abspath('../run/downloads/' + file) for file in os.listdir('../run/downloads')])
    if len(files):
        print('You have %s files to unlink' % len(files))
    
        print()
        os.chdir('../')
        for file in files:
            print(os.path.relpath(file).replace('\\', '/'))
        os.chdir('src')
        print()
        input('Press enter to continue')
        print()
        #print('Unlinking %s files:' % len(files), end=' ')
        bar = Bar('Unlinking %s files' % len(files))
        bar(0)
        for i, file in enumerate(files):
            send2trash.send2trash(file)
            bar(((i+1)/len(files)*100))
        del bar
        print()
        print('Sucessfully refreshed your files')
    else:
        print('Nevermind, you don\'t have any files to refresh.')
        print()
        print('You\'re ready to play VillageWars!')

print()
input('Press enter to continue to VillageWars')
os.system('python -m VillageWarsClient')

