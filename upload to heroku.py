import os
import sys

if __name__ == '__main__':
    os.system('git add .')
    os.system('git commit -m "%s"' % input('Commit name: '))
    os.system('git push -u origin master')
    os.system('git push heroku')
    os.system('heroku logs --tail --app water-warzone')
