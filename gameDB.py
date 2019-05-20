import requests
import time
import datetime
import sys
sys.path.append("__HOME__/mafia")
import updateGame

from getStatus import HTMLHEAD, HEAD, urls




mafia = set('mafia')


no_games = """<br><iframe src="https://giphy.com/embed/3o72EYJlAzeSIupF16" width="480" height="270" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><br><br>"""
win_games = """<br><iframe src="https://giphy.com/embed/3o6vY7UsuMPx3Yj9Xa" width="480" height="240" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><br><br>"""
def request_handler(request):
    if request['method']=="POST":
        print('posting request')
        return handle_post(request)
    if request['method']=='GET':
        return handle_get(request)
    return "there was an error with your request(needs to be get or post)"



#each player will report if they won or lost(based on outcome and role)
#from postman request is: http://608dev.net/sandbox/sc/kms20/gameDB.py
#in body put kerberos: example_kerb and win: True or False(True if you won the game False otherwise)
def handle_post(request):
    print(request)
    if 'kerberos' in request['form'] and 'win' in request['form']:
        kerberos = request['form']['kerberos']
        add = 0
        if request['form']['win']=='True':
            add = 1
            conn = updateGame.get_db_connection()
            c = conn.cursor()  # make cursor into database (allows us to execute commands)
            def add_stats(kerberos, add, c):
                c.execute('''CREATE TABLE IF NOT EXISTS statsT (kerberos text, wins int, games int);''') # run a CREATE TABLE command
                try:
                    wins,games = c.execute('''SELECT wins,games FROM statsT WHERE kerberos=?;''',(kerberos,)).fetchone()
                    c.execute('''UPDATE statsT SET wins=?, games=? WHERE kerberos=?;''',(wins+add,games+1,kerberos)) #with time
                except:
                    wins=0
                    games = 0
                    c.execute('''INSERT into statsT VALUES (?,?,?);''',(kerberos, add,1)) #with time

                return "Win Percentage: " + str(wins+add)+"/"+str(games+1)
            add_stats(kerberos, add, c)
            conn.commit()
            conn.close()
        else:
            return "invalid request"


#get the stats for player with the given kerberos
#from postman request is http://608dev.net/sandbox/sc/kms20/gameDB.py?kerberos=kms20
#in above example kms20 is kerb for player stats
def handle_get(request):

    conn = updateGame.get_db_connection()
    c = conn.cursor()  # make cursor into database (allows us to execute commands)
    kerberos = request['values']['kerberos']
    gameID = c.execute('''SELECT gameID from playersT WHERE kerberos=? ORDER BY gameID DESC;''',(kerberos,)).fetchone()
    if not gameID:
        gameID = 0
    else:
        gameID = gameID[0]
    out1 = HTMLHEAD
    out1 += HEAD.format(urls['home']+'?kerberos='+kerberos,"black","black",urls['home']+'?kerberos='+kerberos,urls['vote']+'?kerberos='+kerberos+'&gameID=home',urls['gamedb']+'?kerberos='+kerberos,urls['newgame']+'?kerberos='+kerberos)


    c.execute('''CREATE TABLE IF NOT EXISTS statsT (kerberos text, wins int, games int);''') # run a CREATE TABLE command
    try:
        wins,games = c.execute('''SELECT wins,games FROM statsT WHERE kerberos=?;''',(kerberos,)).fetchone()
        out1 += '<body bgcolor = {}>Hi, {}! You have won {}/{} games.'.format('#EBF5FB',kerberos,wins,games) + win_games

    except:
        out1 += '<body bgcolor = {}>Hi, {}! You have not played any games!'.format('#EBF5FB',kerberos) + no_games
    conn.commit()
    conn.close()
    out1 += """</font></body> </html> """
    return out1
