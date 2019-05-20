import sqlite3
import sys
sys.path.append("__HOME__/mafia")
import updateGame

"""
defining targets types:

argument = name = type

type = player | list type | pair type type

lists and pairs are comma separated, lists are []-ed
spaces not allowed



priest_role brunnerj id=6 sinners=[a,b] saints=[c,d]

def parse_targets(targets, types):
    return eval("parse_{}(targets, types[1:])".format(types[0]))
def parse_player(s,t):
    x=c.execute("select * from groups where group_name='everyone' and player=? and game_id=?",(s, game_id)).fetchone()
    if x:return s
    raise Exception("player {} is not in game.".format(s))
def parse_living_player(s,t):
    x=c.execute("select * from groups where group_name='alive' and player=? and game_id=?",(s, game_id)).fetchone()
    if x:return s
    raise Exception("player {} is not in game.".format(s))
def parse_list(s,t):
    s2 
    s2 = s[1:-1].split(",")
    l = [parse_targets(x, t) for x in s2]
    return l
def parse_tuple(s,t):
    i = 0
    for i in range(len(s)):
        
"""    

def request_handler(r):
    conn = updateGame.get_db_connection()
    c = conn.cursor()
    if r['method']=="GET":
        game_id = r['values']['id']
        x = c.execute("select command from log where game_id = ?",(game_id,)).fetchall()
        return '\n'.join(a[0] for a in x)
    elif r['method']=='POST':
        game_id = r['form']['id']
        result = ""
        for line in r['form']['commands'].split('\n'):
            print(">{}".format(line))
            s=updateGame.execute_command(line,gameID=game_id)
            if s:print(s)
        conn.close()
        return result
