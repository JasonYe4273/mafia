import sys
sys.path.append("__HOME__/mafia")
import updateGame

"""
this file handles requests to getStatus.py to learn more about a player's status
it lets you know if you're alive or dead, what your role is, and who else is playing and if they are alive or dead

"""
# selected gifs and background colors for each role
gifs = {
    'detective': """<br> <iframe src="https://giphy.com/embed/2tRoKSKZHYpWvPo9TQ" width="480" height="353" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><p><a href="https://giphy.com/gifs/boomerangtoons-scooby-doo-scooby-doo-2tRoKSKZHYpWvPo9TQ">via GIPHY</a></p> <br>""",
    'mafia': """<br> <iframe src="https://giphy.com/embed/3o7btOHBo4Be8Io9IQ" width="480" height="270" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><p><a href="https://giphy.com/gifs/movie-the-godfather-francis-ford-coppola-3o7btOHBo4Be8Io9IQ">via GIPHY</a></p> <br>""",
    'citizen': """<br> <iframe src="https://giphy.com/embed/xUNd9QJeoYNzecQ1KU" width="480" height="270" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><p><a href="https://giphy.com/gifs/abcnetwork-yikes-the-middle-xUNd9QJeoYNzecQ1KU">via GIPHY</a></p> <br>""",
    'doctor': """ <br> <iframe src="https://giphy.com/embed/9Ai5dIk8xvBm0" width="480" height="399" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><p><a href="https://giphy.com/gifs/mr-gif-9Ai5dIk8xvBm0">via GIPHY</a></p> <br> """,
    'dead': """<br> <iframe src="https://giphy.com/embed/zEbDFvxxPSPcI" width="480" height="271" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><p><a href="https://giphy.com/gifs/law-and-order-zEbDFvxxPSPcI">via GIPHY</a></p> <br>"""
    }
colors = {'detective': '#D4EFDF',
          'citizen': '#EBF5FB',
          'mafia': 'black',
          'doctor': '#edc98b',
          'dead': '#FDFEFE'
          }


def request_handler(request):
    '''initial request handler
    decides if the type is right and passes to handle_get if it is
    '''
    if request['method'] == 'GET':
        return handle_get(request)
    return "There was an error with your request. Status requests must be GET"


def handle_get(request):
    example_db = "__HOME__/playersT.db"  # just come up with name of database
    conn = updateGame.get_db_connection()
    c = conn.cursor()  # make cursor into database (allows us to execute commands)
    out = ""

    if 'kerberos' in request['values']:
        status = ''

        kerberos = request['values']['kerberos']
        c.execute(
            '''CREATE TABLE IF NOT EXISTS rolesTe (kerberos text, gameID int, role text, status text);''')  # run a CREATE TABLE command
        c.execute('''CREATE TABLE IF NOT EXISTS playersT (timing timestamp, kerberos text, gameID int);''')

        try:
            gameID = c.execute('''SELECT gameID FROM playersT ORDER BY timing DESC;''').fetchone()
            gameID = int(gameID[0]) - 1
        except:
            gameID = 0

        roles = c.execute('''SELECT status,role,kerberos FROM rolesTe WHERE gameID=?;''', (gameID,)).fetchall()

        other_roles = []
        role = None

        for rol in roles:
            if rol[2] == kerberos:
                status = rol[0]
                role = rol[1]
            else:
                other_roles.append((rol[0], rol[2]))

        if not role:
            conn.commit()
            conn.close()
            return 'Sorry, {} is not in the current game.'.format(kerberos)

        #        add on the heading which should be large and say welcome to the game
        out += """ Welcome to live action mafia! """

        #        check if the person is alive, because then the result will depend on the role
        if status == 'alive':
                out += 'Hi, {}! You are currently alive and your role is {}.'.format(kerberos,role)
        else:
            out += 'Hi, {}! Unfortunately, you have died in the game. ' \
                   'Your role was {}. Come back and play the next game!'.format(kerberos, role)

        if role == 'detective':
            a = c.execute("select (suspect1, suspect2, victim, result) from inv where user=?", (kerberos,)).fetchall()

        out += '\nThe other players are: '

        other_roles.sort(key=lambda a: a[1])
        other_roles.sort(key=lambda a: a[0])

        for rol in other_roles:
            out += """\n {}, who is {} """.format(rol[1], rol[0])

        conn.commit()
        conn.close()
        return out

    conn.commit()
    conn.close()
    return "You must include your kerberos in your request."





