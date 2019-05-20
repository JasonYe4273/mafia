import requests
import time
import datetime
import random
import os
import sys
sys.path.append("__HOME__/mafia")
import updateGame

#collect user who wish to play a game
#have ability to start game
#users need to have posted within the past 5 minutes to be included in the game
#form needs to have kerberos in it and start in it

#roles dict is a list of the possible roles in the game and a description that is returned to
#role percentage is the percentage of players that we want to have this role the rest are citizens
roles_dict={'citizen':'description of citizen', 'mafia':'description of mafia', 'detective': 'description of detective'}
role_percent = {'mafia':.25,'detective':1/5,'doctor':.1,'priest':.1,'secret admirer':.1}
mafia = ['mafia']
#number of minutes before that players will be added
COLLECT_PLAYER_TIME = 5
NUM_TO_DOCTOR = 10
TIME_PER_DAY = datetime.timedelta(minutes = 2)

port = 465  # For SSL
smtp_server = "smtp.gmail.com"
sender_email = "mitmafia608@gmail.com"  # Enter your address
password = "608design"
receiver_email = 'kms20@mit.edu'
#just splits post and get for cleaner code
def request_handler(request):
#    print(request['method'])
    if request['method']=='POST':
        return handle_post(request)
    if request['method']=='GET':
        return handle_get(request)
    return "there was an error with your request needs to be get or post"

#creates the actual game when a post request with start=True comes in
def create_game(users, gameID,cursor):
#    this function takes in a cursor now bc it was having problems when I ran it, since it was opening a new cursor and wouldn't interact correctly
#    added this line to use the passed in cursor
    c = cursor
#    return 'testing'
    c.execute('''CREATE TABLE IF NOT EXISTS rolesTe (kerberos text, gameID int, role text, status text);''') # run a CREATE TABLE command
    
    updateGame.execute_command("new_game {}".format(gameID),gameID=gameID)
    c.execute('''CREATE TABLE IF NOT EXISTS votesTiming (timing timestamp, gameID int);''') # run a CREATE TABLE command
    c.execute('''INSERT into votesTiming VALUES (?,?);''',(datetime.datetime.now(), gameID))

    user_len = len(users)
    roles = []
#    print(users)
    random.shuffle(users)
#    print(users)
    for role in role_percent:
        count=0
#        floor of the role percents time number of users - added = so that if we have 5 players, we still get 1 detecive/2 mafia
#        I think Josh wanted to not have detective and mafia be mutually exclusive but maybe we can talk about that later
        while count < int(role_percent[role]*user_len):
            roles.append(role)
            count+=1
#    if user_len >= NUM_TO_DOCTOR:
#        roles.append('doctor')
    while len(roles)<user_len:
        roles.append('citizen')
    if user_len == 6:
        roles = ['mafia','detective','priest','secret admirer','doctor','citizen']
    for index in range(user_len):
        c.execute('''INSERT into rolesTe VALUES (?,?,?,?);''',(users[index], gameID, roles[index],'alive')) #with time
        role = roles[index] if roles[index]!="secret admirer" else "sa"
        updateGame.execute_command("role {} {}".format(users[index], role),gameID=gameID)
        if roles[index] == "mafia":
            updateGame.execute_command("alignment {} {}".format(users[index], role),gameID=gameID)
    best = c.execute('''SELECT kerberos,role FROM rolesTe WHERE gameID=?;''',(gameID,)).fetchall()




def add_player(timing, kerberos, gameID, c):
    while True:
        espID = bin(random.getrandbits(5))[2:]
        #            print(espID)
        while len(espID) < 5:
            espID = '0' + espID
            espID = '1' + espID + '1'
        sameIDs = c.execute('''SELECT * FROM playersT WHERE espID=? and gameID=?;''', (espID, gameID)).fetchall()
        if not sameIDs:
            break
    c.execute("delete from playersT where kerberos = ? and gameID = ?",(kerberos, gameID))
    c.execute('''INSERT into playersT VALUES (?,?,?,?);''',(timing, kerberos, gameID,espID)) #with time    
            
#allows player to join the current game that is collecting players(only players which clicked in the last time period)
#request: http://608dev.net/sandbox/sc/kms20/newGame.py
#in form put kerberos: example_kerb and start: True/False(True if you would like to start the current game false otherwise)
def handle_post(request):
    conn = updateGame.get_db_connection()
    c = conn.cursor()  # make cursor into database (allows us to execute commands)
    c.execute('''CREATE TABLE IF NOT EXISTS playersT (timing timestamp, kerberos text, gameID int, espID text);''') # run a CREATE TABLE command

    
    gameID = request['form'].get('gameID')
    
    roles = 0
    start = False
    if 'kerberos' in request['form'] and 'start' in request['form']:
        
        kerberos = request['form']['kerberos']
        start = True if request['form']['start']=='True' else False
        try:
            gameID = c.execute('''SELECT gameID FROM playersT ORDER BY timing DESC;''').fetchone()
            gameID = int(gameID[0])
#            print(gameID)
        except:
             gameID = 0
        add_player(datetime.datetime.now(), kerberos, gameID, c)
#        if start:
#        I edited this part so that it finds the current number of users with each post request and only creates a new game at start
        minutes5_ago = datetime.datetime.now()- datetime.timedelta(minutes = COLLECT_PLAYER_TIME)
        best = c.execute('''SELECT kerberos FROM playersT WHERE gameID=? AND timing>?;''',(gameID, minutes5_ago)).fetchall()
#        print(best)
        users = []
#        append the users to the list of users in a random order
        
        for tup in set(best):
            if tup[0]!="":
                users.append(tup[0])
        
        extra = "Push start when ready."
        if start:
            

#            c.execute('''INSERT into playersT VALUES (?,?,?,?);''',(datetime.datetime.now(), "", gameID+1,"")) #with time

            
            c.execute('''CREATE TABLE IF NOT EXISTS votesTiming (timing timestamp, gameID int);''')
            
            c.execute('''INSERT into votesTiming VALUES (?,?);''',(datetime.datetime.now(), gameID+1)) #with time
            
            extra = "Game is started!"
#            conn.commit() # commit commands
#            conn.close()
#            print('creating game')
            
            create_game(users, gameID,c)
            c.execute('''INSERT into playersT VALUES (?,?,?,?);''',(datetime.datetime.now(), "", gameID+1,0)) #with time
        
#        if not start:
#        return request
        conn.commit()
        
        conn.close()

        return 'Game ID is {}. There are currently {} people in the game. {}'.format(gameID, len(users),extra)
    return 'You must specify a user and whether or not to start the game.'

#after posting players recieve gameID and send get requests to recieve their role and description
#until the game starts they get a message stating waiting for game to start
#request: http://608dev.net/sandbox/sc/kms20/newGame.py?kerberos=kms20&gameID=8
#game idea is returned by post request=
def handle_get(request):
    if 'kerberos' in request['args'] and 'gameID' in request['args']:
        gameID = request['values']['gameID']
        kerberos = request['values']['kerberos']
        conn = updateGame.get_db_connection()
        c = conn.cursor()  # make cursor into database (allows us to execute commands)
        c.execute('''CREATE TABLE IF NOT EXISTS rolesTe (kerberos text, gameID int, role text, status text);''') # run a CREATE TABLE command
        role = c.execute('''SELECT role FROM rolesTe WHERE gameID=? and kerberos=?;''',(gameID,kerberos)).fetchone()
        if role is None:
            return "0 waiting for game to start ..."
        info = str(1) + " " + str(role[0]) + ': ' + roles_dict[role[0]]
        return info
    return "there was an issue with your request"
