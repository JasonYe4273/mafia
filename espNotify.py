'''
ESPs can send requests to this file asking for updates on the game and their role in the game
need to include kerberos under "kerberos" in what they submit, returns statements to print separated by | at line breaks
info it returns: you are __, your role is ___, you are alive/dead
yesterday, ___ was murdered at ___, ___ was executed
Currently, there are __ people alive in the game and __ dead
ESP should request here so you don't have HTML interruptions
'''
import sqlite3


def request_handler(request):
    '''
    '''
    if request['method']=='GET':
        return handle_get(request)
    return "You can only send GET requests to this file."

def handle_get(request):
    '''
    '''
    kerberos = request['values']['kerberos']
    example_db = "__HOME__/playersT.db" # just come up with name of database
#    connect to the database
    conn = sqlite3.connect(example_db)  # connect to that database (will create if it doesn't already exist)
    c = conn.cursor()  # make cursor into database (allows us to execute commands)
    gameID = getGameID(c)
    role,status = c.execute("select role,status from rolesTe where kerberos=? and gameID=?;",(kerberos,gameID)).fetchone()
    victim,lat,lon,t = getRecentMurder(c)
    ex_time, executed = getRecentExecution(c)
    best = c.execute('''SELECT kerberos,status FROM rolesTe WHERE gameID=? ;''',(gameID,)).fetchall()
    alive = []
    dead = []
#        append the users to the list of users in a random order
    for tup in set(best):
        if tup[0]!="":
            if tup[1] == "alive":
                alive.append(tup[0])
            else:
                dead.append(tup[0])
    return "You are {}.|Your role is {}.|You are {}.|Yesterday, {} was murdered at {},{}.|{} was executed.|Currently, there are {} people alive|and {} dead.".format(kerberos,role,status,victim,lat,lon,executed,len(alive),len(dead))



def getGameID(c):
    #        Elizabeth's code to get the most up to date gameID
    try:
        gameID = c.execute('''SELECT gameID FROM playersT ORDER BY timing DESC;''').fetchone()
        gameID = int(gameID[0]) - 1
    except:
        gameID = 0;
    return gameID

def getRecentMurder(c):
    '''
    '''
    kill_info = c.execute('''SELECT * FROM killsRecord ORDER BY time DESC;''').fetchone()
    return kill_info[1],round(kill_info[5],4),round(kill_info[6],4), kill_info[3]

def getRecentExecution(c):
    '''
    '''
    c.execute('''CREATE TABLE IF NOT EXISTS executions (timing timestamp, kerberos text, gameID int);''')
    ex_info = c.execute('''SELECT * FROM executions ORDER BY timing DESC;''').fetchone()
    return ex_info[0],ex_info[1]
