import requests

import sys
sys.path.append("__HOME__/mafia")

from getStatus import HTMLHEAD, HEAD, urls

import updateGame
import newGame

#this file is a UI for joining and starting games - I will comment it later, sometime after my test

def getGameID(c):
    #        Elizabeth's code to get the most up to date gameID
    try:
        gameID = c.execute('''SELECT gameID FROM playersT ORDER BY timing DESC;''').fetchone()
        gameID = int(gameID[0])
    except:
#        print('exception')
        gameID = 0
    return gameID

def request_handler(request):
    '''
    '''
#    return request
    if request['method'] == 'GET':
        return get_handler(request)
    elif request['method'] == 'POST':
        return post_handler(request)
    return "Something is wrong with your request"


def get_handler(request):
    '''
    '''
    conn = updateGame.get_db_connection()  # connect to that database (will create if it doesn't already exist)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS playersT (timing timestamp, kerberos text, gameID int);''')
    kerberos = request['values']['kerberos']
    gameID = getGameID(c)
    out = HTMLHEAD
    out += HEAD.format(urls['home']+'?kerberos='+kerberos,"black","black",urls['home']+'?kerberos='+kerberos,urls['vote']+'?kerberos='+kerberos+'&gameID=home',urls['gamedb']+'?kerberos='+kerberos,urls['newgame']+'?kerberos='+kerberos)
    best = c.execute('''SELECT kerberos FROM playersT WHERE gameID=?;''',(gameID,)).fetchall()
    users = []
#        append the users to the list of users in a random order
    for tup in set(best):
        if tup[0]!="":
            users.append(tup[0])
    if kerberos not in users:
        out += "<p> Game {} currently has {} people waiting to start. Do you want to join game {}? </p>".format(gameID,len(users),gameID)
        out += '''<form method="POST">
                    <input type="submit" value="Join game" />
                    <input type="hidden" name="kerberos" value="{}">
                    <input type="hidden" name="start" value="False" />
                 </form>
                    '''.format(kerberos)
    else:
        out += "<p> You are waiting to join game {}, which currently has {} people waiting to start.".format(gameID,len(users),gameID)
    out += "<p> To start game {}, click the button below. </p>".format(gameID)
    out += '''<form method="POST" >
                <input type="submit" value="Start game" />
                <input type="hidden" name="kerberos" value="{}">
                <input type="hidden" name="start" value="True" />
             </form>
                '''.format(kerberos)
    out += "</body></html>"
    return out

def post_handler(request):
    '''
    '''
    kerberos = request['form']['kerberos']
    start = request['form'].get('start')
#    return requests.post(urls['newgame'], data={'kerberos':kerberos,'start':start})
#    return newGame.handle_post({'method': 'POST', 'args': ['kerberos','start'], 'form': {'kerberos': kerberos,'start':start}})
#    return requests.post(urls['new'], data={'kerberos':kerberos,'start':start}).text
#    response = requests.post(urls['new'], data={'kerberos':kerberos,'start':start})
    response = newGame.handle_post({'method': 'POST', 'args': ['kerberos','start'], 'form': {'kerberos': kerberos,'start':start}})
#    return requests.post(urls['new'], data={'kerberos':kerberos,'start':start}).text
    if start == 'True':
        start = True
    else:
        start = False
    
    out = HTMLHEAD
    out += HEAD.format(urls['home']+'?kerberos='+kerberos,"black","black",urls['home']+'?kerberos='+kerberos,urls['vote']+'?kerberos='+kerberos+'&gameID=home',urls['gamedb']+'?kerberos='+kerberos,urls['newgame']+'?kerberos='+kerberos)
#        append the users to the list of users in a random order
    out += response
    if not start:
        out += "<p> To start the game, click the button below. </p>"
        out += '''<form method="POST" >
                    <input type="submit" value="Start game" />
                    <input type="hidden" name="kerberos" value="{}">
                    <input type="hidden" name="start" value="True" />
                 </form>
                    '''.format(kerberos)
        out += """ </body> </html>"""
    return out
