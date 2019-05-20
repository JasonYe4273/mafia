import requests
import datetime
import numpy as np

import sys
sys.path.append("__HOME__/mafia")
import updateGame

SAVE_TIME = 50
#change this to update urls on all files
base_folder = 'https://608dev.net/sandbox/sc/brunnerj/mafia/'
NEW = base_folder + "newGame.py"
VOTE_URL = base_folder + "voting.py"
GAMEDB = base_folder  + "gameDB.py"
UPDATE_URL = base_folder + 'updateGame.py'
KILLID_URL = base_folder + 'killerID.py'
NEWGAME_URL = base_folder + 'joinGame.py'
HOME_URL = base_folder + 'home.py'
STATUS_URL = base_folder+ "getStatus.py"

PRIEST_PERCENT = .1

"""
this file handles requests to getStatus.py to learn more about a player's status
it lets you know if you're alive or dead, what your role is, and who else is playing and if they are alive or dead

"""
#selected gifs and background colors for each role


urls = {'new':NEW,'vote':VOTE_URL,'gamedb':GAMEDB,'update':UPDATE_URL,'killid':KILLID_URL,'newgame':NEWGAME_URL,'home':HOME_URL,'status':STATUS_URL}
'''location info gotten from: https://stackoverflow.com/questions/45630606/can-i-get-accurate-geolocation-in-python-using-html5-location-tool'''
gifs = {'detective': """<br><br> <iframe src="https://giphy.com/embed/2tRoKSKZHYpWvPo9TQ" width="480" height="353" frameBorder="0" class="giphy-embed" allowFullScreen></iframe> <br><br>""",
        'mafia': """<br><br> <iframe src="https://giphy.com/embed/3o7btOHBo4Be8Io9IQ" width="480" height="270" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><br><br>""",
        'citizen': """<br><br> <iframe src="https://giphy.com/embed/xUNd9QJeoYNzecQ1KU" width="480" height="270" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><br><br>""",
        'doctor':""" <br><br> <iframe src="https://giphy.com/embed/9Ai5dIk8xvBm0" width="480" height="399" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><br> <br>""",
        'dead':"""<br><br> <iframe src="https://giphy.com/embed/zEbDFvxxPSPcI" width="480" height="271" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><br><br>""",
        'executed':"""<br><br> <iframe src="https://giphy.com/embed/P43lFJyUBMBna" width="480" height="362" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><br><br>""",
        'secret admirer': """<br><br><iframe src="https://giphy.com/embed/wOfmYO0pFGpDa" width="480" height="480" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><br><br>""",
        'priest': """<br><br><iframe src="https://giphy.com/embed/xUA7aQKbl8jk3htphS" width="480" height="466" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><br><br> """
        }
colors = {'detective':'#D4EFDF',
          'citizen': '#EBF5FB',
          'mafia': 'black',
          'doctor': '#edc98b',
          'dead':'#FDFEFE',
          'secret admirer': '#FC9DCB',
          'priest':'white'
        }

message_dict = {'dead':'have died',
                'executed': 'have been executed'

        }

location_script = '''
<script>
var x = document.getElementById("demo");

function getLocation() {
  console.log("in");

  var count = 0;
  while (1) {
      console.log(navigator.geolocation);
      if (navigator.geolocation) {
        console.log("present!")
        navigator.geolocation.getCurrentPosition(showPosition,errorTaker,{maximumAge:0, timeout:10000000, enableHighAccuracy:false});
        break;
      } else {

      }

  }
}
function donothing() {


}

function showPosition(position) {
  console.log("trying");
 document.getElementById('placeField').value =  position.coords.latitude + "|" + position.coords.longitude;
 document.getElementById("mafia").submit();

}
function errorTaker(pos){
    console.log("fail");
    x.innerHTML = "Fail";
}
</script>
'''
HTMLHEAD = """<html> <head> <link rel="icon" type = "image/jpg" href = "http://clipart-library.com/img/1762322.jpg" />
            <title>  Mafia </title> 
            <style>
            body {
                font-family: Arial;
                margin: 15px 100px 100px 100px;
            }
            ul.menu {
                list-style-type: none;
                margin: 0;
                padding: 10px;
                overflow: auto;
                table-layout: fixed;
                background-color: #b7b7b7;
                width: 100%;
            }
            li.menu {
                float: left;
            }
            li.menu a {
                display: block;
                padding: 8px;
                background-color: #b7b7b7;
                text-align: center;
                text-decoration: none;
            }
            li a:hover {
                background-color: #919191;
            }
            .active {
                background-color: #caebf7;
            }    
            
            a {
                text-decoration: none;
            }
            * {
                box-sizing: border-box;
            }
            
            .column {
                float: "left";
                width: 50%;
                padding: 10px;
            }
            
            .row:after {
                content: "";
                display: table;
                clear: both;
            }
                
            </style>            
            </head>"""

HEAD = """ <h1> <a href="{}"><font style="font-size: 55px" color={}> 
                    Welcome to live action mafia! </font> </a> </h1>
                    <font color = {}>
                    
                    <ul class="menu">
                        <li> <a> </a></li>
                        <li class="menu"><a href="{}"> Home </a> </li>
                        <li class="menu"><a href="{}"> Current votes </a> </li>
                        <li class="menu"><a href="{}"> Current record </a> </li>
                        <li class="menu"><a href="{}"> Join a new game </a> </li>
                    </ul>
                    <br> <br>

                    """
INTRO = '''<body bgcolor = {}>
                            Currently viewing game {} <br>
                        Hi, {}! You are currently alive and your role is {}.

                '''
VOTINGFORM = '''<form method = "POST"> Who would you like to execute?: <input type = "text" name ="vote">
                            <input type = "hidden" name = "gameID" value ="{}"/>
                          <input type ="submit"  value = "submit"> <br>
                        </form>'''

NOTSTARTED = ''' Sorry, game {} has not started yet. Roles will be assigned at start.
                       <br> There are currently {} people in the game. If you would like to start the game, click here.
                        <form method="POST">
                        <input type="hidden" name="startgame" value="True">
                        <input type="hidden" name="kerberos" value="{}">
                        <input type="hidden" name="gameID" value="{}">
                        <input type="hidden" name="start" value="True" />
                        <input type="submit" value="Start game" />
                        </form>
                '''
MAFIA_ACT = '''<form method = "POST" id = "mafia"> Who would you like to kill?: <input type = "text" name ="victim"/>
                               <input type = "hidden" name = "place" id = "placeField" value = ''/>
                              ''' + location_script
MAFIA_ACT2 = '''<input type = "hidden" name = "gameID" value ="{}"/>
                            </form> <button onclick="getLocation()">Log a kill!</button>  <br>  <br>  <br> '''


DETECTIVE_ACT = '''<form method="POST" > Who would you like to investigate? <br>
                                <input type="text" name="suspect1"/>
                               <input type="text" name="suspect2"/> <br>
                               Victim: <input type="text" name="victim"/>
                               <input type = "hidden" name = "gameID" value ="{}"/>
                               <input type="submit" value="submit"/>
                            </form>  <br>  <br>  <br> '''

PRIEST_ACT = '''<form method="POST">
                              <input type="hidden" name="action" value="" />
                              <input type="hidden" name="gameID" value="{}" />
                              Who are the saints? <br>
                   '''
                   
SA_ACT = '''<form method="POST">
                              <input type="hidden" name="action" value="sa_invest" />
                              <input type="hidden" name="gameID" value="{}" />
                              You object of admiration has died. Who would you like to kill? <br>'''                   

DOCTOR_ACT = '''<p>{} has been murdered at {},{}.
                                        Go save them!! </p>
                                        <form method="POST" id="mafia">
                                        <input type="hidden" name="victim" value="{}"/>
                                        <input type="hidden" name="kerberos" value="{}"/>
                                        <input type = "hidden" name = "gameID" value ="{}"/>
                                    <input type="hidden" name="place" id="placeField" value = ""/>
                                    ''' + location_script + '''
                                    </form> <button onclick="getLocation()">Save them!</button>  <br>  <br>  <br> '''

def request_handler(request):
    '''initial request handler
    decides if the type is right and passes to handle_get if it is
    '''
    if request['method']=='GET':
        return handle_get(request)
    if request['method'] == 'POST':
        return handle_post(request)
    return "There was an error with your request."
    return "There was an error with your request. Status requests must be GET"



def handle_get(request):
    '''figures out if the player submitted is in the current game
    if they are playing, displays information about their role and who else is still in the game
    also adds buttons for sending requests
    '''

#    connect to the database
    conn = updateGame.get_db_connection()
    c = conn.cursor()  # make cursor into database (allows us to execute commands)
#        got the current game ID using Elizabeth's method from newGame
    try:
        gameID = c.execute('''SELECT gameID FROM playersT ORDER BY timing DESC;''').fetchone()
        gameID = int(gameID[0])-1
    except:
        gameID = 0;
    if request['values'].get('gameID'):
        gameID = request['values']['gameID']
    c.execute('''CREATE TABLE IF NOT EXISTS rolesTe (kerberos text, gameID int, role text, status text);''')
    all_players = c.execute('''SELECT role,kerberos,status FROM rolesTe WHERE gameID=? ;''',(gameID,)).fetchall()
    alive_roles = []
    for tup in set(all_players):
        if tup[0]!="":
            if tup[2] == "alive":
                alive_roles.append(tup[0])
#    start the html output
    out = HTMLHEAD
#    use the name of the database that has been used in other places (might not end up in the folder with the current script)
    
    c.execute('''CREATE TABLE IF NOT EXISTS finishedGames (gameID int);''')
    finished_games = c.execute('''SELECT gameID from finishedGames''').fetchall()
    finished_games = [x[0] for x in finished_games]
#    for now no login required
#    check if they submitted a kerb to check on
    if 'kerberos' in request['values']:
        kerberos = request['values']['kerberos']
#        make sure the tables you need exist so you don't get errors later
#        c.execute('''CREATE TABLE IF NOT EXISTS rolesTe (kerberos text, gameID int, role text, status text);''') # run a CREATE TABLE command
        c.execute('''CREATE TABLE IF NOT EXISTS playersT (timing timestamp, kerberos text, gameID int, espID text);''')

#        assumes they only have one entry with this kerberos
#        get the roles of all the people in the current game
        roles = c.execute('''SELECT status,role,kerberos FROM rolesTe WHERE gameID=?;''',(gameID,)).fetchall()

#        keep track of the people you're not looking for
        other_roles = []
        role = None
#        check if this kerb is in the current game; also keep track of the other players
        for rol in roles:
            if rol[2] == kerberos:
                status = rol[0]
                role = rol[1]
            else:
                other_roles.append((rol[0],rol[2],rol[1]))
#        if the person isn't playing, let them know
        if not role:
            games = c.execute('''SELECT gameID FROM playersT WHERE kerberos=?;''',(kerberos,)).fetchall()
            games = [x[0] for x in games]
            if int(gameID) not in games:
                conn.commit()
                conn.close()
                return 'Sorry, {} is not in game {}.'.format(kerberos,gameID)
        if role == 'secret' or role == 'sa':
            role = 'secret admirer'
            
#        font color will be white only if the background is black, which is for mafia only
        if not role or status == 'dead' or status == 'executed' or role != 'mafia':
            fontcolor = 'black'
        else:
            fontcolor = "white"

#        add on the heading which should be large and say welcome to the game

        out += HEAD.format(urls['home']+'?kerberos='+kerberos,fontcolor,fontcolor,HOME_URL+'?kerberos='+kerberos,VOTE_URL+'?kerberos='+kerberos+'&gameID='+str(gameID),GAMEDB+'?kerberos='+kerberos,NEWGAME_URL+'?kerberos='+kerberos)
        best = c.execute('''SELECT kerberos FROM playersT WHERE gameID=?;''',(gameID, )).fetchall()
        users = []
#        append the users to the list of users in a random order
        for tup in set(best):
            if tup[0]!="":
                users.append(tup[0])
        if not role:
            out += NOTSTARTED.format(gameID,len(users),kerberos,gameID)
            out += """</font></body> </html> """
            conn.commit()
            conn.close
            return out

        out += '<div class="row"> <div class="column">'
#        check if the person is alive, because then the result will depend on the role
        if status == 'alive':
            color = colors.get(role)
            if not color:
                color = 'white'
            out += INTRO.format(color,gameID,kerberos,role)
            if role in gifs:
                message  = updateGame.execute_command("show_log {}".format(kerberos),gameID=gameID)
                
                if message:
                    message_list = message.split('\n')
                    out += '<ul>'
                    for message in message_list:
                        out += '<li>' + message + '</li>'
                    out += '</ul>'
#                out += str(message)

                
            if int(gameID) not in finished_games:
#                out += str(finished_games)
                if role == 'mafia':
    #                give them a kill option if they're a mafia member
                    out += MAFIA_ACT + MAFIA_ACT2.format(gameID)
    #            give them an investigate option if they're a detective
                elif role == 'detective':
                    out += DETECTIVE_ACT.format(gameID)

    #            give them a save ability if they're a doctor and someone has been killed recently
                elif role == 'doctor':
                    c.execute('''CREATE TABLE IF NOT EXISTS killsRecord (killer text, victim text, gameID int, time timestamp,date text,lat float, lon float);''')
                    c.execute('''SELECT * FROM killsRecord ORDER BY time DESC;''').fetchone()
    #                check for the most recent kill
                    kill_info = c.execute('''SELECT * FROM killsRecord ORDER BY time DESC;''').fetchone()
    #                check if there even was a kill
                    if kill_info != None:
                        dead_status = c.execute('''SELECT status FROM rolesTe WHERE kerberos=?;''',(kill_info[1],)).fetchone()[0]
#                        print(dead_status)
    #                    check the time of the most recent kill
                        kill_time = datetime.datetime.strptime(kill_info[3],'%Y-%m-%d %H:%M:%S.%f')
                        minutes_since_kill = (datetime.datetime.now() - kill_time).total_seconds()/60
    #                    if the kill has happened recently enough, give a save option
                        if minutes_since_kill < SAVE_TIME and dead_status != 'alive':
#                            out += DOCTOR_ACT.format(kill_info[1],round(kill_info[5],4),round(kill_info[6],4),kill_info[1],kerberos,gameID)
                            out += '''<p>{} has been murdered at {},{}.'''.format(kill_info[1],round(kill_info[5],4),round(kill_info[6],4)) + '''
                                        Go save them!! </p>
                                        <form method="POST" id="mafia">
                                        <input type="hidden" name="victim" value="{}"/>'''.format(kill_info[1]) + '''
                                        <input type="hidden" name="kerberos" value="{}"/>'''.format(kerberos) + '''
                                        <input type = "hidden" name = "gameID" value ="{}"/>'''.format(gameID) + '''
                                    <input type="hidden" name="place" id="placeField" value = ""/>
                                    ''' + location_script + '''
                                    </form> <button onclick="getLocation()">Save them!</button>  <br>  <br>  <br> '''
                                    
                elif role == 'priest':
                    num_per_list = int(np.ceil(len(alive_roles)*.1))
                    out += PRIEST_ACT.format(gameID)

                    for i in range(num_per_list):
                        out += '''<input type="text" name="saint{}" /> <br>'''.format(i)
                    out += '''<br> Who are the sinners? <br> '''
                    for i in range(num_per_list):
                        out += '''<input type="text" name="sinner{}" /><br>'''.format(i)
                    out += '''<input type="hidden" name="kerberos" value="{}"/> 
                            <input type="submit" value="submit"/>
                            </form> '''.format(kerberos)
                    
                    
                elif role == 'secret admirer':
                    abilities = updateGame.get_abilities(kerberos, gameID)
                    abilities = [x[1] for x in abilities]
#                    out += str(abilities)
                    if "sa_role" in abilities:
                        out += '''<form method="POST"> Who would you like to admire today?
                                    <input type="text" name="admired" />
                                    <input type="hidden" name="gameID" value="{}" />
                                    <input type="submit" value="submit"/></form>
                        '''.format(gameID)
                    if "sa_set_investigation" in abilities:
                        out += '''<form method="POST"> Someone killed your admiree. Who do you think did it? 
                        Enter a comma separated list and you will be told if the killer is in that set.
                        <input type="text" name="set" />
                        <input type="hidden" name="gameID" value="{}" /><input type="hidden" name="ability" value="{}" />
                        <input type="submit" value="investigate!"/></form>'''.format(gameID, "sa_set_investigation")
                    if "sa_kill_investigation" in abilities:
                        out += '''<form method="POST"> Someone killed your admiree. Who do you think did it? Enter a single name and you will be told if they did it.
                        <input type="text" name="suspect" />
                        <input type="hidden" name="gameID" value="{}" /><input type="hidden" name="ability" value="{}" />
                        <input type="submit" value="investigate!"/></form>'''.format(gameID, "sa_kill_investigation")
    #            let people vote to execute if they are alive

                out += VOTINGFORM.format(gameID)
            else:
                all_players = c.execute('''SELECT role,kerberos,status FROM rolesTe WHERE gameID=? ;''',(gameID,)).fetchall()
                alive_roles = []
                for tup in set(all_players):
                    if tup[0]!="":
                        if tup[2] != "dead" and tup[2]!="executed":
                            alive_roles.append(tup[0])
                if 'mafia' in alive_roles:
                    won = 'mafia'
                else:
                    won = 'citizens'
                out += """<p> This game is over.The {} won. </p>""".format(won)
#                out += flaskrequest.environ.get('HTTP_X_REAL_IP', flaskrequest.remote_addr) + '<br>'
#        attach the dead background color and gif if you are dead
        else:

            out += '''<body bgcolor = {}>
                    Currently viewing gameID: {} <br>
                    Hi, {}! Unfortunately, you {} in the game. Your role was {}. Come back and play the next game!

            '''.format(colors['dead'],gameID,kerberos,message_dict[status],role) + gifs[status]
            out += '</div> <div class="column">'
            if int(gameID) in finished_games:
                all_players = c.execute('''SELECT role,kerberos,status FROM rolesTe WHERE gameID=? ;''',(gameID,)).fetchall()
                alive_roles = []
                for tup in set(all_players):
                    if tup[0]!="":
                        if tup[2] != "dead" and tup[2]!="executed":
                            alive_roles.append(tup[0])
                if 'mafia' in alive_roles:
                    won = 'mafia'
                else:
                    won = 'citizens'
                out += """<p> This game is over.The {} won. </p>""".format(won)
#        start a list of the other players in the game
        out += '</div> <div class="column" >'
        out += '<br> The other players are: <br>'
#        alphabetize the list by name and then by status so all the dead and all the alive are groped together
        other_roles.sort(key = lambda a: a[1])
        other_roles.sort(key = lambda a: a[0])
#        add the other statuses to the list of other players
        out += """<ul class="others-alive"> """

        for rol in other_roles:
            out += """<li> {}, who is {} </li> """.format(rol[1],rol[0])
        out += """</ul> """
       
        if role == 'mafia':
            out += '<br><p>The other mafia members are: <ul class="others-alive">'
            for rol in other_roles:
                if rol[2] == 'mafia':
                    out += '<li> {}, who is {} </li>'.format(rol[1],rol[0])
            out += '</ul></p>'
        
        if role in gifs:
            out += gifs[role]
    
#        end the text
        out += """</div></div></font></body> </html> """
#        close and commit the changes
        conn.commit()
        conn.close()
#        return the text you generated
        return out
#    close the connection and let them know they need a kerb
    conn.commit()
    conn.close()
    return "You must include your kerberos in your request."


def handle_post(request):
    '''post requests sent by clicking buttons on this page come back to this page
    this function reformats them to send to updateGame and update the game appropriately
    lets people know their requests went through
    '''
#    start the html output
    out = HTMLHEAD

    conn = updateGame.get_db_connection()
    c = conn.cursor()  # make cursor into database (allows us to execute commands)
#    for now no login required
#    check if they submitted a kerb to check on
    if 'kerberos' in request['values']:
        kerberos = request['values']['kerberos']
#        make sure the tables you need exist so you don't get errors later
        c.execute('''CREATE TABLE IF NOT EXISTS rolesTe (kerberos text, gameID int, role text, status text);''') # run a CREATE TABLE command
        c.execute('''CREATE TABLE IF NOT EXISTS playersT (timing timestamp, kerberos text, gameID int, espID text);''')
#        got the current game ID using Elizabeth's method from newGame
        try:
            gameID = c.execute('''SELECT gameID FROM playersT ORDER BY timing DESC;''').fetchone()
            gameID = int(gameID[0])-1
        except:
            gameID = 0;
        if request['form'].get('gameID'):
            gameID = request['form']['gameID']
#        assumes they only have one entry with this kerberos
#        get the roles of all the people in the current game
        newgame = None
        if request['form'].get('startgame'):
#            return 'testing'
            start = 'True'
            conn.commit()
            conn.close()
            response = requests.post(urls['new'], data={'kerberos':kerberos,'start':start,'gameID':gameID})
            out = HTMLHEAD
            out += HEAD.format(urls['home']+'?kerberos='+kerberos,"black","black",urls['home']+'?kerberos='+kerberos,urls['vote']+'?kerberos='+kerberos+'&gameID=home',urls['gamedb']+'?kerberos='+kerberos,urls['newgame']+'?kerberos='+kerberos)
        #        append the users to the list of users in a random order
            out += response.text
#            
            out += '<p><a href="{}"> Click to see game: {} </a> </p>'.format(urls['status']+'?kerberos='+kerberos+'&gameID='+gameID,gameID)
            out += """ </body> </html>"""
            return out
        
        c = conn.cursor()
        roles = c.execute('''SELECT status,role,kerberos FROM rolesTe WHERE gameID=?;''',(gameID,)).fetchall()
        
#        keep track of the people you're not looking for
        other_roles = []
        role = None
#        check if this kerb is in the current game; also keep track of the other players
        for rol in roles:
            if rol[2] == kerberos:
                status = rol[0]
                role = rol[1]
            else:
                other_roles.append((rol[0],rol[2],rol[1]))
                
#        if the person isn't playing, let them know
        if not role and not newgame:

            conn.commit()
            conn.close()
            return 'Sorry, {} is not in game {}.'.format(kerberos,gameID)
#        secret admirer comes out weird (as just secret), prob because it's two words
        if role == 'secret' or role == 'sa':
            role = 'secret admirer'
#        font color will be white only if the background is black, which is for mafia only
        if status == 'dead' or status == 'executed' or role != 'mafia':
            fontcolor = 'black'
        else:
            fontcolor = "white"

#        add on the heading which should be large and say welcome to the game

        out += HEAD.format(urls['home']+'?kerberos='+kerberos,fontcolor,fontcolor,urls['home']+'?kerberos='+kerberos,urls['vote']+'?kerberos='+kerberos+'&gameID='+str(gameID),urls['gamedb']+'?kerberos='+kerberos,urls['newgame']+'?kerberos='+kerberos)
        
#        check if the person is alive, because then the result will depend on the role
        
        if status == 'alive' and not newgame:
            color = colors.get(role)
            if not color:
                color = 'white'
            out += INTRO.format(color,gameID,kerberos,role)
#            if role in gifs:
#                message  = updateGame.execute_command("show_log {}".format(kerberos),gameID=gameID)
#                
#                if message:
#                    message_list = message.split('\n')
#                    out += '<ul>'
#                    for message in message_list:
#                        out += '<li>' + message + '</li>'
#                    out += '</ul>'
#                out += str(message)
            out += '<br><br>'
#            if they're voting, send a voting request
            if 'vote' in request['form']:
                vote = request['form']['vote']
#                out += requests.post(VOTE_URL, data = {'vote':vote,'kerberos':kerberos, 'gameID':str(gameID)}).text
                out += updateGame.execute_command("{} vote {}".format(kerberos, vote),gameID=gameID)
                out += "<br>"
#
            elif role == 'mafia':
                out += str(request)
                lat,lon = request['form']['place'].split("|")
                out += updateGame.execute_command("{} mafia_kill \"['{}', {}, {}]\"".format(kerberos,request['form']['victim'],lat,lon),gameID=gameID)
                out += '<br>'
            elif role == 'detective':
                suspect1 = request['form']['suspect1']
                suspect2 = request['form']['suspect2']
                victim = request['form']['victim']
                out += updateGame.execute_command("{} pair_investigation \"['{}','{}','{}']\"".format(kerberos,suspect1,suspect2,victim), gameID=gameID)
                out += '<br>'
            elif role == 'doctor':
                place = request['form']['place']
                victim = request['form']['victim']
                lat,lon = place.split("|")
                out += updateGame.execute_command("{} doctor_role \"['{}',{},{}]\"".format(kerberos,victim,lat,lon),gameID=gameID)
                out += '<br> <br>'
            elif role == 'priest':
                sinners = []
                saints = []
                for entry in request['form']:
                    if 'saint' in entry:
                        saints.append(request['form'][entry])
                    if 'sinner' in entry:
                        sinners.append(request['form'][entry])
#                print('sending command',sinners,saints)
                response = updateGame.execute_command(kerberos+''' priest_role "{'sinners':'''+str(sinners)+''', 'saints':'''+str(saints)+'''}"''',gameID=gameID)
                if response:
                    out += response
                else:
                    out += 'Response recorded!'
                print('command sent')
#                out += '<p> Recorded! </p>'
                out += '<br><br>'
            elif role == 'secret admirer' and 'admired' in request['form']:
                admired = request['form']['admired']
                out += "<p> Admiration recorded! </p>"
                updateGame.execute_command(kerberos+' sa_role '+admired,gameID=gameID)
            elif 'ability' in request['form']:
                ability = request['form']['ability']
                if ability == "sa_set_investigation":
                    targets='"[{}]"'.format(",".join("'{}'".format(x) for x in request['form']['set'].split(",")))
                    s=updateGame.execute_command(kerberos+' '+ability+' '+targets,gameID=gameID)
                elif ability == "sa_kill_investigation":
                    s=updateGame.execute_command(kerberos+' '+ability+' '+request['form']['suspect'],gameID=gameID)
                if s:out += s+"<br>"
#        attach the dead background color and gif if you are dead
        else:
            out += '''<body bgcolor = {}>
                    Currently viewing gameID: {} <br>
                    Hi, {}! Unfortunately, you {} in the game. Your role was {}. Come back and play the next game!

            '''.format(colors['dead'],gameID,kerberos,message_dict[status],role) + gifs['status']
#        start a list of the other players in the game
        out += '<br> The other players are: <br>'
#        alphabetize the list by name and then by status so all the dead and all the alive are grouped together
        other_roles.sort(key = lambda a: a[1])
        other_roles.sort(key = lambda a: a[0])
#        add the other statuses to the list of other players

        out += """<ul class="others-alive"> """

        for rol in other_roles:
            out += """<li> {}, who is {} </li> """.format(rol[1],rol[0])
        out += """</ul> """
        
        if role == 'mafia':
            out += '<br><br> <p> The other mafia members are: <ul class="others-alive">'
            for rol in other_roles:
                if rol[2] == 'mafia':
                    out += '<li> {}, who is </li>'.format(rol[0])
            out += '</ul> </p>'
            
#        end the text
        if role in gifs:
    
            out += gifs[role]
        out += """</div></div></font></body> </html> """
#        close and commit the changes
        conn.commit()
        conn.close()
#        return the text you generated
        return out
#    close the connection and let them know they need a kerb
    conn.commit()
    conn.close()
    return "You must include your kerberos in your request."
