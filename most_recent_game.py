import sys
sys.path.append("__HOME__/mafia")
import updateGame


def request_handler(request):
    if request['method'] == 'GET':
        return get_handler(request)
    return 'Sorry, you must send a get request.'


def get_handler(request):
    kerberos = request['values']['kerberos']
    conn = updateGame.get_db_connection()
    c = conn.cursor() 
    old_games = c.execute('''SELECT gameID FROM finishedGames;''').fetchall()
    old_games = [str(x[0]) for x in old_games]
    games = c.execute('''SELECT gameID FROM rolesTe WHERE kerberos=? ORDER BY gameID DESC;''',(kerberos,)).fetchall()
    games = [str(x[0]) for x in games]
    games = list(dict.fromkeys(games))
    games.sort(reverse = True)
    
    for game in games:
        
        if game not in old_games:
            return game
    return 'You are not in a game.'
    
    
    
