
import sys
sys.path.append("__HOME__/mafia")

from getStatus import HTMLHEAD, HEAD, urls

import updateGame

def request_handler(request):
    '''
    '''
    if request['method'] == 'GET':
        return get_handler(request)
    return "Sorry, you can only do GET requests with this page."


def get_handler(request):
    '''
    '''
    conn = updateGame.get_db_connection()  # connect to that database (will create if it doesn't already exist)
    c = conn.cursor()
    kerberos = request['values']['kerberos']
#    use the name of the database that has been used in other places (might not end up in the folder with the current script)
#    connect to the database

    c.execute('''CREATE TABLE IF NOT EXISTS playersT (timing timestamp, kerberos text, gameID int, espID text);''')
    c.execute('''CREATE TABLE IF NOT EXISTS votesTiming (timing timestamp, gameID int);''')
    c.execute('''CREATE TABLE IF NOT EXISTS rolesTe (kerberos text, gameID int, role text, status text);''')
    kerberos = request['values']['kerberos']
    games = c.execute('''SELECT gameID FROM playersT WHERE kerberos=?;''',(kerberos,)).fetchall()
    games = [str(x[0]) for x in games]
    games = list(dict.fromkeys(games))
    
    out = HTMLHEAD
    out += HEAD.format(urls['home']+'?kerberos='+kerberos,"black","black",urls['home']+'?kerberos='+kerberos,urls['vote']+'?kerberos='+kerberos+'&gameID=home',urls['gamedb']+'?kerberos='+kerberos,urls['newgame']+'?kerberos='+kerberos)
    out += """<p>
               Hi, {}! Here are the games you are currently a part of:
            </p>
            <ul>
            """.format(kerberos)
    c.execute('''CREATE TABLE IF NOT EXISTS finishedGames (gameID int);''')
    old_games = c.execute('''SELECT gameID FROM finishedGames;''').fetchall()
    old_games = [str(x[0]) for x in old_games]
    new_list = ''
    old_list = ''
    for game in games:
        if game not in old_games:
            new_list += '<li><a href="{}"> Game: {} </a> </li>'.format(urls['status']+'?kerberos='+kerberos+'&gameID='+game,game)
        else:
            old_list += '<li><a href="{}"> Game: {} </a> </li>'.format(urls['status']+'?kerberos='+kerberos+'&gameID='+game,game)
    out += new_list + '</ul> <br> <br> Old games: <ul>' + old_list
    out += "</ul> </body> </html>  "

    return out
