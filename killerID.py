import sys
sys.path.append("__HOME__/mafia")
import updateGame

def request_handler(request):
    '''request should be a get request with 'kerberos':kerberos in its values, also 'gameID':gameID
    '''
    if request['method'] == 'GET':
        kerberos = request['values']['kerberos']
        gameID = int(request['values']['gameID'])
        conn = updateGame.get_db_connection()  # connect to that database (will create if it doesn't already exist)
        c = conn.cursor()  # make cursor into database (allows us to execute commands)
        killid = c.execute('''SELECT espID FROM playersT WHERE kerberos=? AND gameID=?''',(kerberos,gameID)).fetchone()
        killid = killid[0]
        return killid
    return "Sorry, you can only send a get request"


