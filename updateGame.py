import random
import sqlite3
import datetime
import shlex
import time
import smtplib, ssl
import random
import os
import traceback
import requests

import sys
sys.path.append("__HOME__/mafia")
base_folder = 'https://608dev.net/sandbox/sc/kms20/mafia/'

VOTE_URL = base_folder + "voting.py"


SAVE_TIME = 15
DEG_TO_FT = 5280*60 #online said it was one mile to each minute
MIN_DIST = 100 #arbitrarily chosen for min saving dist, can be changed later
TIME_PER_DAY = datetime.timedelta(minutes=1000)

VOTING_PERIOD = datetime.timedelta(minutes = 10)
mafia = ['mafia']
"""
how to give input

Most input is given via command strings

execute_command(string,gameID)

e.g.
brunnerj mafia_kill ellenwan

that would cause the system to have brunnerj use the mafia's kill ability on ellenwan

The database userlog contains a list of events that have happened to a user. It is useful to, for example, get pair investigation results.

in general, the format is
player_name ability_name targets

targets is in a reasonable format. Many cases are a single string represting a player. These can be passed directly, unquoted
Other cases are lists or dictionaries. These need to be passed in as a quoted string, which contains valid python syntax. In these cases, player names should also be quoted.

abilities so far:
put the quotation marks, brackets, commas exactly as specified. Where it says player, put the name of a player. In general, player names should be quoted. lat and lon are floats.
Where it says list player, it should be a comma separated list of quoted player names, e.g. ['brunnerj', 'ellenwan'].

pair_investigation "['player suspect', 'player suspect', 'player victim']"
frame "['player framed', 'player victim']"

priest_role "{'sinners':[list player sinners], 'saints':[list player saint]}"

sa_role "admiration_target"
sa_set_investigation "[list player suspects]"
sa_kill_investigation player
sa_kill "[lat, lon]"

mafia_kill "['player victim', lat, lon]"

to be added:
mtp "victim"

splitter_role "[[list player], [list player]]"

roleblock target
child player
vigilante_kill "['player victim', lat, lon]"
mafia_scheme_kill "['player victim', lat, lon]"
trap "['player target', role_guess]"

"""
'''

cost and code are python expressions, everything else is arbitrary text.

Players or groups own artifacts. These have abilities. Abilities are either activated or triggered. Abilities cause effects. Activated have a cost, triggered have a trigger. Costs are a python function that returns a boolean. Triggers are other effects.

To use an ability, a user sumbits "player artifact_id ability targets".
First we run the cost function. If it returns false, abort and don't commit the db changes. If it returns true, then run the effect.
For triggered abilities, whenever an effect is run, all triggered abilities are checked to see if they trigger on it. If any do, then they run afterward.
effects:
  an effect is passed three arguments: controller, targets, source.
    controller is either the controller of the acitviated ability that caused this effect,
    targets are an arbitrary string passed in by the user/ui
    source is the id of the artifact that triggered the effect
Common costs:
{t}: tap this. All artifacts untap each day by default
sac: sacrifice this.
{0}: no cost. Can always be activated.

artifacts and effects are immutable tables probably.
'''
API_TOKEN = '3b7be13f146d1c'

'''actual in game things
groups
mafia

artifacts
mafia_kill: upkeep:use bang on target player
pair_investigator_role: upkeep: create two pair_investigations. ETB: create a pair_investigation_frame
pair_investigation: sac, check location: perform a pair investigation
pair_investigation_frame: sac: add target player to the guilty set

priest_role: {0}: set your priest lists
    upkeep: create a priest_list artifact with your lists
priest_list: when a player dies, if they are on your list, resolve a priest action

secret_adimirer_role: {0}: set your admiration target. ETB: create a mtp artifact
    upkeep: create a admiration artifact with your target
admiration: when a player dies, if it was your target, create a set_investigation and a infallible_investigation
set_investigation: sac: set investigate
infallible_investigation: sac: perform the investigation, if correct, get a bang_target artifact
bang_target: sac: use bang on given target
mtp: sac: remove yourself from the guilty set of target kill

splitter_role: {0}: set your splitter sets
    upkeep: the mafia create a split artifact with your sets
split: {0}: choose a set
    upkeep: sacrifice this. Create a pair_investigation for everyone in the chosen set

roleblocker: {0}: chose a target to block
    upkeep:

child: {t}: use a trust incant on target player. they are informed.
'''

stap="tap(artifact_id)"
ssac="sac(artifact_id)"
szero="zero()"

#some deep magic involving the server sandboxing
s=os.path.dirname(os.path.abspath(__file__))
s2="__HOME__/mafia"
s3=s2 if s2[:4]=="/var" else (s if s[:4]=="/var" else "")
if s3=="":
    raise Exception("Failure to open database because of error with __HOME__")
conn = sqlite3.connect(s3+"/playersT.db")
c = conn.cursor()
#we use a single global db connection; this function returns it for other modules to use
def get_db_connection():
    return conn
#mostly deprecated. The main use case is posting a command, which causes execute_command to be called. Now execute_command is simply called directly in most places. 
def request_handler(request):
    '''handles request by checking if you're posting and sending to post handler if so
    '''
    if request['method'] == 'POST':
        out = post_handler(request)
        conn.close()
        return out
    if request['method']=='GET':
        return "get"+send_updates(request['values']['gameID'],c)
    return 'Something is wrong with your request'
#mostly deprecated.
def post_handler(request):
    if 'setup' in request['form']:
        execute_command("setup")
        return
    action = request['form']['action']
    gameID = eval(request['form']['gameID']) if 'gameID' in request['form'] else get_latest_game_id()
    if action=='investigate':
        f=request['form']
        command = "{} pair_investigation \"['{}','{}','{}']\"".format(f['user'],f['suspect1'],f['suspect2'],f['victim'])
        return execute_command(command, gameID=gameID)
        role = c.execute("select role from rolesTe where kerberos=? and gameID=?;",(f['user'],gameID)).fetchone()
    if action == 'kill':
        if not all([x in request['form'] for x in ['killer','victim','place']]):
            return "invalid request. You need a killer, victim, and place."
        lat,lon = request['form']['place'].split("|")
        command = "{} mafia_kill \"['{}', {}, {}]\"".format(request['form']['killer'],request['form']['victim'],lat,lon)
        return execute_command(command, gameID=gameID)
    elif action == 'save':
        f=request['form']
        lat,lon = f['place'].split("|")
        command = "{} doctor_role \"['{}',{},{}]\"".format(f['kerberos'],f['victim'],lat,lon)
        return execute_command(command, gameID=gameID)
    elif action == 'espkill':
        return ESP_kill(request)
    else:
        return execute_command(request['form']['command'], gameID=gameID)
    return None

def ESP_kill(request):
    '''
    ESP kills bypass most of the roles abilities, so they are evaluated in a separate function.
    '''
    killerID = str(request['form']['killerID'])[::-1]
    victim = request['form']['victim']
    gameID = int(request['form']['gameID'])
    killer = c.execute('''SELECT kerberos FROM playersT WHERE gameID=? AND espID=?;''',(gameID,killerID)).fetchone()
    try:
        killer = killer[0]
    except:
        return "That espID does not correspond to a player in this game."
#        make sure the tables you need exist (for roles and kills)
    c.execute('''CREATE TABLE IF NOT EXISTS rolesTe (kerberos text, gameID int, role text, status text);''') # run a CREATE TABLE command
    c.execute('''CREATE TABLE IF NOT EXISTS ESPkills (killer text, victim text, gameID int, time timestamp,date text);''') # run a CREATE TABLE command
#        get the current date
    current_date = str(datetime.datetime.today().date())

#        get the role of the killer to make sure they're mafia
    killer_role = c.execute('''SELECT role,status FROM rolesTe WHERE kerberos=? AND gameID=?;''',(killer,gameID)).fetchone()
    if killer_role[1] != 'alive':
        return 'Sorry, this person not alive and cannot make a kill.'
    killer_role = killer_role[0]
    
#        make sure the killer is a member of the mafia
    if killer_role == 'mafia':
#            update the role of the dead person to be dead
        c.execute('''INSERT into ESPkills VALUES (?,?,?,?,?);''',(killer, victim, gameID, datetime.datetime.now(), str(current_date)))
        c.execute('''UPDATE rolesTe SET status = "dead" WHERE kerberos = ? AND gameID = ?''',(victim,gameID))
        conn.commit()
        return "You have died."
    return "Sorry, {} is a {}, not a mafia member and cannot execute a kill.".format(killer,killer_role)

#now we start a series of many functions dedicated to the platform. These define artifacts and effects. The platform is inspired by the game Magic.
#basically, all abilities players have are represented as artifacts they own with various abilities.

def new_artifact_ability_short(artifact_name, cost, code, name=None):
    '''this makes a new artifact with a single ability with the same name and given cost and code for effect'''
    if name==None:
        name = artifact_name
    new_artifact_ability(artifact_name,name,cost,name)
    new_effect(name, code)
def new_artifact_ability(artifact_name, ability_name, cost, effect):
    c.execute("insert into artifacts values (?,?,?,?);",(artifact_name, ability_name, cost, effect))
def new_artifact_trigger(artifact_name, trigger, code, ability_name=None):
    if ability_name==None:
        ability_name = artifact_name+"_"+str(len(c.execute("select * from artifacts_triggers where artifact=?",(artifact_name,)).fetchall()))
    c.execute("insert into artifacts_triggers values (?,?,?,?);",(artifact_name, ability_name, trigger, ability_name))
    c.execute("insert into effects values (?,?);",(ability_name, code))
def new_effect(name, code):
    c.execute("insert into effects values (?,?);", (name, code))
def upkeep():
    day = c.execute("select day from meta where game_id = ?",(game_id,)).fetchone()[0]
    next_day_time = datetime.datetime.strptime(c.execute("select next_day from meta where game_id = ?",(game_id,)).fetchone()[0],'%Y-%m-%d %H:%M:%S.%f') + TIME_PER_DAY
    c.execute("update meta set day = ?, next_day = ? where game_id = ?",(day+1,next_day_time,game_id))
    c.execute("update inventory set tapped = 0 where game_id = ?;",(game_id,))
def new_etb_effect(artifact, code):
    new_artifact_trigger(artifact, "etb", code)
def new_upkeep_effect(artifact, code):
    code = "(lambda controller, source:"+code+")(c.execute('select owner from inventory where artifact_id=? and game_id = ?',(source,game_id)).fetchone()[0], source)"
    new_artifact_trigger(artifact, "upkeep", code)
def create_artifact(owner, name):
    id = get_new_id()
    #add to inventory
    c.execute("insert into inventory values (?,?,?,?,?,?);",(game_id,owner, name, id, "{}", 0))
    #register any triggers
    l = c.execute("select trigger, effect from artifacts_triggers where artifact=?",(name,)).fetchall()
    for x in l:
        c.execute("insert into triggers values (?,?,?,?)",(game_id, x[0]+("_"+str(id) if x[0]=="etb" else ""), id, x[1]))
    l = c.execute("select ability from artifacts where artifact=?",(name,)).fetchall()
    for x in l:
        c.execute("insert into player_abilities values (?,?,?,?)",(game_id, owner, id, x[0]))
    do_effect("etb_"+str(id),id,controller=owner, source=id, code="0")
    return id
def get_new_id():
    id = c.execute("select artifact_id from meta where game_id = ?",(game_id,)).fetchone()[0]
    c.execute("update meta set artifact_id = ? where game_id = ?",(id+1,game_id))
    return id
#artifacts can have data attached to them. These functions allow you to get and set that data, which is stored as a dict.
def get_data(artifact_id):
    return eval(c.execute("select artifact_data from inventory where artifact_id=? and game_id = ?",(artifact_id,game_id)).fetchone()[0])
def get_dataf(artifact_id, field):
    d=get_data(artifact_id)
    return d[field] if field in d else None
def set_data(artifact_id, d):
    c.execute("update inventory set artifact_data=? where artifact_id=? and game_id = ?",(str(d),artifact_id,game_id))
def set_dataf(artifact_id, field, value):
    d = get_data(artifact_id)
    d[field] = value
    set_data(artifact_id, d)
def get_owner(artifact_id):
    return c.execute("select owner from inventory where artifact_id=? and game_id = ?",(artifact_id,game_id)).fetchone()[0]
def getDay():
    return c.execute("select day from meta where game_id = ?",(game_id,)).fetchone()[0]

#this is the start of actual functions to change the game state
def bang(controller, targets, source, timing):
    do_effect("kill",targets, controller=controller, source=source, timing=timing)
    userlog(controller, "You killed {}.".format(eval(targets)[0]))
    userlog(eval(targets)[0], "you were killed by {}".format(controller))
    return "Kill Recorded!"

def kill(controller, targets, timing):
    l = eval(targets)
    #record the kill
    c.execute("insert into kills values (?,?,?,?,?,?,?);",(game_id,controller, l[0], timing, getDay(), l[1], l[2]))
    c.execute("insert into killsRecord values (?,?,?,?,?,?,?);",(controller, l[0], game_id, timing, getDay(), l[1], l[2]))
    c.execute("insert into guilt values (?,?,?)",(game_id,controller, l[0]))
    #set the player to dead
    player_dies(l[0])
def player_dies(user):
    c.execute('''UPDATE rolesTe SET status = "dead" WHERE kerberos=? and gameID = ?;''',(user,game_id))
    check_win_condition()

def frame(controller, targets):
    l = eval(targets)
    '''l[0] is the victim, l[1] is framed'''
    c.execute("insert into guilt values (?,?,?)",(game_id,controller, targets))

#set_up_tables and drop_tables are used mostly for testing to prevent our databases from being corrupted with inconsistent stale data. They are not needed in normal usage.
def set_up_tables():
    c.execute("create table if not exists finishedGames(gameID int);")
    c.execute('''CREATE TABLE IF NOT EXISTS votesTiming (timing timestamp, gameID int);''')
    c.execute('''CREATE TABLE IF NOT EXISTS finishedGames (gameID int);''')
    c.execute('''CREATE TABLE IF NOT EXISTS playersT (timing timestamp, kerberos text, gameID int, espID text);''')
    c.execute('''CREATE TABLE IF NOT EXISTS rolesTe (kerberos text, gameID int, role text, status text);''')
    c.execute("create table if not exists meta(game_id int,day int,artifact_id int,next_day timestamp);")
    c.execute("create table if not exists groups(game_id int,player text,group_name text);")
    c.execute("create table if not exists inventory(game_id int,owner text, artifact text, artifact_id int, artifact_data text, tapped int);")
    c.execute("create table if not exists player_abilities(game_id int,owner text, artifact_id int, ability text);")
    c.execute("create table if not exists artifacts(artifact text, ability text, cost text, effect text);")
    c.execute("create table if not exists artifacts_triggers(artifact text, ability text, trigger text, effect text);")
    c.execute("create table if not exists effects(effect text, code text);")
    c.execute("create table if not exists triggers(game_id int,trigger text, artifact_id int, effect text);")
    c.execute("create table if not exists log(game_id int, command text);")
    c.execute("create table if not exists userlog(game_id int, user text, message text, day int);")
    c.execute("create table if not exists guilt (game_id int, killer text, victim text);")
    c.execute("create table if not exists kills (game_id int, killer text, victim text, time timestamp, day int, lat double, lon double);")
    c.execute("create table if not exists players (game_id int, player text, status text);")
    c.execute("CREATE TABLE IF NOT EXISTS killsRecord (killer text, victim text, gameID int, time timestamp,date text,lat float, lon float);") # run a CREATE TABLE command

def drop_tables():
    c.execute("drop table if exists finishedGames;")
    c.execute("drop table if exists votesTiming;")
    c.execute("drop table if exists finishedGames;")
    c.execute("drop table if exists playersT;")
    c.execute("drop table if exists rolesTe;")
    c.execute("drop table if exists meta;")
    c.execute("drop table if exists groups;")
    c.execute("drop table if exists inventory;")
    c.execute("drop table if exists player_abilities;")
    c.execute("drop table if exists artifacts;")
    c.execute("drop table if exists artifacts_triggers;")
    c.execute("drop table if exists effects;")
    c.execute("drop table if exists triggers;")
    c.execute("drop table if exists log;")
    c.execute("drop table if exists userlog;")
    c.execute("drop table if exists guilt;")
    c.execute("drop table if exists kills;")
    c.execute("drop table if exists killsRecord;")

def use_ability(user, artifact_id, ability, targets, timing):
    '''
    this is the generic resolve an action function
    user is who is taking the action
    artifact_id is the artifact the ability is located on
    ability is a string indicating the ability being used (ex. mafia_kill or pair_investigate)
    targets is any additional information to be passed to the ability
'''
    #first look up in the inventory database the artifact
    a = c.execute("select owner, artifact, artifact_data from inventory where artifact_id=? and game_id = ?",(artifact_id,game_id)).fetchone()
    #check if user owns the given artifact_id. If not, fail
    if user != a[0] and c.execute("select * from groups where player=? and group_name=? and game_id = ?",(user,a[0],game_id)).fetchone()==None:
        #fail due to no ownership
        return False
    #look up in the artifact db the (artifact name, ability) to get the cost and effect
    b = c.execute("select cost, effect from artifacts where artifact=? and ability=?",(a[1], ability)).fetchone()
    if b == None:
        x = c.execute("select ability from artifacts where artifact=?",(a[1],)).fetchall()
        print("no ability with that name exists. Did you mean {}".format(x))
        return False
    #run the cost function
    cost_return = eval(b[0])
    if cost_return:
        #if false, abort
        return (False, cost_return)
    else:
        #if true, run the effect
        effect_return = do_effect(b[1], targets, controller=user, source=artifact_id, d=eval(a[2]), timing=timing)
        #log the ability use
        #userlog(user, "{} used ability {} with targets {}".format(user, ability, targets))
        return (True, effect_return)

def do_effect(name, targets, controller=None, source=None, code=None, d=None, timing=None):
    '''generic resolve an effect function
    name is effect name
    targets are the effects targets
    controller is a player name
    for triggered abilities, targets and controller are those of the trigger, not of this effect
    source is an artifact id
'''
    #look up the effect in the effects database
    if code==None:
        effect_code = c.execute("select code from effects where effect=?",(name,)).fetchone()[0];
    else:
        effect_code = code
    #run the python located there, passing in targets, controller, source
    #print(effect_code)
    r = eval(effect_code)
    #look up and resolve any triggers
    l=c.execute("select artifact_id, effect from triggers where trigger=? and game_id = ?",(name,game_id)).fetchall();
    for a in l:
        do_effect(a[1], targets, controller=controller, source=a[0], d=get_data(a[0]))
    return r
#log a string for a user to see.
def userlog(user, text):
    c.execute("insert into userlog values (?,?,?,?);",(game_id, user, text, getDay()))
def get_abilities(user, gameID = None):
    if gameID != None: gameID = game_id
    groups = [x[0] for x in c.execute("select group_name from groups where player = ? and game_id=?",(user,gameID)).fetchall()]+[user]
    return c.execute("select artifact_id, ability from player_abilities where owner in ("+",".join(["?"]*len(groups))+") and game_id=?",tuple(groups+[gameID])).fetchall()
def get_latest_game_id():
    x = c.execute("select game_id from meta").fetchall()
    return max(x[0] for x in x) if x else 0
def new_day_time():return datetime.datetime.strptime(c.execute("select next_day from meta where game_id = ?",(game_id,)).fetchone()[0],'%Y-%m-%d %H:%M:%S.%f')
def execute_command(command, gameID = None):
    try:
        return execute_command_prime(command, gameID=gameID)
    except Exception as e:
        for table in ['meta','groups','inventory','triggers','log','userlog','guilt','kills','players','player_abilities','rolesTe','playersT','effects','killsRecord']:
            print("table {}".format(table))
            for x in c.execute("select * from {}".format(table)).fetchall():
                print(x)
        raise e
def execute_command_prime(command, gameID = None):
    ''' a command is defined as
    player ability targets
    This is the main function of this file. It's usage is described more at the top'''
    if not command or command[0]=="#":
        return
    global game_id
    game_id = get_latest_game_id() if gameID == None and command!="setup" else gameID
    l = shlex.split(command)
    r = (True,"")
    try:
        timing = datetime.datetime.strptime(l[0],'%Y-%m-%d %H:%M:%S.%f')
#        print(timing)
        l = l[1:]
    except:
        timing = datetime.datetime.now()
        command = '"{}" {}'.format(timing, command)
    if l[0]=="setup":
        set_up_dbs()
        return
    if l[0]!="new_game":
        while timing > new_day_time():
            execute_command("\"{}\" day_end".format(new_day_time()),gameID=game_id)
    if l[0]=="new_game":
        new_game(timing)
    elif l[0]=="show":
        if len(l) > 1:
            print("inventory")
            print("\n".join(str(x) for x in c.execute("select * from inventory where owner = ? and game_id = ?",(l[1],game_id)).fetchall()))
            print("userlog")
            print("\n".join(str(x[0]) for x in c.execute("select message from userlog where user = ? and game_id = ?",(l[1],game_id)).fetchall()))
            return
        print("inventory")
        print(c.execute("select * from inventory").fetchall())
        print("userlog")
        print(c.execute("select * from userlog").fetchall())
        print("triggers")
        print(c.execute("select * from triggers").fetchall())
        return
    elif l[0]=="show_log":
        groups = [x[0] for x in c.execute("select group_name from groups where player=? and game_id = ?",(l[1],game_id)).fetchall()]+[l[1]]
        return "\n".join("{} day {}: {}".format(x[0],x[2],x[1]) for x in c.execute("select user, message, day from userlog where user in ("+",".join(["?"]*len(groups))+") and game_id = ?",tuple(groups+[game_id])).fetchall())
    elif l[0]=="show_abilities":
        return get_abilities(l[1], game_id)
    elif l[0]=="role":
        create_artifact(l[1],l[2]+"_role")
        c.execute("delete from rolesTe where kerberos = ? and gameID = ?",(l[1],game_id)).fetchone()
        c.execute("insert into rolesTe values (?,?,?,?);",(l[1], game_id, l[2],'alive'))
        import newGame
        newGame.add_player(timing, l[1], game_id, c)
        if not c.execute("select * from groups where player = ? and game_id = ? and group_name = 'everyone'",(l[1],game_id)).fetchone():
            new_player(l[1])
    elif l[0]=="alignment":
        c.execute("insert into groups values (?,?,?)",(game_id,l[1],l[2]))
    elif l[0]=="day_end":
        do_effect("upkeep", None)
    else:
        player = l[0]
        ability = l[1]
        if l[2][:3] == "id=":
            i = int(l[2][3:])
            targets = "" if len(l)<4 else l[3]
        else:
            groups = [x[0] for x in c.execute("select group_name from groups where player=? and game_id = ?",(player,game_id)).fetchall()]+[player]
            x=c.execute("select artifact_id from player_abilities where owner in ("+",".join(["?"]*len(groups))+") and ability = ? and game_id = ?",tuple(groups+[ability,game_id])).fetchone()
            if x==None:
                return str(groups)+"\nYou don't have any more uses of this ability right now."
            i=x[0]
            targets = "" if len(l)<3 else l[2]
        r = use_ability(player,i,ability, targets, timing)
        if r[1]:
            pass
            #userlog(l[0],r[1])
    if r[0]:
        c.execute("insert into log values (?,?)",(game_id, command))
        conn.commit()
    return r[1]

#some common ability costs
def tap(artifact_id):
    x=c.execute("select tapped from inventory where artifact_id=? and game_id=?",(artifact_id,game_id)).fetchone()
    if not x or x[0]:
        return "That ability has already been used today."
    c.execute("update inventory set tapped=1 where artifact_id=? and game_id = ?",(artifact_id,game_id))
    return ""

def sac(artifact_id):
    name = c.execute("select artifact from inventory where artifact_id=? and game_id = ?",(artifact_id,game_id)).fetchone()
    if not name:
        return "You don't have that ability anymore."
    c.execute("delete from triggers where artifact_id=? and game_id = ?",(artifact_id,game_id))
    c.execute("delete from inventory where artifact_id=? and game_id = ?",(artifact_id,game_id))
    c.execute("delete from player_abilities where artifact_id=? and game_id = ?",(artifact_id,game_id))
    return ""

def zero():
    return ""

def is_alive(player):
    x = c.execute("select status from rolesTe where kerberos = ? and gameID = ?",(player, game_id)).fetchone()
    return x and x[0]=='alive'

def day_end_vote():
    ''' Does the day end execution'''
    if getDay() == 1:
        return
    x = c.execute("select owner, artifact_data from inventory where artifact = 'vote' and game_id = ?",(game_id,)).fetchall()
    player_list = [x[0] for x in c.execute("select player from groups where group_name = 'everyone' and game_id = ?",(game_id,)).fetchall()]
    d = {}
    for p in player_list:
        d[p] = 0
    for v in x:
        d2 = eval(v[1])
        if not is_alive(v[0]): continue # don't count dead people's votes
        vote = d2['vote'] if 'vote' in d2 and is_alive(d2['vote']) else v[0] # if you didn't vote, or voted for a dead person, you self vote
        userlog("everyone", "{} voted for {}.".format(v[0], vote))
        d[vote] += 1
    winner = ""
    most = 0
    for p in d:
        if d[p] > most:
            winner = p
            most = d[p]
    userlog("everyone", "{} is executed with {} votes!".format(winner, most))
    player_dies(winner)
    c.execute("update rolesTe set status = 'executed' where gameID=? and kerberos=?",(game_id, winner))

def new_player(user):
    create_artifact(user, "vote")
    c.execute("insert into groups values (?,?,?)",(game_id, user, "everyone"))

#here is where most of the actual functions that roles use are defined
def pair_investigate(user, targets):
    '''
    This is to investigate if {target1, target2} killed target3
    user is the user of the ability
'''
    target_list = eval(targets)
    target1 = target_list[0]
    target2 = target_list[1]
    target3 = target_list[2]
    #get who did the kill
    killers = [x[0] for x in c.execute("SELECT killer FROM guilt WHERE victim = ? and game_id = ?",(target3,game_id)).fetchall()]
    #print(killers)
    #print(c.execute("select killer,victim from guilt where game_id = ?",(game_id,)).fetchall())
    #randomly choose the result
    l = list(filter(lambda x:x not in killers,[target1,target2]))
    if l:
        r = random.choice(l)
    else:
        r = random.choice([target1,target2])
    userlog(user,"investigation of ({},{}) for {} returns {}".format(target1,target2,target3,r))
    return "{} did not kill {}".format(r,target3)
#priest
def make_priest_lists(controller, source):
    id = create_artifact(controller, "priest_list")
    d = get_data(source)
    d2 = {}
    d2['sinners']=d['sinners']
    d2['saints']=d['saints']
    d2['source']=source
    set_data(id, d2)
def set_lists(targets, source, controller):
    d = get_data(source)
    d2 = eval(targets)
    d["sinners"]=d2["sinners"]
    d["saints"]=d2["saints"]
    set_data(source, d)
    userlog(controller, "your lists are now set to sinners={} and saints={}".format(d['sinners'],d['saints']))
def priest_hit(killer, victim, priest_list):
    '''source is the priest_list'''
    d = get_data(priest_list)
    user = get_owner(priest_list)
    if victim in d["sinners"] and killer in d["saints"]:
        sac(d["source"])
        c.execute("update rolesTe set role = 'citizen' where kerberos = ? and gameID = ?",(user, game_id))
        userlog(user, "a saint killed a sinner when {} died.".format(victim))
    elif victim in d["saints"] and killer in d["sinners"]:
        userlog(user, "a sinner killed a saint when {} died.".format(victim))
#investigator
def make_pair_invs(controller):
    create_artifact(controller, "pair_investigation")
    create_artifact(controller, "pair_investigation")
#secret admirer
def make_sa_list(controller, source):
    id=create_artifact(controller, 'sa_list')
    set_dataf(id,'admired',get_data(source)['admired'])
def sa_hit(victim, sa_list):
    user = get_owner(sa_list)
    d=get_data(sa_list)
    if victim==d['admired']:
        i=create_artifact(user,"sa_set_investigation")
        set_dataf(i, 'victim', victim)
        i=create_artifact(user,"sa_kill_investigation")
        set_dataf(i, 'victim', victim)
        i=create_artifact(user,"death_timer")
        set_dataf(i, 'timer', 2)
        userlog(user,"{} was killed! You die at the end of the next day, and have a set investigation and kill investigation to use on their death.".format(victim))
def set_investigation(suspects, victim, user):
    l = set(x[0] for x in c.execute("select killer from guilt where victim=?",(victim,)).fetchall())
    if l.intersection(set(eval(suspects))):
        userlog(user, "Someone in the set {} killed {}".format(suspects, victim))
        return "Someone in the set made the kill!"
    else:
        userlog(user, "No one in the set {} killed {}".format(suspects, victim))
        return "The killer isn't in that set."
def kill_investigation(suspect, victim, user):
    if suspect==c.execute("select killer from kills where victim=?",(victim,)).fetchone()[0]:
        userlog(user, "{} killed {}!".format(suspect, victim, suspect))
        id=create_artifact(user,"sa_kill")
        set_dataf(id, 'target', suspect)
        return "{} killed {}! You may use kill {}".format(suspect, victim, suspect)
    else:
        userlog(user, "{} did not kill {}".format(suspect, victim))
        return "{} did not kill {}".format(suspect, victim)
def death_timer_upkeep(controller, source):
    t = get_data(source)['timer']
    t -= 1
    set_dataf(source, 'timer', t)
    if t==0:
        player_dies(controller)
def mtp(suspect, victim):
    c.execute("delete from guilt where victim = ? and killer = ?",(victim, suspect))
    return "You are cleared for the kill of {}".format(victim)
#doctor
def can_save(targets, timing):
    l = eval(targets)
    victim = l[0]
    x = c.execute("select lat, lon, time from kills where victim = ?",(victim,)).fetchone()
    kill_lat, kill_lon = x[0], x[1]
    lat, lon = l[1], l[2]
    if x == None:
        return "{} wasn't killed, so you can't save them.".format(victim)
        #userlog(doctor, "{} isn't dead, so you can't save them.".format(l[0]))
    dist = ((kill_lat-lat)**2 + (kill_lon-lon)**2)**(1/2)*DEG_TO_FT #dist in ft
    kill_time = datetime.datetime.strptime(x[2],'%Y-%m-%d %H:%M:%S.%f')
#        convert to minutes
    minutes_since_kill = (timing - kill_time).total_seconds()/60
    if dist > MIN_DIST:
        return "You need to be at the kill site to save them. You are {} ft away.".format(dist)
    if minutes_since_kill > SAVE_TIME:
        return "You are too late to save them."
    return ""
def do_save(doctor, targets):
    victim = eval(targets)[0]
    c.execute('''UPDATE rolesTe SET status = "alive" WHERE kerberos=? AND gameID=?''',(victim,game_id))
    userlog(doctor, "You saved {}".format(victim))
    return "Success!"
def vote(source, target):
#    requests.post(urls['vote'], data = {'vote':vote,'kerberos':kerberos, 'gameID':str(gameID)})
    set_dataf(source, 'vote', target)
    return "You voted for {}".format(target)

def new_game(timing):
    for table in ['meta','groups','inventory','triggers','log','userlog','guilt','kills','players','player_abilities']:
        try:
            c.execute("DELETE from {} WHERE game_id = ?".format(table),(game_id,))
        except Exception as e:
            print(e)
            print(table + ' is a problem table.')
    c.execute("delete from rolesTe where gameID=?",(game_id,))
    c.execute("delete from killsRecord where gameID=?",(game_id,))
    c.execute("delete from playersT where gameID=?",(game_id,))
    c.execute("insert into meta values (?,0,0,?)",(game_id,timing+TIME_PER_DAY))
    create_artifact("mafia","mafia_kill")
    create_artifact("everyone","day_end")

def set_up_dbs():
    '''This function sets up the database tables, and then defines how all of the roles work.
    If in the future, new roles were to be implemented or changed, this is the function that would be changed.
    If the code base is stable, then this function should not need to be called on a regular basis, and instead
    only needs to be called once when the server is first set up'''
    print('setting up')
    drop_tables()
    set_up_tables()
    new_artifact_ability_short("mafia_kill", stap, "bang(controller, targets, source, timing)")
    new_etb_effect("mafia_kill", "tap(source)")
    new_effect("kill","kill(controller, targets, timing)")

    new_upkeep_effect("detective_role","make_pair_invs(controller)")
    new_etb_effect("detective_role","create_artifact(controller,'pair_investigation_frame')")
    new_artifact_ability_short("pair_investigation",ssac,"pair_investigate(controller, targets)")
    new_artifact_ability_short("pair_investigation_frame",ssac,"frame(controller, targets)")

    new_artifact_ability_short("priest_role", szero, "set_lists(targets, source, controller)")
    new_upkeep_effect("priest_role","make_priest_lists(controller, source)")
    new_etb_effect("priest_role","set_lists(\"{'sinners':[],'saints':[]}\", source, controller)")
    new_artifact_trigger("priest_list","kill","priest_hit(controller, eval(targets)[0], source)")
    new_upkeep_effect("priest_list", "sac(source)")

    new_artifact_ability_short("sa_role", szero, "set_dataf(source, 'admired', targets)")
    new_upkeep_effect("sa_role", "make_sa_list(controller, source)")
    new_etb_effect("sa_role", "create_artifact(controller, 'mtp')")
    new_etb_effect("sa_role", "set_dataf(source, 'admired', controller)")
    new_artifact_trigger("sa_list","kill","sa_hit(eval(targets)[0], source)")
    new_upkeep_effect("sa_list","sac(source)")
    new_artifact_ability_short("sa_set_investigation", ssac, "set_investigation(targets, d['victim'], controller)")
    new_artifact_ability_short("sa_kill_investigation", ssac, "kill_investigation(targets, d['victim'], controller)")
    new_artifact_ability_short("sa_kill", ssac, "bang(controller, str([d['target']]+eval(targets)), source, timing)")
    new_artifact_ability_short("mtp", ssac, "mtp(controller, targets)")
    new_upkeep_effect("death_timer", "death_timer_upkeep(controller,source)")

    new_artifact_ability_short("doctor_role", "can_save(targets, timing)", "do_save(controller,targets)")

    new_artifact_ability_short("vote", szero, "vote(source, targets)")
    new_upkeep_effect("day_end", "day_end_vote()")

    new_effect("etb","0")
    new_effect("upkeep","upkeep()")

'''
port = 465  # For SSL
smtp_server = "smtp.gmail.com"
sender_email = "mitmafia608@gmail.com"  # Enter your address
password = "608design"
receiver_email = 'kms20@mit.edu'
'''
# def send_email(receiver, id, sender_email=sender_email):
#     try:
#         receiver_email = receiver + "@mit.edu"
#         print(receiver_email)
#         message = MIMEMultipart("alternative")
#         message["Subject"] = "multipart test"
#         message["From"] = sender_email
#         message["To"] = receiver_email
#
#         text = """
#         Hi {name},
#         How are you?
#         Real Python has many great tutorials:
#         www.realpython.com"""
#         text = text.format(name=receiver)
#         html = """\
#         <html>
#           <body>
#             <p>Hi {name},<br>
#                Click this link for game updates:
#                <a href="http://608dev.net/sandbox/sc/kms20/mafia/getStatus.py?kerberos={name}&gameID={id}">mafia updates!</a>
#             </p>
#           </body>
#         </html>
#         """
#         html = html.format(name=receiver, id = id)
#         # Turn these into plain/html MIMEText objects
#         part1 = MIMEText(text, "plain")
#         part2 = MIMEText(html, "html")
#
#         # Add HTML/plain-text parts to MIMEMultipart message
#         # The email client will try to render the last part first
#         message.attach(part1)
#         message.attach(part2)
#         # Create secure connection with server and send email
#         context = ssl.create_default_context()
#         with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
#             server.login(sender_email, password)
#             server.sendmail(
#                 sender_email, receiver_email, message.as_string()
#             )
#     except:
#         print('email failed')
'''
def end_voting(potential=None, days_ago=0):
    #this is random - needs to change\
    best = c.execute('''SELECT kerberos FROM rolesTe WHERE gameID=? AND status=?;''',(gameID, 'alive')).fetchall()
    print(best)
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
    c.execute('''CREATE TABLE IF NOT EXISTS votesTiming (timing timestamp, gameID int);''')
    dates = c.execute('''SELECT timing FROM votesTiming WHERE gameID = ? ORDER BY timing DESC;''',(gameID,)).fetchall()
    start = datetime.datetime.strptime(dates[days_ago+1][0], '%Y-%m-%d %H:%M:%S.%f')
    end = datetime.datetime.strptime(dates[days_ago][0], '%Y-%m-%d %H:%M:%S.%f')
    dead = []
    for voter in users:
        vote = c.execute('''SELECT vote FROM votes WHERE gameID=? AND timing>? AND timing<? AND kerberos=? ORDER BY timing DESC;''',(gameID, start, end, voter)).fetchone()
        if vote is not None:
            vote = vote[0]
        if vote in dead_dict:
            dead_dict[vote] += 1
            if dead == [] or dead_dict[vote]>max_:
                dead = [vote]
                max_ = dead_dict[vote]
            elif dead_dict[vote]==max_:
                dead.append(vote)
    if len(dead)==1:
        return dead[0]
    elif len(dead)>1:
        prev_most = end_voting(gameID, cursor, dead, days_ago+1)
        if prev_most != None:
            return prev_most
        else:
            return dead[0]
'''
def check_win_condition():
    maf = None
    maf_players = []
    cit_players = []
    for player, role, status in c.execute('''SELECT kerberos, role, status FROM rolesTe WHERE gameID=?;''',(game_id,)).fetchall():
        if role in mafia:
            maf_players.append(player)
        else:
            cit_players.append(player)
        if status == "alive":
            print(player)
            print(maf)
            print(role in mafia)
            inmaf = role in mafia
            if maf is None:
                maf = role in mafia
            elif maf != inmaf:
                return

    if maf:
        maf_add = 1
        cit_add = 0
        out = "maf win"
    else:
        maf_add = 0
        cit_add = 1
        out = "cit win"

    for player in maf_players:
        add_stats(player, maf_add)
    for player in cit_players:
        add_stats(player, cit_add)
    c.execute('''CREATE TABLE IF NOT EXISTS finishedGames (gameID int);''')
    c.execute('''INSERT into finishedGames VALUES (?);''',(game_id,))

def add_stats(kerberos, add):
    c.execute('''CREATE TABLE IF NOT EXISTS statsT (kerberos text, wins int, games int);''') # run a CREATE TABLE command
    try:
        wins,games = c.execute('''SELECT wins,games FROM statsT WHERE kerberos=?;''',(kerberos,)).fetchone()
        c.execute('''UPDATE statsT SET wins=?, games=? WHERE kerberos=?;''',(wins+add,games+1,kerberos)) #with time
    except:
        wins=0
        games = 0
        c.execute('''INSERT into statsT VALUES (?,?,?);''',(kerberos, add,1)) #with time

    return "Win Percentage: " + str(wins+add)+"/"+str(games+1)

# def send_updates(game_id, c):
#     last_time = c.execute('''SELECT timing FROM votesTiming WHERE gameID = ? ORDER BY timing DESC;''',(game_id,)).fetchone()
# #    last_time = datetime.datetime.strptime(c.execute('''SELECT timing FROM votesTiming WHERE gameID = ? ORDER BY timing DESC;''',(game_id,)).fetchone()[0], '%Y-%m-%d %H:%M:%S.%f')
#     if last_time:
#         last_time = datetime.datetime.strptime(last_time[0],'%Y-%m-%d %H:%M:%S.%f')
#         maf = None
#         win = False
#         if datetime.datetime.now()-last_time>=TIME_PER_DAY:
#
#             c.execute('''INSERT into votesTiming VALUES (?,?);''',(datetime.datetime.now(), game_id))
#             death = end_voting(game_id, c)
#             for role in c.execute('''SELECT kerberos FROM rolesTe WHERE gameID=?;''',(game_id,)).fetchall():
#                 send_email(role[0], game_id)
#             if death != None:
#                 c.execute('''UPDATE rolesTe SET status = "dead" WHERE kerberos=? AND gameID=?;''',(death,game_id))
#                 win, maf, maf_players, cit_players = check_win_condition(game_id,c)
#             if win:
'''
def vote_end(request):
    to_return = "no dead"
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
            store = end_voting2(gameID, c)
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
#    conn.close()
    return to_return

def end_voting2(gameID, cursor, potential=None, days_ago=0):
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
#        print(gameID, start, end, voter)
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
        prev_most = end_voting2(gameID, cursor, dead, days_ago+1)
        if prev_most != None:
            return prev_most
        else:
            return dead[0]
'''
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

if __name__ == '__main__':
    pass
    #for testing only!!!!
    """
    while(True):
        command = input(">")
        r = execute_command(command)
        if r: print(r)
"""
