import requests
import time
import datetime
import random
import shlex
import smtplib, ssl
import random
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


import sys
sys.path.append("__HOME__/mafia")

#to update urls, update base_folder in getStatus


from getStatus import HTMLHEAD, HEAD, urls


import updateGame


'''I made it so that it posts automatically, but it goes to my URL rn and prob has to be fixed for whoever is hosting it
'''

TIME_PER_DAY = datetime.timedelta(minutes=1)

VOTING_PERIOD = datetime.timedelta(minutes = 1)
mafia = ['mafia']

fontcolor = 'black'
def request_handler(request):
    if request['method']=="POST":
        return handle_post(request)
    if request['method']=='GET':
        return handle_get(request)
    return "there was an error with your request(needs to be get or post)"

def handle_get(request):
    kerberos = request['values']['kerberos']
    gameID = request['values']['gameID']

    out = HTMLHEAD
    out += HEAD.format(urls['home']+'?kerberos='+kerberos,"black","black",urls['home']+'?kerberos='+kerberos,urls['vote']+'?kerberos='+kerberos+'&gameID=home',urls['gamedb']+'?kerberos='+kerberos,urls['newgame']+'?kerberos='+kerberos)
    out += """<iframe src="https://giphy.com/embed/l2SpWPGLYJK94yY00" width="480" height="270" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><br><br>"""
    out += '<body bgcolor = {}>Hi, {}! Here are the current votes for today.'.format('white',kerberos)

    try:
        gameID = int(gameID)
    except:
        gameID = None


    out += '<br>'

    conn = updateGame.get_db_connection()
    c = conn.cursor()  # make cursor into database (allows us to execute commands)
    c.execute('''CREATE TABLE IF NOT EXISTS votes (timing timestamp, kerberos text, gameID int, vote text);''')
    if type(gameID) == int:
#        send_updates(str(gameID), c)
        last_time = c.execute('''SELECT timing FROM votes WHERE gameID=? AND kerberos=? ORDER BY timing DESC;''',(gameID, 'last voting period')).fetchone()
        best = c.execute('''SELECT kerberos FROM rolesTe WHERE gameID=? AND status=?;''',(gameID, 'alive')).fetchall()
        users = []
        for tup in set(best):
            if tup[0]!="":
                users.append(tup[0])

        if last_time:
            start = last_time[0]
        else:
            start = 0

        end = datetime.datetime.now()
        for voter in users:
            d=eval(c.execute("select artifact_data from inventory where game_id = ? and owner = ? and artifact = 'vote'",(gameID, voter)).fetchone()[0])
            vote = (d['vote'],) if 'vote' in d else None
            #vote = c.execute('''SELECT vote FROM votes WHERE gameID=? AND timing>? AND timing<? AND kerberos=? ORDER BY timing DESC;''',(gameID, start, end, voter)).fetchone()
            if vote is not None:
                vote = vote[0]
                out += voter + " voted for " + vote + "<br>"
    else:
        out += '<p> Please select a game to see current votes. </p>'
        out += '<ul>'
        games = c.execute('''SELECT gameID FROM playersT WHERE kerberos=?;''',(kerberos,)).fetchall()
        games = [str(x[0]) for x in games]
        games = list(dict.fromkeys(games))
        c.execute('''CREATE TABLE IF NOT EXISTS finishedGames (gameID int);''')
        old_games = c.execute('''SELECT gameID FROM finishedGames;''').fetchall()
        old_games = [str(x[0]) for x in old_games]
        for game in games:
            if game not in old_games:
                out += '<li><a href="{}"> Game: {} </a> </li>'.format(urls['vote']+'?kerberos='+kerberos+'&gameID='+game,game)
        out += "</ul> </body> </html> "
    out += """</font></body> </html> """
    return out

def handle_post(request):
    to_return = "no dead"
    conn = updateGame.get_db_connection()
    c = conn.cursor()  # make cursor into database (allows us to execute commands)
    c.execute('''CREATE TABLE IF NOT EXISTS finishedGames (gameID int);''') # run a CREATE TABLE command
    finished_games = c.execute('''SELECT gameID from finishedGames''').fetchall()
    finished_games = [x[0] for x in finished_games]
#    print(finished_games)
    if 'kerberos' in request['form'] and 'vote' in request['form'] and 'gameID' in request['form']:
        c.execute('''CREATE TABLE IF NOT EXISTS votes (timing timestamp, kerberos text, gameID int, vote text);''') # run a CREATE TABLE command
        kerberos = request['form']['kerberos']
        vote = request['form']['vote']
        gameID = request['form']['gameID']
        dead = c.execute('''SELECT kerberos FROM rolesTe WHERE status!="alive";''').fetchall()
        dead = [x[0] for x in dead]
#        send_updates(gameID, c)
        if vote == kerberos:
            return "You cannot vote for yourself."
        elif vote in dead:
            return "You cannot vote for dead people."
        if int(gameID) in finished_games:
            return 'This game has terminated.'
        alive = c.execute('''SELECT kerberos FROM rolesTe WHERE gameID=? AND status="alive";''',(gameID,)).fetchall()
        alive = [x[0] for x in alive]
        if kerberos not in alive:
            return "Sorry, you must be a current, living member of the game to vote."
        c.execute('''INSERT into votes VALUES (?,?,?,?);''',(datetime.datetime.now(), kerberos, gameID, vote)) #with time
        conn.commit()
        to_return = "You successfully voted for {}.".format(vote,)
    if 'end_voting' in request['form'] and 'gameID' in request['form']:
        
        c.execute('''CREATE TABLE IF NOT EXISTS executions (timing timestamp, kerberos text, gameID int);''')
        if request['form']['end_voting'] == 'True':
            gameID = int(request['form']['gameID'])
            if gameID in finished_games:
                return 'This game has terminated.'
            store = end_voting(gameID, c)
#            return store
            c.execute('''INSERT into votes VALUES (?,?,?,?);''',(datetime.datetime.now(), "last voting period", gameID, "")) #with time
            if store != None:
                c.execute('''UPDATE rolesTe SET status = "executed" WHERE kerberos = ? AND gameID = ?''',(store,gameID))
                c.execute('''INSERT into executions VALUES (?,?,?);''',(datetime.datetime.now(),store,gameID))
                return None
                conn.commit()
                all_players = c.execute('''SELECT role,kerberos,status FROM rolesTe WHERE gameID=? ;''',(gameID,)).fetchall()
                alive_roles = []
                dead = []
            #        append the users to the list of users in a random order
                for tup in set(all_players):
                    if tup[0]!="":
                        if tup[2] != "dead" and tup[2]!="executed":
                            alive_roles.append(tup[0])
                        else:
                            dead.append(tup[0])
                others_alive = [x for x in alive_roles if x != 'mafia']
                if 'mafia' not in alive_roles:
                    
                    print('citizens win')
                    for player in all_players:
                        role = player[0]
                        kerb = player[1]
                        win = 'True'
                        if role == 'mafia':
                            win = 'False'
#                        return kerberos
                        gameDB_post({'method': 'POST', 'args': ['kerberos','start'], 'form': {'kerberos': kerb,'win':win}},c)
#                        requests.post(urls['gamedb'],data={'kerberos':kerb,'win':win})
#                        return gameID
#                        print(test.text)
                    c.execute('''INSERT into finishedGames VALUES (?);''',(gameID,))
                    conn.commit()
                elif not others_alive:
                    print('mafia win')
                    for player in all_players:
                        role = player[0]
                        kerb = player[1]
                        win = 'True'
                        if role != 'mafia':
                            win = 'False'
                        gameDB_post({'method': 'POST', 'args': ['kerberos','start'], 'form': {'kerberos': kerb,'win':win}},c)
#                        test = requests.post(urls['gamedb'],data={'kerberos':kerb,'win':win})
#                        print(test.text)
#                    return all_players
                    c.execute('''INSERT into finishedGames VALUES (?);''',(gameID,))
                    conn.commit()
#                        return kerb,win
#                now need to mark the game as done so people don't try to post a bunch of times after the game is done
                to_return = store + " died"
    
    conn.commit()
    conn.close()
    return to_return

def end_voting(gameID, cursor, potential=None, days_ago=0):
    c = cursor
    best = c.execute('''SELECT kerberos FROM rolesTe WHERE gameID=? AND status=?;''',(gameID, 'alive')).fetchall()
    users = []
#        append the users to the list of users in a random order
    for tup in set(best):
        if tup[0]!="":
            users.append(tup[0])
    dead_dict = {}
    if potential is None:
        potential = users
    for player in potential:
        dead_dict[player] = 0
    max_ = 0
    start = datetime.datetime.now()-(VOTING_PERIOD*(days_ago+1))
    end = datetime.datetime.now()-(VOTING_PERIOD*days_ago)
    dead = []
    for voter in users:
        vote = c.execute('''SELECT vote FROM votes WHERE gameID=? AND timing>? AND timing<? AND kerberos=? ORDER BY timing DESC;''',(gameID, start, end, voter)).fetchone()
        if vote is not None:
            vote = vote[0]
        else:
            vote = voter
        if vote in dead_dict:
            dead_dict[vote] += 1
            if dead == [] or dead_dict[vote]>max_:
                dead = [vote]
                max_ = dead_dict[vote]
            elif dead_dict[vote]==max_:
                dead.append(vote)

#    return dead_dict,dead
    if len(dead)==1:
        return dead[0]
    elif len(dead)>1:
        prev_most = end_voting(gameID, cursor, dead, days_ago+1)
        if prev_most != None:
            return prev_most
        else:
            return dead[0]

def gameDB_post(request,c):
    if 'kerberos' in request['form'] and 'win' in request['form']:
        kerberos = request['form']['kerberos']
        add = 0
        if request['form']['win']=='True':
            add = 1
  # make cursor into database (allows us to execute commands)
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

        else:
            return "invalid request"

#    return "Win Percentage: " + str(wins+add)+"/"+str(games+1)
