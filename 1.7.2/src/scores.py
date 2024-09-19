from flask import Flask
import shelve
try:
    import pyperclip
except:
    pass # If pyperclip is not installed, it's no big deal.

import webbrowser

app = Flask(__name__)

@app.route('/scores')
def html():
    users = shelve.open('database/data')
    final = '''<!DOCTYPEhtml>
<html>
    <head>
        <title>Scores - VillageWars</title>
    </head>
    <body>
        <script>

// TODO: Add this code.

        </script>
        <h1>VillageWars</h1>
        <h2 style="color:blue">Scores</h2>
'''

    for username in users.keys():
        final += '<h3>' + username + '''</h3>
<h4>Victories: %s</h4>
<h4>Games finished: %s</h4>
<h4>Total Kills: %s</h4>
<h4>Color: %s</h4>
<h4>Name: %s</h4>
<h4>Email: %s</h4>
<br>''' % (users[username]['victories'], users[username]['games finished'], users[username]['kills'], users[username]['color'], users[username].get('name', 'No Input'), str(users[username].get('email', None)))
    final += '''
    </body>
</html>'''
    return final

@app.route('/userdata/<username>')
def userdata(username):
    users = shelve.open('database/data')
    final = f'''<!DOCTYPEhtml>
<html>
    <head>
        <title>{username} - VillageWars</title>
    </head>
    <body>
        <script>

// TODO: Add this code.

        </script>
        <h1>VillageWars</h1>
        <h2 style="color:blue">Scores</h2>
'''

    
    final += '<h3>' + username + '''</h3>
<h4>Victories: %s</h4>
<h4>Games finished: %s</h4>
<h4>Total Kills: %s</h4>
<h4>Color: %s</h4>
<h4>Name: %s</h4>
<h4>Email: %s</h4>
<br>''' % (users[username]['victories'], users[username]['games finished'], users[username]['kills'], users[username]['color'], users[username].get('name', 'No Input'), str(users[username].get('email', None)))
    final += '''
    </body>
</html>'''
    return final

try:
    pyperclip.copy('http://127.0.0.1:5000/scores')
except:
    pass
webbrowser.open('http://127.0.0.1:5000/scores')
app.run()

